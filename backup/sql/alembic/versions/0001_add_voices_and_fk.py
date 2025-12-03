"""add voices table and make jobs.voice_id a FK

Revision ID: 0001_add_voices_and_fk
Revises: 
Create Date: 2025-11-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, Boolean, Text

# revision identifiers, used by Alembic.
revision = '0001_add_voices_and_fk'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1) Create voices table
    op.create_table(
        'voices',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('language', sa.String, nullable=True),
        sa.Column('provider', sa.String, nullable=True),
        sa.Column('requires_gpu', sa.Boolean, nullable=False, server_default=sa.sql.expression.false()),
        sa.Column('model_path', sa.String, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
    )

    # 2) Populate voices from existing jobs.voice_id strings (if any)
    # Insert distinct voice strings as voice records with provider='piper'
    try:
        conn.execute("""
            INSERT INTO voices(name, language, provider, requires_gpu, model_path, description)
            SELECT DISTINCT voice_id, NULL, 'piper', 0, NULL, NULL FROM jobs WHERE voice_id IS NOT NULL AND voice_id != ''
        """)
    except Exception:
        # If jobs table doesn't exist or no voice strings, ignore
        pass

    # 3) SQLite cannot ALTER COLUMN types easily; create new jobs_temp with voice_id INTEGER FK
    op.create_table(
        'jobs_temp',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=True),
        sa.Column('language', sa.String, nullable=True),
        sa.Column('voice_id', sa.Integer, nullable=True),
        sa.Column('text', sa.Text, nullable=True),
        sa.Column('include_alignments', sa.Boolean, nullable=True),
        sa.Column('original_filename', sa.String, nullable=True),
        sa.Column('total_chunks', sa.Integer, nullable=True),
        sa.Column('completed_chunks', sa.Integer, nullable=True),
        sa.Column('status', sa.String, nullable=True),
        sa.Column('s3_final_url', sa.String, nullable=True),
        sa.Column('alignments_s3_url', sa.String, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=True),
    )

    # 4) Copy data into jobs_temp, mapping voice name -> voices.id
    try:
        conn.execute("""
        INSERT INTO jobs_temp (id, user_id, language, voice_id, text, include_alignments, original_filename, total_chunks, completed_chunks, status, s3_final_url, alignments_s3_url, created_at, updated_at)
        SELECT j.id, j.user_id, j.language,
          (SELECT id FROM voices v WHERE v.name = j.voice_id LIMIT 1) as voice_id,
          j.text, j.include_alignments, j.original_filename, j.total_chunks, j.completed_chunks, j.status, j.s3_final_url, j.alignments_s3_url, j.created_at, j.updated_at
        FROM jobs j
        """)
    except Exception:
        # If jobs table doesn't exist (fresh DB), skip
        pass

    # 5) Drop old jobs table and rename jobs_temp -> jobs
    try:
        op.drop_table('jobs')
    except Exception:
        pass
    op.rename_table('jobs_temp', 'jobs')


def downgrade():
    # For simplicity, downgrade will drop voices table and leave jobs as-is.
    try:
        op.drop_table('voices')
    except Exception:
        pass
