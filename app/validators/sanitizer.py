import bleach


def sanitize_text(text: str) -> str:
    """Видаляє ВСІ HTML-теги (tags=[]) і екранує спецсимволи (< > &).
    '<script>alert(1)</script>Добре' → 'alert(1)Добре'"""
    return bleach.clean(text, tags=[], attributes={}, strip=True).strip()
