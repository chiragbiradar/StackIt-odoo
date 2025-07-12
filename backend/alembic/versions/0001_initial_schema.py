"""Initial schema

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums
    userrole = postgresql.ENUM('guest', 'user', 'admin', name='userrole')
    userrole.create(op.get_bind())
    
    notificationtype = postgresql.ENUM(
        'answer_to_question', 'comment_on_answer', 'mention', 
        'answer_accepted', 'vote_received', name='notificationtype'
    )
    notificationtype.create(op.get_bind())
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('role', userrole, nullable=False, server_default='user'),
        sa.Column('reputation_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('questions_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('answers_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # Create tags table
    op.create_table('tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tags_id'), 'tags', ['id'], unique=False)
    op.create_index(op.f('ix_tags_name'), 'tags', ['name'], unique=True)
    
    # Create questions table
    op.create_table('questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('vote_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('answer_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_closed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('has_accepted_answer', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('accepted_answer_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_questions_author_id'), 'questions', ['author_id'], unique=False)
    op.create_index(op.f('ix_questions_id'), 'questions', ['id'], unique=False)
    op.create_index(op.f('ix_questions_title'), 'questions', ['title'], unique=False)
    
    # Create answers table
    op.create_table('answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('vote_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('comment_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_accepted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_answers_author_id'), 'answers', ['author_id'], unique=False)
    op.create_index(op.f('ix_answers_id'), 'answers', ['id'], unique=False)
    op.create_index(op.f('ix_answers_question_id'), 'answers', ['question_id'], unique=False)
    
    # Add foreign key constraint for accepted_answer_id
    op.create_foreign_key('fk_questions_accepted_answer', 'questions', 'answers', ['accepted_answer_id'], ['id'], ondelete='SET NULL')
    
    # Create question_tags table
    op.create_table('question_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('question_id', 'tag_id', name='uq_question_tag')
    )
    op.create_index(op.f('ix_question_tags_id'), 'question_tags', ['id'], unique=False)
    
    # Create votes table
    op.create_table('votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('is_upvote', sa.Boolean(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('answer_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['answer_id'], ['answers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'answer_id', name='uq_user_answer_vote')
    )
    op.create_index(op.f('ix_votes_answer_id'), 'votes', ['answer_id'], unique=False)
    op.create_index(op.f('ix_votes_id'), 'votes', ['id'], unique=False)
    op.create_index(op.f('ix_votes_user_id'), 'votes', ['user_id'], unique=False)
    
    # Create comments table
    op.create_table('comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('answer_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['answer_id'], ['answers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comments_answer_id'), 'comments', ['answer_id'], unique=False)
    op.create_index(op.f('ix_comments_author_id'), 'comments', ['author_id'], unique=False)
    op.create_index(op.f('ix_comments_id'), 'comments', ['id'], unique=False)
    
    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('notification_type', notificationtype, nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('triggered_by_user_id', sa.Integer(), nullable=True),
        sa.Column('related_question_id', sa.Integer(), nullable=True),
        sa.Column('related_answer_id', sa.Integer(), nullable=True),
        sa.Column('related_comment_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['related_answer_id'], ['answers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['related_comment_id'], ['comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['related_question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['triggered_by_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('notifications')
    op.drop_table('comments')
    op.drop_table('votes')
    op.drop_table('question_tags')
    op.drop_table('answers')
    op.drop_table('questions')
    op.drop_table('tags')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS notificationtype')
    op.execute('DROP TYPE IF EXISTS userrole')
