"""Deleting your own account. Permanent. What goes and what is only anonymised is in
docs/adr/0031-account-deletion.md, and the table-by-table list in docs/DATA_MODEL.md.
"""

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.core import security, storage
from app.core.exceptions import AccountOwnsSharedWorkspacesError, InvalidCredentialsError, ReauthenticationFailedError
from app.models.user import User
from app.repositories import account_repository, workspace_member_repository
from app.schemas.account import DeleteAccountRequest, DeletionPreviewResponse, OwnedWorkspaceResponse
from app.services import auth_service

logger = logging.getLogger(__name__)


def preview(db: Session, user: User) -> DeletionPreviewResponse:
    owned = account_repository.owned_workspaces_with_member_counts(db, user.id)
    deleted = [OwnedWorkspaceResponse(id=w.id, name=w.name, member_count=count) for w, count in owned if count == 1]
    blocking = [OwnedWorkspaceResponse(id=w.id, name=w.name, member_count=count) for w, count in owned if count > 1]

    return DeletionPreviewResponse(
        workspaces_deleted=deleted,
        workspaces_blocking=blocking,
        meetings_kept=account_repository.count_meetings_kept(db, user.id, [w.id for w in deleted]),
        can_delete=not blocking,
    )


def reauthenticate(user: User, request: DeleteAccountRequest) -> None:
    """Asks for the password again, or a fresh Google sign-in. A wrong answer is 403, not 401, so the app does not
    mistake it for an expired session and log the person out."""
    if request.password:
        if user.password_hash is None or not security.verify_password(request.password, user.password_hash):
            raise ReauthenticationFailedError("That password is not right.")

        return

    try:
        claims = auth_service.verify_google_id_token(request.google_id_token)
    except InvalidCredentialsError as error:
        raise ReauthenticationFailedError("Google could not confirm it is you. Sign in with Google again.") from error

    if user.google_sub is None or claims.get("sub") != user.google_sub:
        raise ReauthenticationFailedError("That Google account is not the one linked to this account.")


def delete_account(db: Session, user: User, request: DeleteAccountRequest) -> None:
    reauthenticate(user, request)
    summary = preview(db, user)

    if summary.workspaces_blocking:
        names = ", ".join(f'"{w.name}"' for w in summary.workspaces_blocking)

        raise AccountOwnsSharedWorkspacesError(
            f"You own {names}, and other people are in it. Transfer ownership first: open the workspace, go to "
            "Members, and choose Make owner on someone else. Then you can delete your account."
        )

    user_id = user.id
    meeting_ids: list[UUID] = []
    workspace_ids = [w.id for w in summary.workspaces_deleted]

    for workspace_id in workspace_ids:
        meeting_ids += account_repository.meeting_ids_in_workspace(db, workspace_id)
        account_repository.delete_workspace_with_everything(db, workspace_id)

    account_repository.anonymise_in_meetings(db, user_id)
    account_repository.delete_invites_for(db, user_id)
    account_repository.delete_memberships(db, user_id)
    enrollment_keys = account_repository.delete_voice_data(db, user_id)
    account_repository.delete_sessions(db, user_id)
    account_repository.delete_user(db, user_id)
    db.commit()

    # Storage last: if the database step failed above, nothing was lost. A failure here only leaves orphaned
    # files, which cost space, not privacy-critical rows, and are logged.
    _delete_files(user_id, workspace_ids, meeting_ids, enrollment_keys)


def _delete_files(user_id: UUID, workspace_ids: list[UUID], meeting_ids: list[UUID], enrollment_keys: list[str]) -> None:
    try:
        storage.delete_objects(enrollment_keys)
        storage.delete_prefix(f"enrollment/{user_id}/")

        for meeting_id in meeting_ids:
            storage.delete_prefix(f"meetings/{meeting_id}/")

        for workspace_id in workspace_ids:
            storage.delete_prefix(f"workspace-clips/{workspace_id}/")
    except Exception:  # noqa: BLE001 - the account is already gone, so this must not turn into an error for the user
        logger.exception("Some files of a deleted account could not be removed from storage")
