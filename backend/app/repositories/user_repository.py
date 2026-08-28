from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import EnrollmentStatus, User


def get_by_google_sub(db: Session, google_sub: str) -> User | None:
    return db.execute(select(User).where(User.google_sub == google_sub)).scalar_one_or_none()


def get_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def create_google_user(
    db: Session, *, google_sub: str, email: str, display_name: str, avatar_url: str | None
) -> User:
    user = User(
        google_sub=google_sub,
        email=email,
        display_name=display_name,
        avatar_url=avatar_url,
        password_hash=None,
        enrollment_status=EnrollmentStatus.NOT_STARTED,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def link_google_sub(db: Session, user: User, google_sub: str) -> User:
    """A user who previously signed up with email/password now signs in with Google
    using the same email — attach the Google identity instead of violating the
    email-unique constraint with a second row."""
    user.google_sub = google_sub
    db.commit()
    db.refresh(user)
    return user
