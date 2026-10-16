from fastapi import FastAPI

from app import models  # noqa: F401 — реєструє моделі в Base.metadata
from app.auth.router import router as auth_router
from app.database import Base
from app.routes.admin import router as admin_router
from app.routes.students import router as students_router
from app.routes.teachers import router as teachers_router

app = FastAPI(title="Електронний деканат")

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
