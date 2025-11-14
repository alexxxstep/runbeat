# 📝 Покрокова інструкція по заповненню .env файлу

## Крок 1: Створення .env файлу

```bash
cd apps/backend
cp .env.example .env
```

---

## Крок 2: Supabase (1/4) 🔵

### 2.1. Створення проекту Supabase

1. Перейдіть на https://supabase.com
2. Натисніть **"Start your project"** або **"Sign Up"**
3. Увійдіть через GitHub або створіть акаунт
4. Натисніть **"New Project"**
5. Заповніть форму:
   - **Name**: `runbeat` (або будь-яка назва)
   - **Database Password**: Створіть надійний пароль (збережіть його!)
   - **Region**: Оберіть найближчий регіон
   - **Pricing Plan**: Free (для MVP достатньо)
6. Натисніть **"Create new project"**
7. Дочекайтесь створення проекту (~2 хвилини)

### 2.2. Отримання ключів Supabase

1. В проекті Supabase перейдіть в **Settings** (⚙️ іконка зліва)
2. Відкрийте **API** секцію
3. Знайдіть секцію **Project API keys**

**SUPABASE_URL:**
```
Скопіюйте "Project URL" з секції "Project Settings"
Приклад: https://abcdefghijklmnop.supabase.co
```

**SUPABASE_ANON_KEY:**
```
Скопіюйте "anon public" ключ (використовується на frontend)
Приклад: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYxNjIzOTAyMiwiZXhwIjoxOTMxODE1MDIyfQ.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**SUPABASE_SERVICE_KEY:**
```
Скопіюйте "service_role secret" ключ (ТІЛЬКИ для backend!)
⚠️ УВАГА: Цей ключ обходить RLS - ніколи не використовуйте на frontend!
Приклад: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNjE2MjM5MDIyLCJleHAiOjE5MzE4MTUwMjJ9.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2.3. Заповнення в .env

```env
SUPABASE_URL=https://ваш-проект.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Крок 3: Spotify OAuth (2/4) 🟢

### 3.1. Створення Spotify App

1. Перейдіть на https://developer.spotify.com/dashboard
2. Увійдіть через Spotify акаунт (потрібен Spotify Premium для створення плейлистів)
3. Натисніть **"Create app"**
4. Заповніть форму:
   - **App name**: `RunBeat` (або будь-яка назва)
   - **App description**: `AI music assistant for runners`
   - **Redirect URI**: `http://localhost:8000/auth/spotify/callback`
   - **Which API/SDKs are you planning to use?**: Оберіть "Web API"
5. Поставте галочку на **"I understand and agree..."**
6. Натисніть **"Save"**

### 3.2. Отримання Spotify ключів

1. В Dashboard знайдіть ваш додаток
2. Натисніть на назву додатку
3. На сторінці додатку знайдіть:
   - **Client ID** - скопіюйте його
   - **Client Secret** - натисніть **"View client secret"** та скопіюйте

**SPOTIFY_CLIENT_ID:**
```
Приклад: 1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
```

**SPOTIFY_CLIENT_SECRET:**
```
Приклад: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

### 3.3. Налаштування Redirect URI

1. В Spotify Dashboard перейдіть в **"Edit Settings"**
2. В секції **"Redirect URIs"** додайте:
   ```
   http://localhost:8000/auth/spotify/callback
   ```
3. Натисніть **"Add"** та **"Save"**

### 3.4. Заповнення в .env

**Для локальної розробки:**
```env
SPOTIFY_CLIENT_ID=ваш_client_id
SPOTIFY_CLIENT_SECRET=ваш_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8000/auth/spotify/callback
```

**Для production (Railway):**
```env
SPOTIFY_CLIENT_ID=ваш_client_id
SPOTIFY_CLIENT_SECRET=ваш_client_secret
SPOTIFY_REDIRECT_URI=https://ваш-проект.railway.app/auth/spotify/callback
```

**⚠️ Важливо:** Після деплою на Railway:
1. Отримайте Railway URL (Settings → Domains)
2. Додайте production URL в Spotify Dashboard (Edit Settings → Redirect URIs)
3. Оновіть `SPOTIFY_REDIRECT_URI` в Railway Variables

Дивіться [RAILWAY_QUICK_START.md](./RAILWAY_QUICK_START.md) для деталей.

---

## Крок 4: OpenAI API (3/4) 🤖

### 4.1. Створення OpenAI акаунту

1. Перейдіть на https://platform.openai.com
2. Натисніть **"Sign Up"** або **"Log In"**
3. Увійдіть або створіть акаунт
4. Підтвердіть email та телефон (для безпеки)

### 4.2. Отримання API ключа

1. Перейдіть на https://platform.openai.com/api-keys
2. Натисніть **"Create new secret key"**
3. Дайте назву ключу: `RunBeat Development`
4. Натисніть **"Create secret key"**
5. ⚠️ **ВАЖЛИВО**: Скопіюйте ключ одразу! Він показується тільки один раз!
   Якщо втратили - видаліть старий та створіть новий

**OPENAI_API_KEY:**
```
Приклад: sk-proj-abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ
```

### 4.3. Перевірка балансу

1. Перейдіть на https://platform.openai.com/account/billing
2. Переконайтесь що є кредити (можна додати через "Add payment method")
3. Для тестування достатньо $5-10

### 4.4. Заповнення в .env

```env
OPENAI_API_KEY=sk-proj-ваш_ключ
OPENAI_MODEL=gpt-4

