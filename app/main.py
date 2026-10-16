from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app import models  # noqa: F401 — реєструє моделі в Base.metadata
from app.auth.router import router as auth_router
from app.config import CORS_ORIGINS
from app.database import Base
from app.middleware.rate_limiter import limiter
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routes.admin import router as admin_router
from app.routes.students import router as students_router
from app.routes.teachers import router as teachers_router

app = FastAPI(title="Електронний деканат", version="1.0.0")

# --- Rate Limiting (slowapi) ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS: лише конкретні домени ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
# Додається ОСТАННІМ → стає зовнішнім шаром і ставить заголовки на ВСІ відповіді
app.add_middleware(SecurityHeadersMiddleware)

# --- Роутери ---
app.include_router(auth_router)
app.include_router(students_router)
app.include_router(teachers_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {"message": "Electronic Dean's Office API"}


@app.get("/health")
def health():
    return {"status": "healthy", "database": "SQLite",
            "tables": len(Base.metadata.tables)}
