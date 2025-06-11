"""Initial iosapp schema

Revision ID: 0001
Revises: 
Create Date: 2024-06-11 12:30:00.000000

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
    # Create iosapp schema
    op.execute("CREATE SCHEMA IF NOT EXISTS iosapp")
    
    # Create device_tokens table
    op.create_table('device_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('device_token', sa.String(255), nullable=False, unique=True),
        sa.Column('device_info', postgresql.JSONB(astext_type=sa.Text())),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('last_seen', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        schema='iosapp'
    )
    
    # Create keyword_subscriptions table
    op.create_table('keyword_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('keywords', postgresql.ARRAY(sa.Text), nullable=False),
        sa.Column('sources', postgresql.ARRAY(sa.Text)),
        sa.Column('location_filters', postgresql.JSONB(astext_type=sa.Text())),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['device_id'], ['iosapp.device_tokens.id'], ondelete='CASCADE'),
        schema='iosapp'
    )
    
    # Create job_matches table
    op.create_table('job_matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('matched_keywords', postgresql.ARRAY(sa.Text), nullable=False),
        sa.Column('relevance_score', sa.String()),
        sa.Column('is_read', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['device_id'], ['iosapp.device_tokens.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subscription_id'], ['iosapp.keyword_subscriptions.id'], ondelete='CASCADE'),
        schema='iosapp'
    )
    
    # Create push_notifications table
    op.create_table('push_notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('match_id', postgresql.UUID(as_uuid=True)),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('apns_response', postgresql.JSONB(astext_type=sa.Text())),
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('delivered_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['device_id'], ['iosapp.device_tokens.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['match_id'], ['iosapp.job_matches.id'], ondelete='CASCADE'),
        schema='iosapp'
    )
    
    # Create processed_jobs table
    op.create_table('processed_jobs',
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('device_id', 'job_id'),
        sa.ForeignKeyConstraint(['device_id'], ['iosapp.device_tokens.id'], ondelete='CASCADE'),
        schema='iosapp'
    )
    
    # Create indexes
    op.create_index('idx_device_tokens_active', 'device_tokens', ['is_active', 'created_at'], schema='iosapp')
    op.create_index('idx_device_tokens_token', 'device_tokens', ['device_token'], schema='iosapp')
    
    op.create_index('idx_keyword_subscriptions_device', 'keyword_subscriptions', ['device_id', 'is_active'], schema='iosapp')
    op.create_index('idx_keyword_subscriptions_keywords', 'keyword_subscriptions', ['keywords'], postgresql_using='gin', schema='iosapp')
    
    op.create_index('idx_job_matches_device_created', 'job_matches', ['device_id', sa.text('created_at DESC')], schema='iosapp')
    op.create_index('idx_job_matches_subscription', 'job_matches', ['subscription_id', sa.text('created_at DESC')], schema='iosapp')
    op.create_index('idx_job_matches_unread', 'job_matches', ['device_id', 'is_read', sa.text('created_at DESC')], schema='iosapp')
    
    op.create_index('idx_push_notifications_device', 'push_notifications', ['device_id', sa.text('created_at DESC')], schema='iosapp')
    op.create_index('idx_push_notifications_status', 'push_notifications', ['status', 'created_at'], schema='iosapp')
    
    op.create_index('idx_processed_jobs_lookup', 'processed_jobs', ['device_id', 'job_id'], schema='iosapp')
    
    # Create updated_at trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Add updated_at triggers
    op.execute("""
        CREATE TRIGGER update_device_tokens_updated_at 
            BEFORE UPDATE ON iosapp.device_tokens 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_keyword_subscriptions_updated_at 
            BEFORE UPDATE ON iosapp.keyword_subscriptions 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_keyword_subscriptions_updated_at ON iosapp.keyword_subscriptions")
    op.execute("DROP TRIGGER IF EXISTS update_device_tokens_updated_at ON iosapp.device_tokens")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop tables (foreign key constraints will be dropped automatically)
    op.drop_table('processed_jobs', schema='iosapp')
    op.drop_table('push_notifications', schema='iosapp')
    op.drop_table('job_matches', schema='iosapp')
    op.drop_table('keyword_subscriptions', schema='iosapp')
    op.drop_table('device_tokens', schema='iosapp')
    
    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS iosapp CASCADE")