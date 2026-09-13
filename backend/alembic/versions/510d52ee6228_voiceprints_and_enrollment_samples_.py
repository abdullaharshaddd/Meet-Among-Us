"""voiceprints and enrollment_samples tables

Revision ID: 510d52ee6228
Revises: afb0dbe03f9b
Create Date: 2026-09-06 23:31:36.573618

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '510d52ee6228'
down_revision: Union[str, Sequence[str], None] = 'afb0dbe03f9b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Supabase ships pgvector but doesn't enable it by default. IF NOT EXISTS
    # makes this safe to re-run, same as the citext extension in the users
    # migration.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table('voiceprints',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('centroid', Vector(192), nullable=False),
    sa.Column('sample_count', sa.Integer(), nullable=False),
    sa.Column('intra_speaker_variance', sa.Float(), nullable=False),
    sa.Column('match_threshold', sa.Float(), nullable=False),
    sa.Column('model_version', sa.String(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )

    op.create_table('enrollment_samples',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('audio_key', sa.String(), nullable=False),
    sa.Column('language', sa.Enum('en', 'ur', 'mixed', name='enrollment_language'), nullable=False),
    sa.Column('duration_sec', sa.Float(), nullable=False),
    sa.Column('snr_db', sa.Float(), nullable=False),
    sa.Column('speech_duration_sec', sa.Float(), nullable=False),
    sa.Column('embedding', Vector(192), nullable=True),
    sa.Column('accepted', sa.Boolean(), nullable=False),
    sa.Column('rejection_reason', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # Looked up on every submission (status, three-strikes count) and reset.
    op.create_index('ix_enrollment_samples_user_id', 'enrollment_samples', ['user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_enrollment_samples_user_id', table_name='enrollment_samples')
    op.drop_table('enrollment_samples')
    op.execute("DROP TYPE IF EXISTS enrollment_language")
    op.drop_table('voiceprints')
    # vector extension intentionally left enabled — dropping a shared extension
    # isn't this migration's call, same reasoning as citext in the users migration.
