from slowapi import Limiter
from slowapi.util import get_remote_address

# Ключ ліміту — IP-адреса клієнта
limiter = Limiter(key_func=get_remote_address)
