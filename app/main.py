from fastapi import FastAPI

from app import models  # noqa: F401 — реєструє моделі в Base.metadata
from app.auth.router import router as auth_router
from app.database import Base

app = FastAPI(title="Електронний деканат")

app.include_router(auth_router)


@app.get("/")
def root():
    return {"message": "Electronic Dean's Office API"}


@app.get("/health")
def health():
    return {"status": "healthy", "database": "SQLite",
            "tables": len(Base.metadata.tables)}
