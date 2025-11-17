# RunBeat - Quick Start Guide

**Швидкий старт для розробників** - запустіть RunBeat локально за 5 хвилин! ⚡

---

## 🎯 Що вам потрібно

- Python 3.11+
- Node.js 18+
- Git

**Опціонально для повного функціоналу:**
- Supabase account (безкоштовно)
- Spotify Developer account (безкоштовно)
- OpenAI API key (~$5-10 для тестування)

---

## ⚡ Швидкий старт (5 хвилин)

### 1. Клонуйте репозиторій

```bash
git clone https://github.com/yourusername/runbeat.git
cd runbeat
```

### 2. Backend Setup

```bash
cd apps/backend

# Встановіть залежності
pip install -r requirements.txt

# Створіть .env файл
cp .env.example .env

# Відредагуйте .env (мінімально потрібні):
# OPENAI_API_KEY=your_key_here
# SUPABASE_URL=your_url_here
# SUPABASE_SERVICE_KEY=your_key_here
# SPOTIFY_CLIENT_ID=your_id_here
# SPOTIFY_CLIENT_SECRET=your_secret_here

# Запустіть сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ Backend запущено на `http://localhost:8000`

### 3. Frontend Setup (в новому терміналі)

```bash
cd apps/web

# Встановіть залежності
npm install

# Створіть .env файл
cp .env.example .env

# Відредагуйте .env:
# VITE_API_URL=http://localhost:8000
# VITE_SUPABASE_URL=your_url_here
# VITE_SUPABASE_ANON_KEY=your_key_here

# Запустіть dev сервер
npm run dev
```

✅ Frontend запущено на `http://localhost:5173`

### 4. Database Setup

```bash
# 1. Створіть проект на supabase.com
# 2. Перейдіть в SQL Editor
# 3. Скопіюйте і виконайте:
#    apps/backend/DATABASE_MIGRATION_COMPLETE_v2.sql
```

✅ База даних готова!

---

## 🎉 Готово!

Відкрийте браузер: `http://localhost:5173`

Ви побачите RunBeat chat interface. Спробуйте:
- "Хочу пробігти 30 хвилин"
- "Інтервальна тренування 40 хв"
- "Легка пробіжка під рок музику"

---

## 🧪 Перевірте, що все працює

### Backend Health Check

```bash
curl http://localhost:8000/health
# Очікується: {"status":"healthy","service":"runbeat-api"}
```

### API Docs

Відкрийте: `http://localhost:8000/docs`

### Run Tests

```bash
# Backend tests
cd apps/backend
pytest tests/ -v

# Frontend tests
cd apps/web
npm run test
```

---

## 🔧 Налаштування IDE (VSCode)

### Рекомендовані розширення

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss"
  ]
}
```

### Settings

```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  }
}
```

---

## 📚 Наступні кроки

1. **Прочитайте документацію:**
   - [README.md](./README.md) - Загальний огляд
   - [ARCHITECTURE_REPORT.md](./docs/ARCHITECTURE_REPORT.md) - Архітектура
   - [API.md](./docs/API.md) - API документація

2. **Вивчіть код:**
   - `apps/backend/app/agents/` - AI агенти
   - `apps/web/src/pages/ChatPage.tsx` - Головна сторінка
   - `apps/backend/app/services/` - Бізнес-логіка

3. **Зробіть свій перший внесок:**
   - Перегляньте [Issues](https://github.com/yourusername/runbeat/issues)
   - Виберіть задачу з міткою `good first issue`
   - Прочитайте [CONTRIBUTING.md](./CONTRIBUTING.md)

---

## 🐛 Troubleshooting

### Backend не запускається

```bash
# Перевірте версію Python
python --version  # Має бути 3.11+

# Перевірте залежності
pip list | grep fastapi

# Перевірте .env файл
cat .env | grep OPENAI_API_KEY
```

### Frontend не запускається

```bash
# Перевірте версію Node
node --version  # Має бути 18+

# Очистіть node_modules
rm -rf node_modules package-lock.json
npm install

# Перевірте .env файл
cat .env | grep VITE_API_URL
```

### Database помилки

```bash
# Перевірте підключення до Supabase
curl https://your-project.supabase.co/rest/v1/

# Перевірте чи виконана міграція
# Зайдіть в Supabase Dashboard → SQL Editor
# Виконайте: SELECT * FROM users LIMIT 1;
```

### Spotify OAuth не працює

1. Перевірте Redirect URI в Spotify Dashboard:
   - Має бути: `http://localhost:8000/auth/spotify/callback`
2. Перевірте Client ID та Secret в `.env`
3. Перезапустіть backend після зміни `.env`

---

## 💡 Корисні команди

```bash
# Backend
cd apps/backend
pytest tests/ -v                    # Запустити тести
ruff check app/                     # Перевірити код
black app/                          # Форматувати код
uvicorn app.main:app --reload       # Запустити з hot reload

# Frontend
cd apps/web
npm run dev                         # Dev сервер
npm run build                       # Production build
npm run preview                     # Preview build
npm run lint                        # Lint code
npm run test                        # Run tests

# Database
# Supabase Dashboard → SQL Editor → Run migration
```

---

## 🎓 Навчальні ресурси

### LangChain (AI Agents)
- [LangChain Docs](https://python.langchain.com/)
- [Multi-Agent Tutorial](https://python.langchain.com/docs/modules/agents/)

### FastAPI
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Tutorial](https://fastapi.tiangolo.com/tutorial/)

### React + TypeScript
- [React Docs](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

### Supabase
- [Supabase Docs](https://supabase.com/docs)
- [PostgreSQL Tutorial](https://www.postgresql.org/docs/)

---

## 📞 Потрібна допомога?

- 💬 [GitHub Discussions](https://github.com/yourusername/runbeat/discussions)
- 🐛 [Report Bug](https://github.com/yourusername/runbeat/issues/new)
- 📧 Email: support@runbeat.app

---

**Happy Coding!** 🚀

Made with ❤️ by RunBeat Team

