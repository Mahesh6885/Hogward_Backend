"""Helper utilities."""
import math


def paginate(query, page: int, page_size: int):
    """Apply pagination to a SQLAlchemy query, return (items, total, total_pages)."""
    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total, total_pages


def generate_project_code(last_id: int) -> str:
    """Generate a human-readable project code like PRJ-00001."""
    return f"PRJ-{last_id:05d}"


def success_response(message: str, data=None) -> dict:
    """Standard success response envelope."""
    return {"success": True, "message": message, "data": data}


def error_response(message: str, error_code: str = "ERROR") -> dict:
    """Standard error response envelope."""
    return {"success": False, "message": message, "error_code": error_code}
