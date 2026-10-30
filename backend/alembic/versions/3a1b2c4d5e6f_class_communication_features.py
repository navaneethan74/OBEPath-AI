"""class_communication_features

Revision ID: 3a1b2c4d5e6f
Revises: 2eff8e0f240d
Create Date: 2026-10-29 18:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a1b2c4d5e6f'
down_revision: Union[str, Sequence[str], None] = '2eff8e0f240d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. class_resources
    op.create_table(
        'class_resources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_class_resources_id'), 'class_resources', ['id'], unique=False)
    op.create_index(op.f('ix_class_resources_class_id'), 'class_resources', ['class_id'], unique=False)

    # 2. class_announcements
    op.create_table(
        'class_announcements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('pinned', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_class_announcements_id'), 'class_announcements', ['id'], unique=False)
    op.create_index(op.f('ix_class_announcements_class_id'), 'class_announcements', ['class_id'], unique=False)

    # 3. announcement_reads
    op.create_table(
        'announcement_reads',
        sa.Column('announcement_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['announcement_id'], ['class_announcements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('announcement_id', 'student_id')
    )

    # 4. class_doubts
    op.create_table(
        'class_doubts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('visibility', sa.String(length=20), nullable=False, server_default=sa.text("'private'")),
        sa.Column('status', sa.String(length=20), nullable=False, server_default=sa.text("'open'")),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id']),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_class_doubts_id'), 'class_doubts', ['id'], unique=False)
    op.create_index(op.f('ix_class_doubts_class_id'), 'class_doubts', ['class_id'], unique=False)

    # 5. class_doubt_replies
    op.create_table(
        'class_doubt_replies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doubt_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.ForeignKeyConstraint(['author_id'], ['users.id']),
        sa.ForeignKeyConstraint(['doubt_id'], ['class_doubts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_class_doubt_replies_id'), 'class_doubt_replies', ['id'], unique=False)
    op.create_index(op.f('ix_class_doubt_replies_doubt_id'), 'class_doubt_replies', ['doubt_id'], unique=False)


def downgrade() -> None:
    op.drop_table('class_doubt_replies')
    op.drop_table('class_doubts')
    op.drop_table('announcement_reads')
    op.drop_table('class_announcements')
    op.drop_table('class_resources')
