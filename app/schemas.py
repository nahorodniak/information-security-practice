import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

NAME_RE = re.compile(r"^[A-Za-zА-Яа-яІіЇїЄєҐґ'’ʼ .\-]+$")


# ── Реєстрація ──
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=30,
                          pattern=r"^[a-zA-Z0-9_]+$",
                          description="Латиниця, цифри, підкреслення")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)  # bcrypt: макс. 72 байти
    full_name: str = Field(..., min_length=2, max_length=100)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Пароль має містити хоча б одну велику літеру")
        if not re.search(r"[a-z]", v):
            raise ValueError("Пароль має містити хоча б одну малу літеру")
        if not re.search(r"\d", v):
            raise ValueError("Пароль має містити хоча б одну цифру")
        # bcrypt враховує лише перші 72 БАЙТИ (кирилиця = 2 байти/символ)
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Пароль занадто довгий (максимум 72 байти в UTF-8)")
        return v

    @field_validator("full_name")
    @classmethod
    def full_name_allowlist(cls, v: str) -> str:
        # Allow-list: лише літери, пробіл, апостроф, дефіс, крапка → жодних <script>
        if not NAME_RE.match(v):
            raise ValueError("Ім'я може містити лише літери, пробіл, апостроф, дефіс")
        return v.strip()


class UserResponse(BaseModel):
    """Відповідь БЕЗ password_hash."""
    id: int
    username: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Вхід ──
class LoginRequest(BaseModel):
    username: str = Field(..., max_length=30)
    password: str = Field(..., max_length=72)


class LoginResponse(BaseModel):
    message: str
    user_id: int
    username: str
    roles: list[str] = []
