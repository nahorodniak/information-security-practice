from passlib.context import CryptContext

# Bcrypt: повільний алгоритм з вбудованою унікальною сіллю (cost factor 12)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Повертає bcrypt-хеш ($2b$12$...). Сіль генерується автоматично."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Порівнює введений пароль із хешем з БД (сіль береться з самого хешу)."""
    return pwd_context.verify(plain_password, hashed_password)
