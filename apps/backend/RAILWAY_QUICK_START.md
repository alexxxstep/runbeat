# 🚂 Railway Quick Start - Швидкий старт

## ⚡ Швидкий чеклист деплою

### 1️⃣ Підготовка GitHub репозиторію

```bash
cd apps/backend
git init
git add .
git commit -m "feat: initial backend setup"
git remote add origin https://github.com/ваш-username/runbeat-backend.git
git push -u origin main
```

### 2️⃣ Створення Railway проекту

1. Перейдіть на https://railway.app
2. **"New Project"** → **"Deploy from GitHub repo"**
3. Оберіть ваш репозиторій `runbeat-backend`
4. Railway автоматично визначить Python проект

### 3️⃣ Налаштування Environment Variables

В Railway Dashboard → ваш проект → **"Variables"** додайте:

```env
# Supabase
SUPABASE_URL=https://ваш-проект.supabase.co
SUPABASE_ANON_KEY=ваш_anon_key
SUPABASE_SERVICE_KEY=ваш_service_key

# Spotify
SPOTIFY_CLIENT_ID=ваш_client_id
SPOTIFY_CLIENT_SECRET=ваш_client_secret
# SPOTIFY_REDIRECT_URI - буде встановлено автоматично після отримання Railway URL

# OpenAI
OPENAI_API_KEY=sk-proj-ваш_ключ
OPENAI_MODEL=gpt-4

# App Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=["https://ваш-web-app.vercel.app"]
```

### 4️⃣ Отримання Railway URL

1. Railway Dashboard → Settings → **"Domains"**
2. Скопіюйте **"Default Domain"** (наприклад: `runbeat-backend-production.up.railway.app`)

### 5️⃣ Оновлення Spotify Redirect URI

**В Spotify Dashboard:**
1. https://developer.spotify.com/dashboard → ваш додаток
2. **"Edit Settings"** → **"Redirect URIs"**
3. Додайте: `https://ваш-проект.railway.app/auth/spotify/callback`
4. **"Save"**

**В Railway Variables:**
1. Додайте або оновіть:
   ```
   SPOTIFY_REDIRECT_URI=https://ваш-проект.railway.app/auth/spotify/callback
   ```
2. Railway автоматично перезапустить сервіс

### 6️⃣ Перевірка деплою

```bash
# Health check
curl https://ваш-проект.railway.app/health

# Очікуваний відповідь:
# {"status":"healthy","timestamp":"2025-01-15T10:30:00","service":"runbeat-api"}
```

---

## 📝 Важливі моменти

✅ **Railway автоматично:**
- Визначає Python проект
- Встановлює залежності з `requirements.txt`
- Запускає через `Procfile` або `railway.json`
- Встановлює `PORT` змінну автоматично

✅ **SPOTIFY_REDIRECT_URI:**
- Може бути встановлено автоматично через `RAILWAY_PUBLIC_DOMAIN`
- Або встановіть вручну в Railway Variables
- **Обов'язково** додайте той самий URL в Spotify Dashboard

✅ **Файли для Railway:**
- `Procfile` - команда запуску
- `railway.json` - конфігурація деплою (опціонально)
- `runtime.txt` - версія Python (опціонально)

---

## 🔍 Troubleshooting

**Проблема:** Deployment fails
**Рішення:** Перевірте логи в Railway Dashboard → Deployments → View Logs

**Проблема:** Health check не працює
**Рішення:** Перевірте що всі env variables встановлені правильно

**Проблема:** Spotify OAuth не працює
**Рішення:** Переконайтесь що `SPOTIFY_REDIRECT_URI` точно відповідає URL в Spotify Dashboard (з `https://`)

---

## 📚 Детальна інструкція

Дивіться [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) для повної інструкції з усіма деталями.

---

**Готово!** 🎉 Ваш Backend задеплоєний на Railway!

