# RunBeat Backend

FastAPI + LangChain служба, що керує AI-діалогом, створює воркаути та генерує плейлисти.

---

## 🔧 Prerequisites

- Python **3.11+** (рекомендовано `uv` як package manager)
- Supabase проект (Postgres)
- Spotify Developer app
- OpenAI API ключ

---

## 🚀 Setup & Local Run

```bash
cd apps/backend
python -m venv .venv && source .venv/bin/activate   # або `uv venv && source .venv/bin/activate`
pip install -r requirements.txt                     # або `uv pip install -r requirements.txt`
cp .env.example .env
```

1. Заповніть `.env` (див. [ENV_SETUP_GUIDE.md](./ENV_SETUP_GUIDE.md)). Мінімум:
   - `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
   - `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI`
   - `OPENAI_API_KEY`, `OPENAI_MODEL` (+ окремі моделі для агентів за потреби)
   - `CORS_ORIGINS=["http://localhost:5173"]`
2. Запустіть сервер:

```bash
uvicorn app.main:app --reload
```

3. Health check:

```bash
curl http://localhost:8000/health
```

Swagger UI доступний на `http://localhost:8000/docs`, ReDoc — `http://localhost:8000/redoc`.

---

## 🗂 Структура

```
app/
├── api/routes/             # REST endpoints (chat, playlists, workouts, auth, ...)
├── agents/                 # Supervisor + LangChain tools/prompts
├── services/               # Conversation persistence, Spotify, playlist generator, etc.
├── schemas/                # Pydantic V2 models (chat/workout/playlist/conversation)
├── core/config.py          # Settings (Pydantic Settings)
└── main.py                 # FastAPI entrypoint
```

Ключові сервіси:
- `services/workout_builder.py` — головний LangChain агент.
- `agents/supervisor.py` — оркестрація стану розмови.
- `services/playlist_generator.py` — алгоритмічний підбір треків (Spotify API).

---

## 🧪 Development Recipes

| Завдання | Команда |
| --- | --- |
| Run tests | `pytest` |
| Lint | `ruff check app` |
| Format | `black app --line-length 100` |
| Type-check prompt configs | Під час імпорту `app.core.config` (валідація Pydantic) |

Корисні scripts:
- `test_api_endpoints.sh`, `test_chat_http.sh` – швидкі smoke-тести.
- `run_tests.sh` – послідовний запуск тестів/лінтів у CI.

---

## 🗃 Database / Supabase

- Початкова схема: `DATABASE_MIGRATION_COMPLETE_v2.sql` (виконайте у Supabase SQL Editor).
- Основні таблиці: `users`, `workouts`, `playlists`, `conversations`, `error_logs`.
- RLS правила вже включені у файл міграцій.

---

## ☁️ Deployment (Railway)

- У директорії є `railway.json` (Nixpacks builder). Railway автоматично викликає:
  - `pip install -r requirements.txt`
  - `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Створіть сервіс → підключіть GitHub репозиторій → вкажіть environment variables.
- Після отримання `*.up.railway.app`:
  1. Додайте URL у Spotify Dashboard (`SPOTIFY_REDIRECT_URI=https://<domain>/auth/spotify/callback`).
  2. Оновіть `CORS_ORIGINS` / `FRONTEND_URL`.
  3. Перезапустіть сервіс (Railway робить це автоматично).

---

## 📚 Додаткові матеріали

- [ENV_SETUP_GUIDE.md](./ENV_SETUP_GUIDE.md) — детальний гайд по змінним середовища.
- [ENV_EXAMPLE.md](./ENV_EXAMPLE.md) — приклад заповненого `.env`.
- [OPENAI_MODELS_USAGE.md](./OPENAI_MODELS_USAGE.md) — поради щодо підбору моделей та вартості.
- [docs/LOGOUT_FEATURE.md](./docs/LOGOUT_FEATURE.md) — опис реалізації `/auth/logout`.

Оновлено: **19 листопада 2025**

