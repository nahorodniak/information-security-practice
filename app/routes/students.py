from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database import get_db
from app.models import Grade, User

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/me/grades")
def my_grades(current_user: User = Depends(require_role("student")),
              db: Session = Depends(get_db)):
    """Студент бачить ЛИШЕ власні оцінки (student_id береться з токена, не з URL)."""
    grades = db.query(Grade).filter(Grade.student_id == current_user.id).all()
    return {
        "student": current_user.username,
        "grades": [{"subject_id": g.subject_id, "grade": g.grade,
                    "comment": g.comment, "date": g.date_assigned.isoformat()}
                   for g in grades],
    }
