"""Add email authentication tables

Revision ID: email_auth_001
Create Date: 2026-01-25

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'email_auth_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Update users table
    # Drop old cognito_sub column if it exists and add new columns
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Try to drop cognito_sub if it exists (ignore if doesn't exist)
        try:
            batch_op.drop_column('cognito_sub')
        except:
            pass
        
        # Add new columns if they don't exist
        try:
            batch_op.add_column(sa.Column('hashed_password', sa.String(), nullable=True))
        except:
            pass
            
        try:
            batch_op.add_column(sa.Column('full_name', sa.String(), nullable=True))
        except:
            pass
            
        try:
            batch_op.add_column(sa.Column('is_verified', sa.Boolean(), nullable=True, server_default='0'))
        except:
            pass
            
        try:
            batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True, default=datetime.utcnow))
        except:
            pass

    # Create verification_codes table
    try:
        op.create_table(
            'verification_codes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(), nullable=False),
            sa.Column('code', sa.String(), nullable=False),
            sa.Column('code_type', sa.String(), nullable=False),
            sa.Column('is_used', sa.Boolean(), nullable=True, server_default='0'),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_verification_codes_email'), 'verification_codes', ['email'], unique=False)
    except:
        # Table might already exist
        pass


def downgrade():
    # Drop verification_codes table
    op.drop_index(op.f('ix_verification_codes_email'), table_name='verification_codes')
    op.drop_table('verification_codes')
    
    # Revert users table changes
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('is_verified')
        batch_op.drop_column('full_name')
        batch_op.drop_column('hashed_password')
        batch_op.add_column(sa.Column('cognito_sub', sa.String(), nullable=True))
