"""seed_data

Revision ID: e356f1a85cb2
Revises: b5a2a35738e2
Create Date: 2026-07-03 23:26:01.785237

"""
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e356f1a85cb2'
down_revision: str | Sequence[str] | None = 'b5a2a35738e2'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Define tables for bulk insert
    settings_table = sa.table(
        'settings',
        sa.column('key', sa.String),
        sa.column('value', sa.String),
        sa.column('value_type', sa.String),
        sa.column('category', sa.String),
        sa.column('description', sa.String),
        sa.column('updated_at', sa.DateTime),
    )

    variables_table = sa.table(
        'variables',
        sa.column('id', sa.String),
        sa.column('name', sa.String),
        sa.column('display_name', sa.String),
        sa.column('description', sa.String),
        sa.column('default_value', sa.String),
        sa.column('value_type', sa.String),
        sa.column('is_required', sa.Integer),
        sa.column('is_system', sa.Integer),
        sa.column('scope', sa.String),
        sa.column('sort_order', sa.Integer),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )

    now = datetime.now(UTC)

    # Insert default settings
    op.bulk_insert(
        settings_table,
        [
            {
                "key": "auto_embed",
                "value": "true",
                "value_type": "boolean",
                "category": "ai",
                "description": "Automatically generate embeddings for contexts",
                "updated_at": now,
            },
            {
                "key": "auto_tag",
                "value": "true",
                "value_type": "boolean",
                "category": "ai",
                "description": "Automatically suggest tags for new contexts",
                "updated_at": now,
            },
            {
                "key": "learning_enabled",
                "value": "true",
                "value_type": "boolean",
                "category": "ai",
                "description": "Enable post-conversation learning loop",
                "updated_at": now,
            },
            {
                "key": "theme",
                "value": "dark",
                "value_type": "text",
                "category": "ui",
                "description": "Application theme (light or dark)",
                "updated_at": now,
            },
            {
                "key": "default_model",
                "value": "gpt-4.1",
                "value_type": "text",
                "category": "ai",
                "description": "Default model for chat completions",
                "updated_at": now,
            },
            {
                "key": "token_limit",
                "value": "128000",
                "value_type": "number",
                "category": "ai",
                "description": "Default token budget limit",
                "updated_at": now,
            },
            {
                "key": "search_top_k",
                "value": "10",
                "value_type": "number",
                "category": "search",
                "description": "Number of contexts to retrieve by default",
                "updated_at": now,
            },
        ],
    )

    # Insert default system variables
    op.bulk_insert(
        variables_table,
        [
            {
                "id": str(uuid.uuid4()),
                "name": "date",
                "display_name": "Current Date",
                "description": "System-defined active date variable",
                "default_value": None,
                "value_type": "date",
                "is_required": 1,
                "is_system": 1,
                "scope": "system",
                "sort_order": 1,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "time",
                "display_name": "Current Time",
                "description": "System-defined active time variable",
                "default_value": None,
                "value_type": "text",
                "is_required": 1,
                "is_system": 1,
                "scope": "system",
                "sort_order": 2,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "workspace",
                "display_name": "Active Workspace",
                "description": "System-defined active workspace name",
                "default_value": None,
                "value_type": "text",
                "is_required": 1,
                "is_system": 1,
                "scope": "system",
                "sort_order": 3,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "model",
                "display_name": "Selected Chat Model",
                "description": "System-defined active chat model name",
                "default_value": None,
                "value_type": "text",
                "is_required": 1,
                "is_system": 1,
                "scope": "system",
                "sort_order": 4,
                "created_at": now,
                "updated_at": now,
            },
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(sa.text("DELETE FROM settings WHERE key IN ('auto_embed', 'auto_tag', 'learning_enabled', 'theme', 'default_model', 'token_limit', 'search_top_k');"))
    op.execute(sa.text("DELETE FROM variables WHERE scope = 'system';"))
