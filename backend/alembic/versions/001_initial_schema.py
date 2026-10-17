"""Initial database schema migration for CareerShield AI.

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-10-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. job_analyses table
    op.create_table(
        "job_analyses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_title", sa.String(length=255), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("recruiter_name", sa.String(length=255), nullable=True),
        sa.Column("recruiter_email", sa.String(length=255), nullable=True),
        sa.Column("recruiter_phone", sa.String(length=50), nullable=True),
        sa.Column("contact_channel", sa.String(length=50), nullable=False, server_default="EMAIL"),
        sa.Column("job_description", sa.Text(), nullable=False),
        sa.Column("salary_offered", sa.String(length=100), nullable=True),
        sa.Column("salary_frequency", sa.String(length=20), nullable=True, server_default="ANNUAL"),
        sa.Column("location", sa.String(length=150), nullable=True),
        sa.Column("application_url", sa.String(length=500), nullable=True),
        sa.Column("requires_payment", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("payment_amount_claimed", sa.Float(), nullable=True),
        sa.Column("payment_reason", sa.String(length=255), nullable=True),
        sa.Column("ml_risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("heuristic_risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("final_risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("risk_level", sa.String(length=30), nullable=False, server_default="LOW_RISK"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("warning_signs", sa.JSON(), nullable=False),
        sa.Column("evidence_snippets", sa.JSON(), nullable=False),
        sa.Column("recommendations", sa.JSON(), nullable=False),
        sa.Column("company_assessment", sa.JSON(), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False, server_default="v1.0-rules-only"),
        sa.Column("client_ip_hash", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_analyses_id", "job_analyses", ["id"], unique=False)
    op.create_index("ix_job_analyses_company_name", "job_analyses", ["company_name"], unique=False)
    op.create_index("ix_job_analyses_created_at", "job_analyses", ["created_at"], unique=False)

    # 2. analysis_feedbacks table
    op.create_table(
        "analysis_feedbacks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("user_verdict", sa.String(length=50), nullable=False),
        sa.Column("actual_outcome", sa.String(length=50), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["job_analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_feedbacks_id", "analysis_feedbacks", ["id"], unique=False)
    op.create_index("ix_analysis_feedbacks_analysis_id", "analysis_feedbacks", ["analysis_id"], unique=False)

    # 3. known_company_benchmarks table
    op.create_table(
        "known_company_benchmarks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("official_career_url", sa.String(length=255), nullable=False),
        sa.Column("legitimate_domains", sa.JSON(), nullable=False),
        sa.Column("never_charges_fees_policy", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("official_hr_email_pattern", sa.String(length=255), nullable=True),
        sa.Column("frequently_spoofed", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("advisory_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_known_company_benchmarks_canonical_name", "known_company_benchmarks", ["canonical_name"], unique=True)

    # 4. model_eval_metrics table
    op.create_table(
        "model_eval_metrics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("algorithm_name", sa.String(length=100), nullable=False),
        sa.Column("dataset_records_count", sa.Integer(), nullable=False),
        sa.Column("test_accuracy", sa.Float(), nullable=False),
        sa.Column("precision_macro", sa.Float(), nullable=False),
        sa.Column("recall_macro", sa.Float(), nullable=False),
        sa.Column("f1_macro", sa.Float(), nullable=False),
        sa.Column("roc_auc", sa.Float(), nullable=False),
        sa.Column("confusion_matrix", sa.JSON(), nullable=False),
        sa.Column("feature_importance_top20", sa.JSON(), nullable=False),
        sa.Column("trained_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_model_eval_metrics_model_version", "model_eval_metrics", ["model_version"], unique=True)


def downgrade() -> None:
    op.drop_table("model_eval_metrics")
    op.drop_table("known_company_benchmarks")
    op.drop_table("analysis_feedbacks")
    op.drop_table("job_analyses")
