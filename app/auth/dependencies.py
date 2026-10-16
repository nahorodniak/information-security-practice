from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.auth.jwt_handler import verify_token
from app.database import get_db
from app.models import User

# auto_error=False → відсутній токен обробляємо самі і повертаємо 401 (а не 403)
bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail,
                         headers={"WWW-Authenticate": "Bearer"})


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """АУТЕНТИФІКАЦІЯ: хто ти? Перевіряє JWT і повертає User або 401."""
    if credentials is None:
        raise _unauthorized("Потрібна автентифікація")
    try:
        payload = verify_token(credentials.credentials)
    except JWTError:
        raise _unauthorized("Невалідний або протермінований токен")

    if payload.get("type") != "access":
        raise _unauthorized("Потрібен access token")

    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise _unauthorized("Невалідний токен")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise _unauthorized("Користувача не знайдено або деактивовано")
    return user


def require_role(*allowed_roles: str):
    """АВТОРИЗАЦІЯ: що тобі дозволено? Ролі беруться з БД, а не з токена."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_roles = {r.name for r in current_user.roles}
        if not user_roles.intersection(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Доступ заборонено. Потрібна роль: {', '.join(allowed_roles)}",
            )
        return current_user
    return role_checker
