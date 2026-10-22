"""workspaces, workspace_members and invites

Revision ID: 1cdbf3e2aee4
Revises: 510d52ee6228
Create Date: 2026-10-22 13:52:07.851745

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1cdbf3e2aee4'
down_revision: Union[str, Sequence[str], None] = '510d52ee6228'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('workspaces',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('owner_user_id', sa.UUID(), nullable=False),
    sa.Column('join_code', sa.String(length=8), nullable=False),
    sa.Column('code_joining_enabled', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('join_code')
    )
    op.create_table('invites',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('scope', sa.Enum('workspace', 'project', name='invite_scope'), nullable=False),
    sa.Column('workspace_id', sa.UUID(), nullable=False),
    sa.Column('project_id', sa.UUID(), nullable=True),
    sa.Column('email', postgresql.CITEXT(), nullable=False),
    sa.Column('token', sa.String(), nullable=False),
    sa.Column('invited_by_user_id', sa.UUID(), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('accepted_by_user_id', sa.UUID(), nullable=True),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('email_status', sa.Enum('sending', 'sent', 'failed', name='email_status'), nullable=False),
    sa.Column('email_error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['accepted_by_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['invited_by_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token')
    )
    op.create_table('workspace_members',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('workspace_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('role', sa.Enum('owner', 'admin', 'member', name='workspace_role'), nullable=False),
    sa.Column('can_create_projects', sa.Boolean(), nullable=False),
    sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('workspace_id', 'user_id')
    )
    # Looked up on every invite creation (duplicate check) and every pending-invite list.
    op.create_index('ix_invites_workspace_id_email', 'invites', ['workspace_id', 'email'])
    op.create_index('ix_workspace_members_user_id', 'workspace_members', ['user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('workspace_members')
    op.drop_table('invites')
    op.drop_table('workspaces')
    op.execute("DROP TYPE workspace_role")
    op.execute("DROP TYPE invite_scope")
    op.execute("DROP TYPE email_status")
