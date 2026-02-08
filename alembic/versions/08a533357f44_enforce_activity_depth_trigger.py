"""enforce_activity_depth_trigger

Revision ID: 08a533357f44
Revises: 956ca4a28e29
Create Date: 2026-02-08 20:12:19.802601

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08a533357f44'
down_revision: Union[str, None] = '956ca4a28e29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Trigger for INSERT
    op.execute("""
    CREATE TRIGGER check_depth_insert 
    BEFORE INSERT ON activities 
    FOR EACH ROW
    BEGIN
        SELECT RAISE(ABORT, 'Max activity tree depth (3) exceeded')
        WHERE (
            WITH RECURSIVE parent_chain(id, parent_id, level) AS (
                SELECT id, parent_id, 1 FROM activities WHERE id = NEW.parent_id
                UNION ALL
                SELECT a.id, a.parent_id, pc.level + 1
                FROM activities a JOIN parent_chain pc ON a.id = pc.parent_id
            )
            SELECT MAX(level) FROM parent_chain
        ) >= 3;
    END;
    """)
    
    # Trigger for UPDATE (if parent_id changes)
    op.execute("""
    CREATE TRIGGER check_depth_update
    BEFORE UPDATE OF parent_id ON activities 
    FOR EACH ROW
    WHEN NEW.parent_id IS NOT NULL
    BEGIN
        SELECT RAISE(ABORT, 'Max activity tree depth (3) exceeded')
        WHERE (
            WITH RECURSIVE parent_chain(id, parent_id, level) AS (
                SELECT id, parent_id, 1 FROM activities WHERE id = NEW.parent_id
                UNION ALL
                SELECT a.id, a.parent_id, pc.level + 1
                FROM activities a JOIN parent_chain pc ON a.id = pc.parent_id
            )
            SELECT MAX(level) FROM parent_chain
        ) >= 3;
    END;
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS check_depth_insert")
    op.execute("DROP TRIGGER IF EXISTS check_depth_update")
