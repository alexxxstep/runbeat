# Приклад .env файлу

Скопіюйте цей файл в `.env` та заповніть своїми значеннями.

```env
# ============================================
# Supabase Configuration
# ============================================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ============================================
# Spotify OAuth
# ============================================
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8000/auth/spotify/callback

# ============================================
# OpenAI Configuration
# ============================================
OPENAI_API_KEY=sk-proj-ваш_ключ
OPENAI_MODEL=gpt-4

# Optional: Different models for different agents (falls back to OPENAI_MODEL if not set)
# OPENAI_MODEL_PARSER=gpt-4
# OPENAI_MODEL_CONVERSATION=gpt-3.5-turbo
# OPENAI_MODEL_SUPERVISOR=gpt-4

# ============================================
# LangChain Feature Flags
# ============================================
USE_LANGCHAIN_PARSER=true
USE_LANGCHAIN_SUPERVISOR=true

# ============================================
# App Settings
# ============================================
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000","http://localhost:19006"]
FRONTEND_URL=

# ============================================
# Railway/Deployment
# ============================================
PORT=8000
RAILWAY_PUBLIC_DOMAIN=
```

## Пояснення змінних OpenAI

### Обов'язкові:

- `OPENAI_API_KEY` - API ключ OpenAI (обов'язково)
- `OPENAI_MODEL` - Модель за замовчуванням для всіх агентів (за замовчуванням: `gpt-4`)

### Опціональні (для різних агентів):

- `OPENAI_MODEL_PARSER` - Модель для parser tools (парсинг даних)
- `OPENAI_MODEL_CONVERSATION` - Модель для ConversationAgent (розмова та створення воркаутів)
- `OPENAI_MODEL_SUPERVISOR` - Модель для SupervisorAgent (координація)

Якщо опціональні змінні не встановлені, використовується `OPENAI_MODEL`.

## Приклади конфігурацій

### Варіант 1: Одна модель для всіх (найпростіше)

```env
OPENAI_API_KEY=sk-proj-ваш_ключ
OPENAI_MODEL=gpt-4
```

### Варіант 2: Оптимізація вартості (різні моделі)

```env
OPENAI_API_KEY=sk-proj-ваш_ключ
OPENAI_MODEL=gpt-4  # Fallback
OPENAI_MODEL_PARSER=gpt-4  # Точний парсинг
OPENAI_MODEL_CONVERSATION=gpt-3.5-turbo  # Дешевша розмова
OPENAI_MODEL_SUPERVISOR=gpt-4  # Координація
```

### Варіант 3: Економія (gpt-3.5 для тестування)

```env
OPENAI_API_KEY=sk-proj-ваш_ключ
OPENAI_MODEL=gpt-3.5-turbo
```
