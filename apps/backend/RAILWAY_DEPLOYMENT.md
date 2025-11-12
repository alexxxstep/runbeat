# 🚂 Railway Deployment Guide - RunBeat Backend

## 📋 Огляд

Цей гайд покроково пояснює як задеплоїти RunBeat Backend на Railway через GitHub.

**Важливо:** Після деплою на Railway потрібно оновити `SPOTIFY_REDIRECT_URI` в Spotify Dashboard на production URL.

---

## Крок 1: Підготовка репозиторію GitHub

### 1.1. Створення репозиторію

1. Перейдіть на https://github.com/new
2. Створіть новий репозиторій:
   - **Repository name**: `runbeat-backend` (або будь-яка назва)
   - **Visibility**: Private (рекомендовано для production)
   - **Initialize**: НЕ ставити галочки (репо вже існує)
3. Натисніть **"Create repository"**

### 1.2. Підключення локального репозиторію

```bash
cd apps/backend

# Ініціалізація git (якщо ще не зроблено)
git init

# Додавання remote
git remote add origin https://github.com/ваш-username/runbeat-backend.git

# Створення .gitignore (якщо ще немає)
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.env
.env.local
*.log
logs/
.venv/
venv/
EOF

# Коміт та push
git add .
git commit -m "feat: initial backend setup"
git branch -M main
git push -u origin main
```

---

## Крок 2: Створення Railway проекту

### 2.1. Реєстрація на Railway

1. Перейдіть на https://railway.app
2. Натисніть **"Start a New Project"**
3. Увійдіть через GitHub (рекомендовано)
4. Дозвольте Railway доступ до GitHub репозиторіїв

### 2.2. Створення нового проекту

1. Натисніть **"New Project"**
2. Оберіть **"Deploy from GitHub repo"**
3. Знайдіть ваш репозиторій `runbeat-backend`
4. Натисніть на нього
5. Railway автоматично визначить Python проект

### 2.3. Налаштування деплою

Railway автоматично:
- Визначить що це Python проект
- Знайде `requirements.txt`
- Налаштує деплой

**Якщо потрібно вказати команду запуску:**
- В Railway Dashboard → ваш проект → Settings
- Знайдіть **"Start Command"**
- Встановіть: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## Крок 3: Налаштування Environment Variables

### 3.1. Додавання змінних оточення

1. В Railway Dashboard → ваш проект
2. Відкрийте вкладку **"Variables"**
3. Додайте всі змінні з `.env` файлу:

**Supabase:**
```
SUPABASE_URL=https://ваш-проект.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Spotify:**
```
SPOTIFY_CLIENT_ID=ваш_client_id
SPOTIFY_CLIENT_SECRET=ваш_client_secret
SPOTIFY_REDIRECT_URI=https://ваш-проект.railway.app/auth/spotify/callback
```

**OpenAI:**
```
OPENAI_API_KEY=sk-proj-ваш_ключ
OPENAI_MODEL=gpt-4
```

**App Settings:**
```
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=["https://ваш-web-app.vercel.app","https://ваш-mobile-app.expo.dev"]
```

### 3.2. Отримання Railway URL

1. В Railway Dashboard → ваш проект
2. Відкрийте вкладку **"Settings"**
3. Знайдіть секцію **"Domains"**
4. Скопіюйте **"Default Domain"** (наприклад: `runbeat-backend-production.up.railway.app`)
5. Це ваш production URL!

---

## Крок 4: Оновлення Spotify Redirect URI

### 4.1. Додавання production URL в Spotify

1. Перейдіть на https://developer.spotify.com/dashboard
2. Відкрийте ваш додаток RunBeat
3. Натисніть **"Edit Settings"**
4. В секції **"Redirect URIs"** додайте:
   ```
   https://ваш-проект.railway.app/auth/spotify/callback
   ```
   (замініть на ваш Railway URL)
5. Натисніть **"Add"** та **"Save"**

### 4.2. Оновлення SPOTIFY_REDIRECT_URI в Railway

1. В Railway Dashboard → Variables
2. Знайдіть `SPOTIFY_REDIRECT_URI`
3. Оновіть на:
   ```
   https://ваш-проект.railway.app/auth/spotify/callback
   ```
4. Railway автоматично перезапустить сервіс

---

## Крок 5: Створення необхідних файлів для Railway

### 5.1. railway.json (опціонально)

Створіть файл `apps/backend/railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 5.2. Procfile (альтернатива)

Створіть файл `apps/backend/Procfile`:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 5.3. runtime.txt (опціонально)

