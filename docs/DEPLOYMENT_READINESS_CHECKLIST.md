# Чеклист готовності до деплою

**Дата:** 2025-11-14

## ✅ Готовність до деплою

### Backend (FastAPI)

#### Конфігурація ✅
- [x] `railway.json` налаштовано
- [x] `Procfile` створено
- [x] `runtime.txt` вказано Python 3.11
- [x] `requirements.txt` оновлено з усіма залежностями
- [x] Environment variables документовано

#### Функціональність ✅
- [x] API endpoints працюють
- [x] Conversation flow реалізовано
- [x] Spotify integration додано
- [x] LLM integration налаштовано
- [x] Database connection налаштовано
- [x] Error handling реалізовано
- [x] CORS налаштовано

#### Тести ✅
- [x] Unit tests проходять
- [x] Integration tests проходять
- [x] Conversation manager тести проходять

#### Документація ✅
- [x] API документація доступна (`/docs`)
- [x] Deployment guide створено
- [x] Environment variables guide створено

---

### Frontend Web (React + Vite)

#### Конфігурація ✅
- [x] `railway.json` налаштовано
- [x] `package.json` оновлено
- [x] Build команда налаштована
- [x] Environment variables документовано

#### Функціональність ✅
- [x] Chat interface реалізовано
- [x] Playlist display реалізовано
- [x] Spotify integration додано
- [x] Loading states додано
- [x] Error handling реалізовано
- [x] API client налаштовано

#### UX ✅
- [x] TypingIndicator додано
- [x] Playlist display покращено
- [x] Clarification questions відображаються
- [x] Spotify button працює

---

### Database (Supabase)

#### Міграції ✅
- [x] `DATABASE_MIGRATION_FINAL.sql` створено
- [x] `DATABASE_MIGRATION_ADD_CONVERSATIONS.sql` створено
- [x] Всі таблиці визначено
- [x] RLS policies налаштовано
- [x] Indexes створено

#### Таблиці ✅
- [x] `users` - користувачі
- [x] `workouts` - тренування
- [x] `playlists` - плейлисти
- [x] `conversations` - розмови
- [x] `playlist_tracks` - треки плейлистів

---

## ⚠️ Перед деплоєм потрібно перевірити

### 1. Environment Variables

**Backend (Railway):**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=https://your-railway-domain.up.railway.app/auth/spotify/callback
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=["https://your-web-domain.up.railway.app"]
```

**Web (Railway):**
```env
VITE_API_URL=https://your-backend-railway-domain.up.railway.app
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
```

### 2. Spotify OAuth

- [ ] Додати production redirect URI в Spotify Dashboard:
  - `https://your-backend-railway-domain.up.railway.app/auth/spotify/callback`
- [ ] Перевірити що Client ID та Secret правильні

### 3. Supabase

- [ ] Виконати міграції бази даних
- [ ] Перевірити RLS policies
- [ ] Перевірити що всі таблиці створено

### 4. Railway Deployment

**Backend:**
- [ ] Root Directory: `apps/backend`
- [ ] Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Всі environment variables додано

**Web:**
- [ ] Root Directory: `apps/web`
- [ ] Build Command: `npm install && npm run build`
- [ ] Start Command: `npx serve -s dist -l $PORT`
- [ ] Всі environment variables додано

---

## 🚀 Інструкції для деплою

### Крок 1: Backend Deployment

1. **Створити проект в Railway:**
   - Перейти на https://railway.app
   - New Project → Deploy from GitHub repo
   - Обрати репозиторій
   - Root Directory: `apps/backend`

2. **Налаштувати змінні оточення:**
   - Variables → Add всі змінні з вище
   - Зберегти

3. **Отримати Railway URL:**
   - Settings → Domains → Default Domain
   - Скопіювати URL

4. **Оновити Spotify Redirect URI:**
   - Spotify Dashboard → Edit Settings
   - Додати: `https://your-railway-domain.up.railway.app/auth/spotify/callback`
   - Оновити `SPOTIFY_REDIRECT_URI` в Railway

5. **Перевірити деплой:**
   - Health check: `https://your-railway-domain.up.railway.app/health`
   - API docs: `https://your-railway-domain.up.railway.app/docs`

### Крок 2: Web Deployment

1. **Створити новий сервіс в Railway:**
   - New Service → Deploy from GitHub repo
   - Root Directory: `apps/web`

2. **Налаштувати змінні оточення:**
   - `VITE_API_URL` = backend Railway URL
   - `VITE_SUPABASE_URL` = Supabase URL
   - `VITE_SUPABASE_ANON_KEY` = Supabase anon key

3. **Перевірити деплой:**
   - Відкрити Railway domain
   - Перевірити що API підключено

### Крок 3: Database Migration

1. **Виконати міграції в Supabase:**
   - SQL Editor → New Query
   - Виконати `DATABASE_MIGRATION_FINAL.sql`
   - Виконати `DATABASE_MIGRATION_ADD_CONVERSATIONS.sql`

2. **Перевірити таблиці:**
   - Table Editor → перевірити що всі таблиці створено

---

## ✅ Post-Deployment Checklist

### Backend
- [ ] Health endpoint: `/health` працює
- [ ] API docs: `/docs` доступні
- [ ] Chat endpoint: `/api/v1/chat/message` працює
- [ ] Playlist generation: `/api/v1/playlists/generate` працює
- [ ] Spotify OAuth: `/auth/spotify/callback` працює
- [ ] Database connection успішна

### Web
- [ ] App завантажується
- [ ] API connection працює
- [ ] Chat interface працює
- [ ] Playlist generation працює
- [ ] Spotify OAuth flow працює

### Integration
- [ ] CORS налаштовано правильно
- [ ] Spotify redirect URIs налаштовано
- [ ] Всі сервіси комунікують
- [ ] Error handling працює

---

## 📊 Статус готовності

| Компонент | Статус | Готовність |
|-----------|--------|------------|
| Backend | ✅ | 100% |
| Frontend Web | ✅ | 100% |
| Database | ✅ | 100% |
| Documentation | ✅ | 100% |
| Configuration | ✅ | 100% |

**Загальна готовність: 100%** ✅

---

## 🎯 Висновок

**Проект готовий до деплою!** ✅

Всі необхідні компоненти реалізовано, протестовано та документовано. Потрібно лише:
1. Налаштувати environment variables в Railway
2. Виконати міграції бази даних
3. Оновити Spotify redirect URIs
4. Задеплоїти backend та web

**Детальні інструкції:** Див. [docs/DEPLOYMENT.md](./DEPLOYMENT.md)

