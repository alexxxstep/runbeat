# RunBeat 🏃‍♂️🎵

> AI-помічник для створення персоналізованих workout-планів та Spotify плейлистів через природний діалог

## 🎯 Що це?

RunBeat — це AI-driven застосунок, який:

- Веде живий діалог українською для збору параметрів тренування
- Автоматично створює workout-план (тривалість, інтенсивність, HR зони)
- Генерує персоналізований Spotify плейлист з урахуванням BPM, енергії та жанрів
- Зберігає історію тренувань та дозволяє повторно генерувати плейлисти

**Технологічний стек**:

- **Backend**: Python 3.11+, FastAPI, LangChain (multi-agent), Supabase, Spotify API
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Zustand
- **AI**: OpenAI GPT-4/4o (конфігуровані моделі для різних агентів)
- **Деплой**: Railway (Nixpacks)

## 📖 Архітектурна документація

Детальна документація системи розділена на два ключові документи:

### 🏗️ [Architecture Report](./docs/ARCHITECTURE_REPORT.md)

Високорівневий огляд архітектури з ASCII-діаграмами:

- Загальна схема системи (Frontend ↔ Backend ↔ Integrations)
- Backend layers (API → Services → AI Agents → Schemas)
- AI Conversation Stack (покроковий flow)
- Playlist & Prompt Flow (детальний lifecycle)
- End-to-End Data Flow (3 кроки: створення workout → підтвердження → генерація плейлиста)
- Stack Snapshot та deployment

### 🤖 [AI Conversation Architecture](./docs/AI_CONVERSATION_ARCHITECTURE.md)

Детальна документація LangChain multi-agent системи:

- SupervisorAgent та WorkoutBuilder (відповідальності, методи)
- Conversation State Machine (ASCII state diagram)
- LangChain Tools (`extract_workout_parameters`, `create_workout_from_params`)
- System Prompts та conversation flow
- Music Prompt lifecycle (від збору до Spotify)
- Backend ↔ Frontend контракт
- Тестування (41 unit/integration тест)
- Troubleshooting та best practices

## 🗂 Структура репозиторію

```
.
├── apps/
│   ├── backend/        # FastAPI + LangChain служба
│   └── web/            # React + Vite клієнт
├── docs/               # Головні архітектурні документи
└── README.md           # Ви тут 🙂
```

## ⚡ Швидкий старт

### Backend (FastAPI)

```bash
cd apps/backend
python -m venv .venv && source .venv/bin/activate  # або `uv venv`
pip install -r requirements.txt                    # або `uv pip install -r requirements.txt`
cp .env.example .env && # заповніть значення (див. ENV_SETUP_GUIDE.md)
uvicorn app.main:app --reload
```

Перевірка: `curl http://localhost:8000/health`

### Web (React + Vite)

```bash
cd apps/web
npm install
cp .env.example .env  # встановіть VITE_API_URL
npm run dev
```

UI доступний на `http://localhost:5173`. За замовчуванням чат працює з бекендом, що слухає `http://localhost:8000`.

## 🧪 Тести та якість

| Частина             | Команда                            |
| ------------------- | ---------------------------------- |
| Backend tests       | `cd apps/backend && pytest`        |
| Backend lint/format | `ruff check app`, `black app`      |
| Web tests           | `cd apps/web && npm test` (Vitest) |
| Web lint            | `npm run lint`                     |

## 🚀 Деплой

- **Backend**: Railway через `apps/backend/railway.json` (Nixpacks builder + `uvicorn`). Налаштуйте env variables у Railway Dashboard.
- **Web**: Railway Nixpacks за допомогою `apps/web/nixpacks.toml` (Node 20 + `npm ci && npm run build`, сервиться через `npx serve`).
- Перед деплоєм оновіть Spotify Redirect URI та CORS (`apps/backend/.env`).

## 📚 Додаткова документація

- **[Backend README](./apps/backend/README.md)** — специфіка backend (структура, запуск, Railway деплой, налаштування `.env`)
- **[Backend Tests](./apps/backend/tests/README.md)** — інформація про тестування (unit, integration, coverage)

---

> **Версія**: 2.1
> **Останнє оновлення**: 19 листопада 2025
> **Ліцензія**: MIT
