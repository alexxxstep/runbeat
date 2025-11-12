# 🔄 Оновлення SPOTIFY_REDIRECT_URI на Production URL

## Крок 1: Отримайте Railway URL

1. **Відкрийте Railway Dashboard**
   - https://railway.app → ваш проект `runbeat`

2. **Перейдіть в Settings**
   - Натисніть ⚙️ (Settings) в лівому меню

3. **Знайдіть Domains**
   - Прокрутіть до секції **"Domains"**
   - Знайдіть **"Default Domain"**

4. **Скопіюйте Railway URL**
   - Приклад: `runbeat-production.up.railway.app`
   - Або: `runbeat-production-1234.up.railway.app`

---

## Крок 2: Оновіть SPOTIFY_REDIRECT_URI в Railway

### Варіант A: Через Variables UI

1. **Відкрийте Variables**
   - Railway Dashboard → ваш проект → **Variables**

2. **Знайдіть SPOTIFY_REDIRECT_URI**
   - Знайдіть рядок з `SPOTIFY_REDIRECT_URI`
   - Натисніть на іконку редагування (✏️) або клікніть на значення

3. **Оновіть значення**
   - Старе: `http://localhost:8000/auth/spotify/callback`
   - Нове: `https://ваш-проект.railway.app/auth/spotify/callback`
   - **ВАЖЛИВО:** Використовуйте `https://` (не `http://`)

4. **Збережіть**
   - Натисніть **"Save"** або **"Update"**
   - Railway автоматично перезапустить deployment

### Варіант B: Через Raw Editor

1. **Відкрийте Raw Editor**
   - Variables → кнопка **"Raw Editor"** (`{}`)

2. **Знайдіть рядок**
   ```
   SPOTIFY_REDIRECT_URI=http://localhost:8000/auth/spotify/callback
   ```

3. **Замініть на**
   ```
   SPOTIFY_REDIRECT_URI=https://ваш-проект.railway.app/auth/spotify/callback
   ```

4. **Збережіть**
   - Натисніть **"Save"** або **"Apply"**

---

## Крок 3: Додайте Production URL в Spotify Dashboard

**Це обов'язково!** Spotify перевіряє Redirect URI перед авторизацією.

1. **Відкрийте Spotify Developer Dashboard**
   - https://developer.spotify.com/dashboard
   - Увійдіть в ваш акаунт

2. **Відкрийте ваш додаток**
   - Знайдіть додаток `RunBeat` (або вашу назву)
   - Натисніть на нього

3. **Відкрийте Settings**
   - Натисніть **"Edit Settings"**

4. **Додайте Redirect URI**
   - Прокрутіть до секції **"Redirect URIs"**
   - Натисніть **"Add"** або **"+"**
   - Введіть: `https://ваш-проект.railway.app/auth/spotify/callback`
   - Натисніть **"Add"**

5. **Збережіть**
   - Натисніть **"Save"** внизу сторінки

### Примітка про кілька Redirect URIs

Spotify дозволяє додати кілька Redirect URIs. Можна залишити обидва:
- `http://localhost:8000/auth/spotify/callback` (для локальної розробки)
- `https://ваш-проект.railway.app/auth/spotify/callback` (для production)

---

## Крок 4: Перевірка

### 1. Перевірте Railway Variables

```bash
# В Railway Dashboard → Variables
# Переконайтесь що:
SPOTIFY_REDIRECT_URI=https://ваш-проект.railway.app/auth/spotify/callback
```

### 2. Перевірте Spotify Dashboard

```bash
# В Spotify Dashboard → ваш додаток → Edit Settings
# Переконайтесь що в Redirect URIs є:
https://ваш-проект.railway.app/auth/spotify/callback
```

### 3. Перевірте Health Endpoint

```bash
curl https://ваш-проект.railway.app/health
```

Очікуваний результат:
```json
{"status":"healthy","timestamp":"...","service":"runbeat-api"}
```

### 4. Тест Spotify OAuth (коли буде реалізовано)

Після реалізації Spotify OAuth endpoint, перевірте що redirect працює:
- Відкрийте: `https://ваш-проект.railway.app/auth/spotify`
- Має перенаправити на Spotify для авторизації
- Після авторизації має повернути на ваш callback URL

---

## ✅ Чеклист

- [ ] Отримано Railway URL (Settings → Domains)
- [ ] Оновлено `SPOTIFY_REDIRECT_URI` в Railway Variables
- [ ] Додано production URL в Spotify Dashboard (Redirect URIs)
- [ ] Збережено зміни в обох місцях
- [ ] Перевірено Health endpoint
- [ ] Railway deployment перезапущений

---

## 🐛 Troubleshooting

### Проблема: OAuth не працює після оновлення

**Рішення:**
1. Перевірте що URL точно відповідає в обох місцях:
   - Railway Variables
   - Spotify Dashboard
2. Переконайтесь що URL починається з `https://` (не `http://`)
3. Перевірте що немає trailing slash: `/callback` (не `/callback/`)
4. Перезапустіть deployment в Railway

### Проблема: "Invalid redirect URI" в Spotify

**Рішення:**
1. Перевірте що URL точно скопійований з Railway
2. Переконайтесь що URL додано в Spotify Dashboard
3. Перевірте що натиснули "Save" в Spotify Dashboard
4. Зачекайте 1-2 хвилини (Spotify може кешувати)

---

## 📝 Приклад повного URL

Якщо ваш Railway Domain: `runbeat-production.up.railway.app`

То `SPOTIFY_REDIRECT_URI` має бути:
```
https://runbeat-production.up.railway.app/auth/spotify/callback
```

**Формат:**
- `https://` - обов'язково HTTPS
- `ваш-проект.railway.app` - ваш Railway Domain
- `/auth/spotify/callback` - шлях до callback endpoint

---

**Готово!** Після оновлення SPOTIFY_REDIRECT_URI ваш Spotify OAuth буде працювати на production! 🎉

