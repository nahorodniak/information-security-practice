from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
def list_users(current_user: User = Depends(require_role("admin")),
               db: Session = Depends(get_db)):
    return [{"id": u.id, "username": u.username, "email": u.email,
             "roles": [r.name for r in u.roles]} for u in db.query(User).all()]
