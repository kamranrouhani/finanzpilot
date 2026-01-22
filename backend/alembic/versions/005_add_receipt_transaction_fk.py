"""Add foreign key constraint to receipt.transaction_id

Revision ID: 005_add_receipt_transaction_fk
Revises: 004_add_budgets_table
Create Date: 2026-01-22 05:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_add_receipt_transaction_fk'
down_revision: Union[str, None] = '004_add_budgets_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add foreign key constraint and index to receipt.transaction_id."""
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_receipts_transaction_id',
        'receipts',
        'transactions',
        ['transaction_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Add index for performance
    op.create_index(
        'ix_receipts_transaction_id',
        'receipts',
        ['transaction_id']
    )


def downgrade() -> None:
    """Remove foreign key constraint and index."""
    op.drop_index('ix_receipts_transaction_id', table_name='receipts')
    op.drop_constraint('fk_receipts_transaction_id', 'receipts', type_='foreignkey')