# Optional: Different models for different agents (falls back to OPENAI_MODEL if not set)
# OPENAI_MODEL_PARSER=gpt-4
# OPENAI_MODEL_CURATOR=gpt-4-turbo-preview
# OPENAI_MODEL_CONVERSATION=gpt-3.5-turbo
# OPENAI_MODEL_SUPERVISOR=gpt-4
```

**Примітка:** `gpt-4` - це модель за замовчуванням для всіх агентів. Можна використовувати:
- `gpt-4` - найкраща якість (дорожче)
- `gpt-4-turbo-preview` - швидше та дешевше
- `gpt-3.5-turbo` - найдешевше (для тестування)

**Опціонально:** Можна встановити різні моделі для різних агентів:
- `OPENAI_MODEL_PARSER` - для WorkoutParserAgent (парсинг воркаутів)
- `OPENAI_MODEL_CURATOR` - для MusicCuratorAgent (генерація плейлистів)
- `OPENAI_MODEL_CONVERSATION` - для ConversationAgent (розмова)
- `OPENAI_MODEL_SUPERVISOR` - для ConversationOrchestrator (координація)

---

## Крок 5: App Settings (4/4) ⚙️

### 5.1. Заповнення базових налаштувань

Ці параметри не потребують зовнішніх сервісів - просто заповніть:

```env
# Режим роботи (development для розробки, production для продакшену)
ENVIRONMENT=development

# Рівень логування (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# CORS дозволені домени (для frontend)
# Додайте URL вашого frontend додатку
CORS_ORIGINS=["http://localhost:3000","http://localhost:19006"]
```

**Пояснення:**
- `ENVIRONMENT=development` - для розробки (показує `/docs`)
- `LOG_LEVEL=INFO` - стандартний рівень логування
- `CORS_ORIGINS` - список URL з яких можна робити запити:
  - `http://localhost:3000` - React Web app
  - `http://localhost:19006` - Expo Mobile app

---

## ✅ Перевірка правильності заповнення

### Приклад повного .env файлу:

```env
# Supabase
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYxNjIzOTAyMiwiZXhwIjoxOTMxODE1MDIyfQ.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNjE2MjM5MDIyLCJleHAiOjE5MzE4MTUwMjJ9.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Spotify OAuth
SPOTIFY_CLIENT_ID=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
SPOTIFY_CLIENT_SECRET=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
SPOTIFY_REDIRECT_URI=http://localhost:8000/auth/spotify/callback

# OpenAI
OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ
OPENAI_MODEL=gpt-4

# App Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000","http://localhost:19006"]
```

### Чеклист перевірки:

- [ ] Всі значення заповнені (немає `your_...` або `test_...`)
- [ ] `SUPABASE_URL` починається з `https://` та закінчується на `.supabase.co`
- [ ] `SUPABASE_ANON_KEY` та `SUPABASE_SERVICE_KEY` - це довгі JWT токени
- [ ] `SPOTIFY_CLIENT_ID` та `SPOTIFY_CLIENT_SECRET` - це рядки з букв та цифр
- [ ] `OPENAI_API_KEY` починається з `sk-proj-` або `sk-`
- [ ] `CORS_ORIGINS` - це JSON масив з лапками

---

## 🚀 Тестування після заповнення

```bash
cd apps/backend

# Перевірка що .env файл читається
python -c "from app.core.config import settings; print('✅ Config loaded:', settings.ENVIRONMENT)"

# Запуск сервера
uvicorn app.main:app --reload

# В іншому терміналі - перевірка health endpoint
curl http://localhost:8000/health
```

---

## ❓ Часті питання

**Q: Чи можна використовувати тестові значення?**
A: Ні, для роботи потрібні реальні ключі. Але для тестування health endpoints можна тимчасово використати будь-які значення.

**Q: Якщо немає Spotify Premium?**
A: Spotify API дозволяє отримувати рекомендації без Premium, але для створення плейлистів потрібен Premium акаунт.

**Q: Скільки коштує OpenAI API?**
A: GPT-4 коштує ~$0.03 за 1K токенів (вхідні) та ~$0.06 за 1K токенів (вихідні). Для тестування достатньо $5-10.

**Q: Чи безпечно зберігати ключі в .env?**
A: Так, `.env` файл вже додано в `.gitignore` і не буде закомічений в git. Ніколи не публікуйте `.env` файл!

**Q: Як налаштувати SPOTIFY_REDIRECT_URI для Railway?**
A: Після деплою на Railway:
1. Отримайте Railway URL (Railway Dashboard → Settings → Domains)
2. Додайте production URL в Spotify Dashboard (Edit Settings → Redirect URIs)
3. Встановіть `SPOTIFY_REDIRECT_URI` в Railway Variables
Дивіться [RAILWAY_QUICK_START.md](./RAILWAY_QUICK_START.md) для деталей.

**Q: Чи можна використовувати один Spotify App для development та production?**
A: Так, Spotify дозволяє додати кілька Redirect URIs в одному додатку. Просто додайте обидва:
- `http://localhost:8000/auth/spotify/callback` (для локальної розробки)
- `https://ваш-проект.railway.app/auth/spotify/callback` (для production)

---

## 📚 Корисні посилання

- [Supabase Dashboard](https://supabase.com/dashboard)
- [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- [OpenAI Platform](https://platform.openai.com)
- [Supabase API Keys Docs](https://supabase.com/docs/guides/api/api-keys)
- [Spotify Web API Guide](https://developer.spotify.com/documentation/web-api)

---

**Готово!** Після заповнення всіх параметрів можна запускати Backend сервер. 🎉

