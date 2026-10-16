from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Role, User
from app.schemas import LoginRequest, LoginResponse, UserCreate, UserResponse
from app.security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse,
             status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # 1. Унікальність username та email
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Username вже зайнятий")
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email вже зареєстровано")

    # 2. Хешуємо пароль — у БД потрапляє лише хеш
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=hash_password(user_data.password),
    )
    # 3. PoLP: нові користувачі отримують лише роль student
    student_role = db.query(Role).filter(Role.name == "student").first()
    if student_role:
        new_user.roles.append(student_role)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user  # UserResponse відфільтрує password_hash


@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    # Однакове повідомлення для «немає користувача» і «невірний пароль»
    # → захист від Username Enumeration
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Невірний логін або пароль")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Акаунт деактивовано")
    return LoginResponse(message="Вхід успішний", user_id=user.id,
                         username=user.username,
                         roles=[r.name for r in user.roles])
