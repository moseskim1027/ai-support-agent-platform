"""Add orders table with sample data

Revision ID: 003
Revises: 002
Create Date: 2026-02-21 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create orders table
    op.create_table(
        "orders",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("items", sa.Integer(), nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("tracking_number", sa.String(length=50), nullable=True),
        sa.Column("estimated_delivery", sa.Date(), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_orders_customer_name"), "orders", ["customer_name"], unique=False)
    op.create_index(op.f("ix_orders_status"), "orders", ["status"], unique=False)

    # Insert sample order data
    op.execute("""
        INSERT INTO orders (id, customer_name, status, items, total_amount, tracking_number, estimated_delivery, metadata, created_at)
        VALUES
        ('ORD-10001', 'John Smith', 'delivered', 3, 249.99, 'TRK987654', '2026-02-15', '{"notes": "Delivered successfully"}', '2026-02-10 10:30:00'),
        ('ORD-10002', 'Jane Doe', 'shipped', 2, 149.50, 'TRK876543', '2026-02-24', '{"carrier": "FedEx"}', '2026-02-18 14:20:00'),
        ('ORD-10003', 'Bob Johnson', 'processing', 1, 89.99, NULL, '2026-02-28', '{"priority": "standard"}', '2026-02-20 09:15:00'),
        ('ORD-10004', 'Alice Williams', 'pending', 5, 599.99, NULL, '2026-03-05', '{"payment_method": "credit_card"}', '2026-02-21 16:45:00'),
        ('ORD-10005', 'John Smith', 'shipped', 1, 79.99, 'TRK765432', '2026-02-25', '{"carrier": "UPS"}', '2026-02-19 11:00:00'),
        ('ORD-10006', 'Charlie Brown', 'delivered', 2, 159.99, 'TRK654321', '2026-02-18', '{"signature_required": true}', '2026-02-12 13:30:00'),
        ('ORD-10007', 'Jane Doe', 'processing', 4, 329.99, NULL, '2026-03-01', '{"gift_wrap": true}', '2026-02-21 08:20:00'),
        ('ORD-10008', 'David Lee', 'shipped', 2, 199.99, 'TRK543210', '2026-02-26', '{"express_shipping": true}', '2026-02-20 15:10:00'),
        ('ORD-10009', 'Emma Davis', 'cancelled', 1, 49.99, NULL, NULL, '{"cancellation_reason": "customer_request"}', '2026-02-17 10:00:00'),
        ('ORD-10010', 'Frank Miller', 'delivered', 3, 279.99, 'TRK432109', '2026-02-16', '{"feedback_rating": 5}', '2026-02-11 12:45:00')
    """)


def downgrade() -> None:
    op.drop_index(op.f("ix_orders_status"), table_name="orders")
    op.drop_index(op.f("ix_orders_customer_name"), table_name="orders")
    op.drop_table("orders")
