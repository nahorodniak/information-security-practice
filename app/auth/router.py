from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.jwt_handler import (create_access_token, create_refresh_token,
                                  verify_token)
from app.database import get_db
from app.models import Role, User
from app.schemas import (LoginRequest, TokenRefreshRequest, TokenResponse,
                         UserCreate, UserInfo, UserResponse)
from app.security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _primary_role(user: User) -> str:
    return user.roles[0].name if user.roles else "student"


@router.post("/register", response_model=UserResponse,
             status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Username вже зайнятий")
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email вже зареєстровано")

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=hash_password(user_data.password),
    )
    student_role = db.query(Role).filter(Role.name == "student").first()
    if student_role:
        new_user.roles.append(student_role)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Невірний логін або пароль")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Акаунт деактивовано")
    return TokenResponse(
        access_token=create_access_token(user.id, _primary_role(user)),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: TokenRefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = verify_token(body.refresh_token)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Невалідний refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Потрібен refresh token")

    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Невалідний refresh token")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Користувача не знайдено")
    # Ротація: видаємо НОВУ пару токенів
    return TokenResponse(
        access_token=create_access_token(user.id, _primary_role(user)),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserInfo)
def me(current_user: User = Depends(get_current_user)):
    return UserInfo(id=current_user.id, username=current_user.username,
                    email=current_user.email, full_name=current_user.full_name,
                    roles=[r.name for r in current_user.roles])
