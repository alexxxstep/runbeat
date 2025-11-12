# 🔐 Додавання Environment Variables в Railway

## Спосіб 1: Raw Editor (Найшвидший для багатьох змінних) ⚡

### Крок 1: Відкрийте Raw Editor

1. В Railway Dashboard → ваш проект → **Variables**
2. Натисніть кнопку **"Raw Editor"** (іконка з `{}`)

### Крок 2: Скопіюйте змінні з .env

Відкрийте ваш `.env` файл та скопіюйте всі змінні (без коментарів `#`):

```env
SUPABASE_URL=https://ваш-проект.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SPOTIFY_CLIENT_ID=ваш_client_id
SPOTIFY_CLIENT_SECRET=ваш_client_secret
SPOTIFY_REDIRECT_URI=https://ваш-проект.railway.app/auth/spotify/callback
OPENAI_API_KEY=sk-proj-ваш_ключ
OPENAI_MODEL=gpt-4
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=["https://ваш-web-app.vercel.app"]
```

### Крок 3: Вставте в Raw Editor

1. В Raw Editor вставте скопійовані змінні
2. **Формат:** `KEY=value` (по одній змінній на рядок)
3. Натисніть **"Save"** або **"Apply"**

### Крок 4: Перевірка

Після збереження змінні з'являться в списку Variables.

---

## Спосіб 2: Додавання по одній змінній (New Variable)

### Покрокова інструкція:

1. **Відкрийте Variables**
   - Railway Dashboard → ваш проект → **Variables**

2. **Натисніть "New Variable"**
   - Кнопка з `+` та текстом "New Variable"

3. **Заповніть форму:**
   - **Key:** `SUPABASE_URL`
   - **Value:** `https://ваш-проект.supabase.co`
   - Натисніть **"Add"** або **"Save"**

4. **Повторіть для кожної змінної**

### Приклад заповнення:

| Key | Value |
|-----|-------|
| `SUPABASE_URL` | `https://ваш-проект.supabase.co` |
| `SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `SUPABASE_SERVICE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `SPOTIFY_CLIENT_ID` | `ваш_client_id` |
| `SPOTIFY_CLIENT_SECRET` | `ваш_client_secret` |
| `SPOTIFY_REDIRECT_URI` | `https://ваш-проект.railway.app/auth/spotify/callback` |
| `OPENAI_API_KEY` | `sk-proj-ваш_ключ` |
| `OPENAI_MODEL` | `gpt-4` |
| `ENVIRONMENT` | `production` |
| `LOG_LEVEL` | `INFO` |
| `CORS_ORIGINS` | `["https://ваш-web-app.vercel.app"]` |

---

## Спосіб 3: Railway CLI (Для автоматизації)

### Встановлення Railway CLI:

```bash
# Windows (PowerShell)
iwr https://railway.app/install.ps1 | iex

# macOS/Linux
curl -fsSL https://railway.app/install.sh | sh
```

### Логін:

```bash
railway login
```

### Додавання змінних з .env файлу:

```bash
# Перейдіть в директорію з .env файлом
cd apps/backend

# Додайте всі змінні з .env
railway variables set $(cat .env | grep -v '^#' | xargs)
```

Або по одній:

```bash
railway variables set SUPABASE_URL=https://ваш-проект.supabase.co
railway variables set SUPABASE_ANON_KEY=ваш_ключ
# ... і так далі
```

---

## 📋 Повний список змінних для Railway

### Supabase (1-3):
```env
SUPABASE_URL=https://ваш-проект.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Spotify (4-6):
```env
SPOTIFY_CLIENT_ID=ваш_client_id
SPOTIFY_CLIENT_SECRET=ваш_client_secret
SPOTIFY_REDIRECT_URI=https://ваш-проект.railway.app/auth/spotify/callback
```

**⚠️ Важливо:** `SPOTIFY_REDIRECT_URI` має бути production URL з Railway!
- Отримайте Railway URL: Settings → Domains → Default Domain
- Формат: `https://ваш-проект.railway.app/auth/spotify/callback`

### OpenAI (7-8):
```env
OPENAI_API_KEY=sk-proj-ваш_ключ
OPENAI_MODEL=gpt-4
```

### App Settings (9-11):
```env
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=["https://ваш-web-app.vercel.app"]
```

---

## ✅ Перевірка після додавання

1. **Перевірте що всі змінні додані:**
   - Railway Dashboard → Variables
   - Повинно бути 11 змінних (або більше якщо додали додаткові)

2. **Перевірте формат:**
   - Ключі мають бути в UPPER_CASE
   - Значення без лапок (якщо не JSON масив)

3. **Перезапустіть deployment:**
   - Railway автоматично перезапустить після додавання змінних
   - Або вручну: Deployments → Redeploy

---

## 🔒 Безпека

- ✅ Railway автоматично шифрує змінні
- ✅ Змінні не відображаються в логах
- ✅ Доступ тільки для вас та вашої команди
- ❌ Ніколи не комітьте `.env` файл в git

---

## 🐛 Troubleshooting

### Проблема: Змінні не застосовуються

**Рішення:**
1. Перевірте що змінні збережені (натисніть Save)
2. Перезапустіть deployment вручну
3. Перевірте логи на помилки

### Проблема: SPOTIFY_REDIRECT_URI не працює

**Рішення:**
1. Перевірте що URL точно відповідає Railway Domain
2. Переконайтесь що URL починається з `https://`
3. Перевірте що URL додано в Spotify Dashboard

### Проблема: CORS_ORIGINS не працює

**Рішення:**
1. Перевірте формат: `["https://domain.com"]` (JSON масив)
2. Переконайтесь що немає пробілів після ком
3. Використовуйте подвійні лапки для JSON

---

## 💡 Поради

1. **Використовуйте Raw Editor** для швидкого додавання багатьох змінних
2. **Скопіюйте з .env** та видаліть коментарі перед вставкою
3. **Перевірте Railway URL** перед додаванням SPOTIFY_REDIRECT_URI
4. **Зберігайте backup** вашого .env файлу в безпечному місці

---

**Готово!** Після додавання всіх змінних ваш Backend буде готовий до роботи! 🎉

