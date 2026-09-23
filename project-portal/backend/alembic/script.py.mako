"""Alembic script template."""
# Revision identifiers, used by Alembic.
revision = "${revision}"
down_revision = ${down_revision | repr}
branch_labels = ${branch_labels | repr}
depends_on = ${depends_on | repr}

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
