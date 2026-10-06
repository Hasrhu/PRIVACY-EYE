"""Add scan_reports, scan_report_signals, and scan_report_tests tables

Revision ID: 002_scan_reports
Revises: 
Create Date: 2026-10-06 23:25:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_scan_reports'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create scan_reports
    op.create_table(
        'scan_reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('report_number', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('live_session_id', sa.String(length=100), nullable=False),
        sa.Column('assessment', sa.String(length=100), nullable=False),
        sa.Column('category_label', sa.String(length=200), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('reliability', sa.String(length=50), nullable=False),
        sa.Column('input_quality', sa.String(length=50), nullable=False),
        sa.Column('processing_location', sa.String(length=100), nullable=False),
        sa.Column('has_face_capture', sa.Boolean(), nullable=False),
        sa.Column('face_capture_storage_key', sa.String(length=500), nullable=True),
        sa.Column('jpg_report_storage_key', sa.String(length=500), nullable=True),
        sa.Column('pdf_report_storage_key', sa.String(length=500), nullable=True),
        sa.Column('report_status', sa.String(length=50), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('preprocessing_version', sa.String(length=50), nullable=False),
        sa.Column('fusion_version', sa.String(length=50), nullable=False),
        sa.Column('calibration_version', sa.String(length=50), nullable=False),
        sa.Column('target_face_id', sa.String(length=50), nullable=True),
        sa.Column('faces_detected_count', sa.Integer(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('why_reasons', sa.JSON(), nullable=True),
        sa.Column('raw_snapshot', sa.JSON(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scan_reports_report_number', 'scan_reports', ['report_number'], unique=True)
    op.create_index('ix_scan_reports_user_id', 'scan_reports', ['user_id'], unique=False)
    op.create_index('ix_scan_reports_live_session_id', 'scan_reports', ['live_session_id'], unique=False)
    op.create_index('ix_scan_reports_user_created', 'scan_reports', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_scan_reports_session_user', 'scan_reports', ['live_session_id', 'user_id'], unique=False)

    # Create scan_report_signals
    op.create_table(
        'scan_report_signals',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('report_id', sa.String(length=36), nullable=False),
        sa.Column('signal_name', sa.String(length=100), nullable=False),
        sa.Column('signal_value', sa.String(length=200), nullable=False),
        sa.Column('signal_status', sa.String(length=50), nullable=False),
        sa.Column('signal_explanation', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['scan_reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scan_report_signals_report_id', 'scan_report_signals', ['report_id'], unique=False)

    # Create scan_report_tests
    op.create_table(
        'scan_report_tests',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('report_id', sa.String(length=36), nullable=False),
        sa.Column('test_name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['scan_reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scan_report_tests_report_id', 'scan_report_tests', ['report_id'], unique=False)


def downgrade() -> None:
    op.drop_table('scan_report_tests')
    op.drop_table('scan_report_signals')
    op.drop_table('scan_reports')
