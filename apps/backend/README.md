# RunBeat Backend

FastAPI backend for RunBeat - AI music assistant for runners.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
# or using uv:
uv pip install -r requirements.txt
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Fill in `.env` with your credentials:
   - Supabase URL and keys
   - Spotify Client ID and Secret
   - OpenAI API Key

4. Run the server:
```bash
uvicorn app.main:app --reload
```

5. Check health:
```bash
curl http://localhost:8000/health
```

## API Documentation

When running in development mode, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
app/
├── main.py              # FastAPI app entry
├── core/
│   └── config.py       # Settings (Pydantic)
├── api/
│   └── routes/         # API endpoints
├── services/           # Business logic
├── models/             # Pydantic models
├── schemas/            # API schemas
└── utils/              # Utilities
```

## Development

- Format code: `black app/ --line-length 100`
- Lint code: `ruff check app/`
- Run tests: `pytest`

## Deployment

### Railway Deployment

Для деплою на Railway через GitHub:

1. **Швидкий старт:** Дивіться [RAILWAY_QUICK_START.md](./RAILWAY_QUICK_START.md)
2. **Детальна інструкція:** Дивіться [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)

**Важливо:** Після деплою на Railway не забудьте:
- Оновити `SPOTIFY_REDIRECT_URI` в Railway Variables
- Додати production URL в Spotify Dashboard

## Database Setup

### Initial Migration

Run the complete database migration in your Supabase SQL Editor:

```bash
# Execute this file in Supabase SQL Editor
DATABASE_MIGRATION_COMPLETE_v2.sql
```

This migration includes:
- ✅ Users, Workouts, Playlists tables
- ✅ Conversations table (AI chat history)
- ✅ Error logs table
- ✅ All indexes and RLS policies
- ✅ Genre normalization support

See [DATABASE_MIGRATION_COMPLETE_v2.sql](./DATABASE_MIGRATION_COMPLETE_v2.sql) for details.

## Features

### AI Chat System
- 🤖 Multi-agent LangChain architecture
- 💬 Natural language workout planning
- 🧠 User pattern learning & personalization
- 📊 Conversation analytics

### Playlist Generation
- 🎵 Dual variant generation
- ⚡ BPM matching to workout intensity
- 🎼 Genre-based track selection
- 🔄 Track exclusion & regeneration

### API Endpoints
- `/chat/message` - AI conversation
- `/workouts` - Workout CRUD
- `/playlists` - Playlist generation & history
- `/analytics` - User patterns & insights
- `/auth/spotify` - Spotify OAuth flow

## Documentation

- [Environment Setup Guide](./ENV_SETUP_GUIDE.md) - Покрокова інструкція по заповненню .env
- [OpenAI Models Usage](./OPENAI_MODELS_USAGE.md) - AI integration & costs
- [Agents Analysis](./docs/AGENTS_ANALYSIS.md) - Multi-agent system details
- [Railway Quick Start](./RAILWAY_QUICK_START.md) - Швидкий старт деплою на Railway
- [Railway Deployment](./RAILWAY_DEPLOYMENT.md) - Детальна інструкція деплою

