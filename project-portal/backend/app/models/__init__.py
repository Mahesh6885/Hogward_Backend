"""Models package — import all models so Alembic can discover them."""
from app.models.domain import Domain, DomainName  # noqa: F401
from app.models.user import User, UserRole, UserStatus  # noqa: F401
from app.models.problem_statement import ProblemStatement, RealmEnum, DifficultyEnum  # noqa: F401
from app.models.project import Project, ProjectStatus  # noqa: F401
from app.models.review import Review, ReviewStatus  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
