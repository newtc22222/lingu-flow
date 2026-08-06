"""0003_question_bank

Decouples Question from ExamTemplate so questions become a reusable bank.

A question used to be hard-owned by exactly one template via a NOT NULL
`exam_template_id` with ON DELETE CASCADE. Placement now lives in the
`exam_template_questions` join table, so one question can appear in many exams
and deleting an exam removes only the links.

Also adds:
  * bank taxonomy on questions (`exam_type`, `part`, `passage_group`)
  * `questions.archived_at` for soft delete, so deleting a question can't
    cascade away the answer history of past sessions
  * `answer_records.order_index`, freezing the question order of a sitting so
    later edits to an exam can't retroactively rewrite finished results
  * `exam_templates.seed_key` / `seed_version`, so built-in content can be
    updated in place instead of being matched by display name

WARNING: `downgrade()` is lossy by construction. A question attached to several
templates collapses to one (`MIN(exam_template_id)`), and a question attached to
none cannot be represented at all under the restored NOT NULL column, so those
rows are deleted. Do not treat it as a production rollback plan — take a
database snapshot before deploying this.

Revision ID: 0003_question_bank
Revises: 0002_card_position_image_notes
Create Date: 2026-08-06 00:00:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0003_question_bank'
down_revision: Union[str, None] = '0002_card_position_image_notes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Maps the four built-in templates seeded before this migration onto the stable
# seed keys the seeder now matches on. The TOEIC entry deliberately points at
# `toeic-reading-full` — the key the expanded Parts 5/6/7 content uses — so that
# content lands as an in-place update of the existing row rather than as a
# second TOEIC exam alongside a stale one.
SEED_KEYS = {
    "TOEIC Part 5 — Incomplete Sentences Practice": "toeic-reading-full",
    "IELTS Academic Reading — Practice Set 1": "ielts-academic-reading-1",
    "HSK Level 2 — Vocabulary & Grammar": "hsk2-vocab-grammar",
    "JLPT N5 — Language Knowledge": "jlpt-n5-language-knowledge",
}


def upgrade() -> None:
    conn = op.get_bind()

    # 1. The junction table.
    op.create_table(
        'exam_template_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('exam_template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['exam_template_id'], ['exam_templates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        # Named to match ExamTemplateQuestion.__table_args__ exactly; Base.metadata
        # has no naming_convention, so a mismatch would churn on autogenerate.
        sa.UniqueConstraint(
            'exam_template_id', 'question_id',
            name='uq_exam_template_questions_template_question',
        ),
    )
    op.create_index(
        'ix_exam_template_questions_exam_template_id',
        'exam_template_questions', ['exam_template_id'],
    )
    op.create_index(
        'ix_exam_template_questions_question_id',
        'exam_template_questions', ['question_id'],
    )
    op.create_index(
        'ix_exam_template_questions_template_order',
        'exam_template_questions', ['exam_template_id', 'order_index'],
    )

    # 2. Backfill one link per existing question, preserving its order.
    #    UUIDs are generated Python-side to match how the app makes every other
    #    id — pgcrypto/gen_random_uuid() is not installed here.
    #    This reads rows, so it cannot run under `--sql` (offline) rendering;
    #    the DDL around it still renders for review.
    if not context.is_offline_mode():
        existing = conn.execute(
            sa.text("SELECT id, exam_template_id, order_index FROM questions")
        ).fetchall()
        if existing:
            conn.execute(
                sa.text(
                    "INSERT INTO exam_template_questions "
                    "(id, exam_template_id, question_id, order_index) "
                    "VALUES (:id, :template_id, :question_id, :order_index)"
                ),
                [
                    {
                        "id": str(uuid.uuid4()),
                        "template_id": str(row[1]),
                        "question_id": str(row[0]),
                        "order_index": row[2],
                    }
                    for row in existing
                ],
            )

    # 3. Bank taxonomy. exam_type is backfilled from the owning template, then
    #    tightened to NOT NULL.
    op.add_column('questions', sa.Column('exam_type', sa.String(), nullable=True))
    op.execute(
        """
        UPDATE questions SET exam_type = exam_templates.exam_type
        FROM exam_templates
        WHERE questions.exam_template_id = exam_templates.id
        """
    )
    # Defensive: the column is NOT NULL today so this should be a no-op, but a
    # stray orphan would otherwise fail the ALTER with a less obvious error.
    op.execute("UPDATE questions SET exam_type = 'custom' WHERE exam_type IS NULL")
    op.alter_column('questions', 'exam_type', nullable=False)
    op.create_index('ix_questions_exam_type', 'questions', ['exam_type'])

    # 4. Remaining new question columns.
    op.add_column('questions', sa.Column('part', sa.String(), nullable=True))
    op.add_column('questions', sa.Column('passage_group', sa.String(), nullable=True))
    op.add_column(
        'questions',
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_questions_part', 'questions', ['part'])
    op.create_index('ix_questions_exam_type_part', 'questions', ['exam_type', 'part'])
    op.create_index('ix_questions_passage_group', 'questions', ['passage_group'])
    op.create_index('ix_questions_archived_at', 'questions', ['archived_at'])

    # 5. Freeze each past sitting's question order. MUST run before step 7 —
    #    it is the one step that reads a column dropped below.
    op.add_column(
        'answer_records',
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
    )
    op.execute(
        """
        UPDATE answer_records SET order_index = questions.order_index
        FROM questions
        WHERE answer_records.question_id = questions.id
        """
    )

    # 6. Seed identity, so built-in content can be versioned rather than
    #    matched by display name.
    op.add_column('exam_templates', sa.Column('seed_key', sa.String(), nullable=True))
    op.add_column('exam_templates', sa.Column('seed_version', sa.String(), nullable=True))
    op.create_index(
        'ix_exam_templates_seed_key', 'exam_templates', ['seed_key'], unique=True,
    )
    for name, seed_key in SEED_KEYS.items():
        # op.execute renders under --sql as well as running online; the name is
        # inlined via a bound literal because offline mode has no parameters.
        op.execute(
            sa.text(
                "UPDATE exam_templates SET seed_key = :seed_key, seed_version = '1' "
                "WHERE name = :name AND is_public = true AND seed_key IS NULL"
            ).bindparams(seed_key=seed_key, name=name)
        )

    # 7. Drop the old ownership coupling.
    op.drop_index('ix_questions_exam_template_id', table_name='questions')
    op.drop_column('questions', 'exam_template_id')
    op.drop_column('questions', 'order_index')

    # 8. Recompute the denormalized counter from the junction.
    op.execute(
        """
        UPDATE exam_templates SET total_questions = (
            SELECT COUNT(*) FROM exam_template_questions
            WHERE exam_template_questions.exam_template_id = exam_templates.id
        )
        """
    )


def downgrade() -> None:
    # Restore the columns nullable so the backfill has somewhere to land.
    op.add_column(
        'questions',
        sa.Column('exam_template_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        'questions',
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
    )

    # Lossy: a question shared across templates collapses onto its lowest-id
    # template and loses every other placement.
    op.execute(
        """
        UPDATE questions SET
            exam_template_id = link.exam_template_id,
            order_index = link.order_index
        FROM (
            SELECT DISTINCT ON (question_id)
                   question_id, exam_template_id, order_index
            FROM exam_template_questions
            ORDER BY question_id, exam_template_id
        ) AS link
        WHERE questions.id = link.question_id
        """
    )
    # Bank questions attached to no template cannot exist under the restored
    # NOT NULL column.
    op.execute("DELETE FROM questions WHERE exam_template_id IS NULL")
    op.alter_column('questions', 'exam_template_id', nullable=False)
    op.create_foreign_key(
        'questions_exam_template_id_fkey', 'questions', 'exam_templates',
        ['exam_template_id'], ['id'], ondelete='CASCADE',
    )
    op.create_index('ix_questions_exam_template_id', 'questions', ['exam_template_id'])

    op.drop_index('ix_exam_templates_seed_key', table_name='exam_templates')
    op.drop_column('exam_templates', 'seed_version')
    op.drop_column('exam_templates', 'seed_key')

    op.drop_column('answer_records', 'order_index')

    op.drop_index('ix_questions_archived_at', table_name='questions')
    op.drop_index('ix_questions_passage_group', table_name='questions')
    op.drop_index('ix_questions_exam_type_part', table_name='questions')
    op.drop_index('ix_questions_part', table_name='questions')
    op.drop_index('ix_questions_exam_type', table_name='questions')
    op.drop_column('questions', 'archived_at')
    op.drop_column('questions', 'passage_group')
    op.drop_column('questions', 'part')
    op.drop_column('questions', 'exam_type')

    op.drop_index(
        'ix_exam_template_questions_template_order',
        table_name='exam_template_questions',
    )
    op.drop_index(
        'ix_exam_template_questions_question_id',
        table_name='exam_template_questions',
    )
    op.drop_index(
        'ix_exam_template_questions_exam_template_id',
        table_name='exam_template_questions',
    )
    op.drop_table('exam_template_questions')
