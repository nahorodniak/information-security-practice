# README

# Електронний деканат — захищений REST API

**ПІБ:** Нагородняк Анастасія

**Група:** 233з он (Б2F501ЗОН24)

**Дисципліна:** Безпека інформаційних систем — Заочна практична робота №1

FastAPI + SQLite + SQLAlchemy/Alembic + JWT (access/refresh) + RBAC + bcrypt.
Проєкт реалізує кілька незалежних шарів захисту (Defense in Depth):

1. ізольоване контейнерне середовище, секрети поза кодом (Docker Compose, `.env`);
2. модель доступу RBAC «Користувач → Роль → Дозвіл» у БД, принцип мінімальних привілеїв;
3. bcrypt-хешування паролів + сувора Pydantic-валідація;
4. JWT-автентифікація (401) та рольова авторизація (403);
5. захист веб-рівня: Security Headers, CORS allow-list, Rate Limiting, санітизація проти Stored XSS.

## Запуск

```bash
git clone https://github.com/YOUR_USERNAME/information-security-practice.git
cd information-security-practice

cp .env.example .env            # у .env вкажіть ключ: openssl rand -hex 32
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api python -m app.seed
```

- API: [http://localhost:8000](http://localhost:8000/)
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

Повне скидання БД: `docker compose down -v` → `docker compose up -d --build` → міграція → seed.

## Ендпоінти та ролі

| Метод | Шлях | Доступ | Примітка |
| --- | --- | --- | --- |
| GET | `/`, `/health` | public | `/health` → `tables: 8` |
| POST | `/auth/register` | public | ліміт 10/хв; нова роль — лише `student` |
| POST | `/auth/login` | public | ліміт 5/хв; повертає access + refresh |
| POST | `/auth/refresh` | public (потрібен refresh token) | ротація пари токенів |
| GET | `/auth/me` | будь-який автентифікований | лише access token |
| GET | `/students/me/grades` | student | лише власні оцінки (id з токена) |
| GET | `/teachers/students/{id}/grades` | teacher, admin |  |
| POST | `/teachers/grades` | teacher, admin | `assigned_by` = автор оцінки |
| GET | `/admin/users` | admin |  |

## Тестові облікові записи

| Логін | Роль |
| --- | --- |
| `admin` | admin |
| `teacher01` | teacher |
| `student01` | student |

Паролі задані лише в `app/seed.py`.

## Матриця RBAC (seed)

| Дозвіл | admin | teacher | student |
| --- | --- | --- | --- |
| read_grades | ✓ | ✓ | ✓ |
| edit_grades | ✓ | ✓ | — |
| read_schedule | ✓ | ✓ | ✓ |
| manage_users / manage_groups / manage_subjects | ✓ | — | — |
| view_reports | ✓ | ✓ | — |

## Фінальна перевірка (чиста БД → `alembic upgrade head` → seed)

Логін обмежено 5 запитами/хв, тому тест №20 виконується останнім.

| № | Сценарій | Очікування | Фактичний результат |
| --- | --- | --- | --- |
| 1 | `GET /health` | 200, `tables: 8` | **200**, `{"status":"healthy","database":"SQLite","tables":8}` |
| 2 | Реєстрація (валідні дані) | 201, без `password_hash` | **201**, у відповіді немає `password_hash` |
| 3 | Дублікат username | 409 | **409** «Username вже зайнятий» |
| 4 | Слабкий пароль | 422 | **422** «Пароль має містити хоча б одну велику літеру» |
| 5 | XSS в `full_name` | 422 | **422** (allow-list відхилив `<script>`) |
| 6 | Логін admin | 200, access + refresh | **200**, обидва токени |
| 7 | Невірний пароль / неіснуючий логін | 401, однаковий текст | **401** «Невірний логін або пароль» (в обох випадках) |
| 8 | `GET /auth/me` без токена | 401 | **401** «Потрібна автентифікація» |
| 9 | Токен `abc.def.ghi` | 401 | **401** «Невалідний або протермінований токен» |
| 10 | Refresh замість access | 401 | **401** «Потрібен access token» |
| 11 | `POST /auth/refresh` | 200 | **200**, нова пара токенів |
| 12 | `GET /students/me/grades` (student) | 200 | **200**, оцінка 92 |
| 13 | Студент → `/admin/users` | 403 | **403** |
| 14 | Викладач → `/admin/users` | 403 | **403** |
| 15 | Адмін → `/admin/users` | 200 | **200**, список користувачів |
| 16 | Оцінка 9999 | 422 | **422** «Input should be less than or equal to 100» |
| 17 | Stored XSS у коментарі | 201, тег вирізано | **201**, `"comment":"alert(document.cookie)Добре"` |
| 18 | Security Headers `/health` | CSP, XFO, nosniff, HSTS, Referrer-Policy | усі присутні (+ `X-XSS-Protection: 0`, `Cache-Control: no-store`) |
| 19 | CORS `Origin: http://evil.example` | 400, без `access-control-allow-origin` | **400**, заголовка немає; для `http://localhost:3000` — **200** з `access-control-allow-origin` |
| 20 | 6 × `POST /auth/login` за хвилину | 429 | **401 ×5, потім 429** |

Додатково перевірено: токен з `alg: none` → 401; токен, підписаний чужим ключем → 401;
студент → `POST /teachers/grades` → 403; повторний `python -m app.seed` → «Database already seeded.».

## STRIDE

| Загроза | Контрзахід у коді | Що можна покращити |
| --- | --- | --- |
| **S**poofing — підроблення особи / токена | bcrypt (cost 12), підписаний JWT HS256, `algorithms=[...]` (проти `alg: none`), перевірка `type`, однакова відповідь 401 (проти enumeration), CORS allow-list | RS256 / ключі, що ротуються; MFA |
| **T**ampering — зміна даних | підпис JWT, Pydantic-валідація (діапазон оцінки 0–100, allow-list імені), ORM (параметризовані запити → немає SQLi), санітизація `comment` (bleach) | цифровий підпис записів оцінок, аудит-журнал змін |
| **R**epudiation — відмова від дій | поле `assigned_by` в оцінках (підзвітність) | окрема таблиця аудиту (хто/що/коли/з якої IP) |
| **I**nformation Disclosure — витік даних | `UserResponse` без `password_hash`; студент бачить лише свої оцінки; CSP `default-src 'none'`, `nosniff`, `Cache-Control: no-store`; секрети лише в `.env` | HttpOnly-cookie, шифрування БД, менеджер секретів |
| **D**enial of Service / Brute force | Rate Limiting (`/login` 5/хв, `/register` 10/хв), обмеження довжин полів | Redis-сховище лімітів (зараз in-memory), WAF, блокування акаунта після N невдач |
| **E**levation of Privilege | `require_role` (ролі беруться з БД, а не з токена), нові користувачі лише `student`, мінімальні привілеї | Redis-blacklist токенів і відкликання refresh token, перевірка permissions (а не лише ролей) |

## Скріншоти

[Untitled](Untitled%203fbb94942094816ca970d347e4c969d4.csv)