Якщо потрібна конкретна версія Python, створіть `apps/backend/runtime.txt`:

```
python-3.11.0
```

---

## Крок 6: Перевірка деплою

### 6.1. Перевірка логів

1. В Railway Dashboard → ваш проект
2. Відкрийте вкладку **"Deployments"**
3. Натисніть на останній deployment
4. Перевірте логи на помилки

### 6.2. Тестування endpoints

```bash
# Health check
curl https://ваш-проект.railway.app/health

# Очікуваний відповідь:
# {"status":"healthy","timestamp":"2025-01-15T10:30:00","service":"runbeat-api"}
```

### 6.3. Перевірка документації

Відкрийте в браузері:
```
https://ваш-проект.railway.app/docs
```

**Примітка:** В production режимі (`ENVIRONMENT=production`) `/docs` може бути вимкнено для безпеки.

---

## Крок 7: Налаштування Custom Domain (опціонально)

### 7.1. Додавання домену

1. В Railway Dashboard → Settings → Domains
2. Натисніть **"Custom Domain"**
3. Введіть ваш домен (наприклад: `api.runbeat.com`)
4. Додайте CNAME запис в DNS:
   ```
   Type: CNAME
   Name: api (або @)
   Value: ваш-проект.railway.app
   ```

### 7.3. Оновлення Spotify Redirect URI

Після налаштування custom domain оновіть:
```
SPOTIFY_REDIRECT_URI=https://api.runbeat.com/auth/spotify/callback
```

---

## Крок 8: Налаштування автоматичного деплою

### 8.1. Railway автоматично деплоїть при push

Railway за замовчуванням:
- Автоматично деплоїть при push в `main` branch
- Створює preview deployments для pull requests (якщо увімкнено)

### 8.2. Налаштування GitHub Actions (опціонально)

Якщо потрібен більший контроль, створіть `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Railway

on:
  push:
    branches:
      - main
    paths:
      - 'apps/backend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Railway
        uses: bervProject/railway-deploy@v1.0.0
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: backend
```

---

## 🔒 Безпека

### Важливі моменти:

1. **Ніколи не комітьте `.env` файл**
   - Переконайтесь що `.env` в `.gitignore`
   - Використовуйте Railway Variables для production

2. **Service Keys**
   - `SUPABASE_SERVICE_KEY` - обходить RLS, використовуйте тільки на backend
   - Ніколи не використовуйте на frontend

3. **API Keys**
   - Обмежте доступ до Railway Dashboard
   - Використовуйте GitHub Secrets для CI/CD

---

## 📊 Monitoring та Logs

### Перегляд логів:

1. Railway Dashboard → ваш проект → **"Deployments"**
2. Натисніть на deployment → **"View Logs"**
3. Логи оновлюються в реальному часі

### Метрики:

Railway показує:
- CPU використання
- Memory використання
- Network traffic
- Request count

---

## 🐛 Troubleshooting

### Проблема: Deployment fails

**Рішення:**
1. Перевірте логи в Railway Dashboard
2. Переконайтесь що всі env variables встановлені
3. Перевірте що `requirements.txt` коректний
4. Перевірте Python версію в `runtime.txt`

### Проблема: Health check fails

**Рішення:**
1. Перевірте що Supabase ключі правильні
2. Перевірте що `SUPABASE_URL` коректний
3. Перевірте логи для деталей помилки

### Проблема: Spotify OAuth не працює

**Рішення:**
1. Перевірте що `SPOTIFY_REDIRECT_URI` точно відповідає URL в Spotify Dashboard
2. Переконайтесь що URL починається з `https://` (не `http://`)
3. Перевірте що немає trailing slash: `/callback` (не `/callback/`)

---

## ✅ Чеклист деплою

- [ ] Репозиторій створено на GitHub
- [ ] Код закомічено та запушено
- [ ] Railway проект створено
- [ ] GitHub репозиторій підключено до Railway
- [ ] Всі environment variables додані в Railway
- [ ] Railway URL отримано
- [ ] Spotify Redirect URI оновлено на production URL
- [ ] `SPOTIFY_REDIRECT_URI` в Railway оновлено
- [ ] Health check працює (`/health`)
- [ ] Логи перевірені на помилки
- [ ] Custom domain налаштовано (опціонально)

---

## 📚 Корисні посилання

- [Railway Documentation](https://docs.railway.app)
- [Railway Dashboard](https://railway.app/dashboard)
- [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- [Railway Environment Variables](https://docs.railway.app/develop/variables)

---

**Готово!** Ваш Backend тепер задеплоєний на Railway! 🚂✨

