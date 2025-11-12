# Виправлення помилки "INVALID_CLIENT: Invalid redirect URI"

## Проблема

При спробі авторизації через Spotify виникає помилка:

```
INVALID_CLIENT: Invalid redirect URI
GET https://accounts.spotify.com/authorize?...redirect_uri=https%3A%2F%2Frunbeatbackend-production.up.railway.app%2Fauth%2Fspotify%2Fcallback... 400 (Bad Request)
```

**Причина:** Redirect URI не зареєстрований в Spotify Dashboard.

---

## ✅ Рішення: Додати Redirect URI в Spotify Dashboard

### Крок 1: Відкрийте Spotify Developer Dashboard

1. Перейдіть на [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Увійдіть в свій Spotify акаунт
3. Знайдіть ваш додаток **RunBeat** (або назву вашого додатку)
4. Натисніть на назву додатку

### Крок 2: Додайте Redirect URI

1. На сторінці додатку натисніть **"Edit Settings"** (або кнопку з іконкою ⚙️)
2. Прокрутіть до секції **"Redirect URIs"**
3. В поле **"Redirect URIs"** додайте:

   ```
   https://runbeatbackend-production.up.railway.app/auth/spotify/callback
   ```

   ⚠️ **ВАЖЛИВО:** Скопіюйте точно цей URL, включаючи `https://` та `/auth/spotify/callback`

4. Натисніть **"Add"** (якщо є кнопка) або просто введіть та збережіть
5. Натисніть **"Save"** внизу сторінки

### Крок 3: Перевірте Railway Variables

Переконайтеся, що в Railway Variables встановлено правильний `SPOTIFY_REDIRECT_URI`:

1. Відкрийте [Railway Dashboard](https://railway.app)
2. Виберіть ваш проект → Backend service
3. Перейдіть в **Variables**
4. Знайдіть `SPOTIFY_REDIRECT_URI`
5. Переконайтеся, що значення:
   ```
   https://runbeatbackend-production.up.railway.app/auth/spotify/callback
   ```
6. Якщо значення неправильне або відсутнє:
   - Натисніть **"New Variable"** (якщо відсутнє)
   - **Key:** `SPOTIFY_REDIRECT_URI`
   - **Value:** `https://runbeatbackend-production.up.railway.app/auth/spotify/callback`
   - Натисніть **"Add"**

### Крок 4: Перезапустіть Backend

Після зміни змінних Railway автоматично перезапустить сервіс. Якщо ні:

1. В Railway Dashboard → ваш Backend service
2. Натисніть **"Redeploy"** або **"Restart"**

---

## 🔍 Перевірка

### Перевірка 1: Spotify Dashboard

В Spotify Dashboard → ваш додаток → Edit Settings → Redirect URIs має бути:

```
https://runbeatbackend-production.up.railway.app/auth/spotify/callback
```

### Перевірка 2: Railway Variables

В Railway Dashboard → Variables має бути:

```
SPOTIFY_REDIRECT_URI=https://runbeatbackend-production.up.railway.app/auth/spotify/callback
```

### Перевірка 3: Тестування

1. Відкрийте ваш Web App
2. Перейдіть на `/login`
3. Натисніть "Увійти через Spotify"
4. Має відкритися Spotify OAuth сторінка (без помилки 400)

---

## 📝 Додаткові Redirect URIs

Якщо ви хочете використовувати один Spotify App для development та production, додайте обидва URI:

**В Spotify Dashboard → Redirect URIs:**

```
http://localhost:8000/auth/spotify/callback
https://runbeatbackend-production.up.railway.app/auth/spotify/callback
```

---

## ⚠️ Важливі примітки

1. **URL має точно відповідати:**

   - ✅ `https://runbeatbackend-production.up.railway.app/auth/spotify/callback`
   - ❌ `https://runbeatbackend-production.up.railway.app/auth/spotify/callback/` (зайвий слеш)
   - ❌ `http://runbeatbackend-production.up.railway.app/auth/spotify/callback` (http замість https)

2. **Після зміни в Spotify Dashboard:**

   - Зміни застосовуються миттєво
   - Не потрібно перезапускати backend

3. **Якщо Railway URL змінився:**
   - Оновіть Redirect URI в Spotify Dashboard
   - Оновіть `SPOTIFY_REDIRECT_URI` в Railway Variables

---

## 🐛 Якщо проблема залишається

1. **Перевірте, що URI точно відповідає:**

   - Скопіюйте URI з помилки (декодуйте URL encoding)
   - Порівняйте з URI в Spotify Dashboard
   - Мають бути ідентичними

2. **Перевірте Client ID:**

   - В помилці показано `client_id=c56683db635749b180ad62e5c3814a82`
   - Переконайтеся, що це правильний Client ID з Spotify Dashboard

3. **Очистіть кеш браузера** та спробуйте знову

4. **Перевірте логи Railway:**
   - Railway Dashboard → ваш Backend → Logs
   - Шукайте помилки про `SPOTIFY_REDIRECT_URI`

---

## 📚 Корисні посилання

- [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- [Spotify OAuth Guide](https://developer.spotify.com/documentation/web-api/tutorials/code-flow)
- [Railway Dashboard](https://railway.app)
