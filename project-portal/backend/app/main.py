"""FastAPI application entry point."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.routes import auth, users, topics, projects, admin

app = FastAPI(
    title=settings.APP_NAME,
    description="""
## Project Portal API

A private project topic selection and review portal.

### Roles
- **ADMIN**: Full access — manage users, topics, projects, reviews
- **USER**: Limited access — view own profile, submit project, view own reviews

### Domains
- **AI**: Gets 10 random AI topics to choose from
- **CYBERSECURITY**: Gets 10 random Cybersecurity topics
- **OPEN_INNOVATION**: Enters a custom project topic

### Authentication
Use `POST /api/auth/login` to obtain a Bearer token. Include it in the `Authorization` header.
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Exception handlers ───────────────────────────────────────────────────────

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": str(detail), "error_code": "HTTP_ERROR"},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    from fastapi.encoders import jsonable_encoder
    errors = exc.errors()
    messages = []
    for e in errors:
        loc = " -> ".join(str(l) for l in e["loc"] if l != "body")
        messages.append(f"{loc}: {e['msg']}" if loc else e["msg"])
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "; ".join(messages),
            "error_code": "VALIDATION_ERROR",
            "details": jsonable_encoder(errors),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import logging
    logging.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error", "error_code": "INTERNAL_ERROR"},
    )

# ─── Startup Event ────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    from app.database.database import engine
    from app.database.migration import auto_migrate_schema
    try:
        auto_migrate_schema(engine)
    except Exception as e:
        import logging
        logging.error("Failed to auto migrate schema on startup: %s", e)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(topics.router)
app.include_router(projects.router)
app.include_router(admin.router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


# ─── Frontend Static Files ───────────────────────────────────────────────────
import os
from fastapi.staticfiles import StaticFiles

# Path to project-portal/frontend
_frontend_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend"
)
if os.path.exists(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")

