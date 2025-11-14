# Post-Deployment Checklist

**Дата:** 2025-11-14
**Статус:** Web app задеплоївся ✅

---

## ✅ Web App Deployment Status

З логів Railway видно:
- ✅ Container запустився успішно
- ✅ App працює на порту 8080
- ✅ Статичні файли віддаються (JS, CSS, SVG)
- ✅ HTTP запити обробляються (200, 304 статуси)

---

## 🔍 Перевірка після деплою

### 1. Environment Variables

Перевірити що в Railway → Variables додані:

**Web App:**
```env
VITE_API_URL=https://your-backend-railway-domain.up.railway.app
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**⚠️ Важливо:**
- `VITE_API_URL` має вказувати на backend Railway domain
- Якщо змінні додані після build, потрібно перезапустити deployment

---

### 2. Backend API

Перевірити що backend працює:

- [ ] Health check: `https://your-backend-domain.up.railway.app/health`
- [ ] API docs: `https://your-backend-domain.up.railway.app/docs` (якщо ENVIRONMENT=development)
- [ ] Chat endpoint: `https://your-backend-domain.up.railway.app/api/v1/chat/message`

---

### 3. Web App Functionality

Відкрити web app в браузері та перевірити:

#### 3.1. Завантаження
- [ ] App завантажується без помилок
- [ ] Немає помилок в browser console
- [ ] Статичні файли завантажуються

#### 3.2. API Connection
- [ ] Відкрити browser console (F12)
- [ ] Перевірити що `API URL` правильний (якщо DEV mode)
- [ ] Перевірити що немає CORS помилок
- [ ] Перевірити що API запити відправляються на правильний URL

#### 3.3. Chat Interface
- [ ] Відправити тестове повідомлення
- [ ] Перевірити що відповідь приходить
- [ ] Перевірити clarification flow
- [ ] Перевірити генерацію плейлисту

#### 3.4. Spotify Integration
- [ ] Перевірити Spotify OAuth flow
- [ ] Перевірити створення плейлисту в Spotify
- [ ] Перевірити кнопку "Відкрити в Spotify"

---

### 4. Database Connection

Перевірити Supabase:

- [ ] Таблиці створено (users, workouts, playlists, conversations)
- [ ] RLS policies налаштовано
- [ ] Можна вставити тестові дані

---

### 5. Common Issues & Solutions

#### Проблема: API connection fails

**Симптоми:**
- Помилки в console: "Failed to fetch" або "Network error"
- Chat не працює

**Рішення:**
1. Перевірити `VITE_API_URL` в Railway Variables
2. Перевірити що backend працює (health check)
3. Перевірити CORS settings в backend
4. Перевірити що `CORS_ORIGINS` містить web domain

#### Проблема: Environment variables не працюють

**Симптоми:**
- API URL залишається `http://localhost:8000`
- Supabase не підключається

**Рішення:**
1. Перевірити що змінні додані в Railway Variables
2. **Важливо:** Vite environment variables вбудовуються під час build
3. Якщо змінні додані після build, потрібно:
   - Redeploy service в Railway
   - Або зробити новий commit і push

#### Проблема: CORS errors

**Симптоми:**
- Помилки в console: "CORS policy" або "Access-Control-Allow-Origin"

**Рішення:**
1. Перевірити `CORS_ORIGINS` в backend environment variables
2. Додати web domain в `CORS_ORIGINS`:
   ```env
   CORS_ORIGINS=["https://your-web-domain.up.railway.app"]
   ```
3. Перезапустити backend deployment

#### Проблема: Static files not loading

**Симптоми:**
- 404 errors для JS/CSS files
- App не завантажується

**Рішення:**
1. Перевірити `railway.json` - `startCommand` має бути:
   ```json
   "startCommand": "npx serve -s dist -l $PORT"
   ```
2. Перевірити що build створив `dist` folder
3. Перевірити Railway build logs

---

## 📊 Testing Checklist

### Manual Testing

- [ ] **Chat Flow:**
  - [ ] Відправити "Хочу пробігти 30 хв"
  - [ ] Перевірити clarification question
  - [ ] Відповісти на clarification
  - [ ] Перевірити генерацію плейлисту

- [ ] **Playlist Generation:**
  - [ ] Перевірити що плейлист генерується
  - [ ] Перевірити відображення треків
  - [ ] Перевірити створення в Spotify (якщо автентифіковано)

- [ ] **Spotify OAuth:**
  - [ ] Перевірити login flow
  - [ ] Перевірити callback
  - [ ] Перевірити збереження token

- [ ] **Error Handling:**
  - [ ] Перевірити обробку помилок API
  - [ ] Перевірити обробку timeout
  - [ ] Перевірити обробку network errors

---

## 🔧 Debugging Tips

### Browser Console

Відкрити browser console (F12) та перевірити:

1. **API URL:**
   ```javascript
   // В development mode буде видно в console
   console.log('API URL:', import.meta.env.VITE_API_URL);
   ```

2. **Network Requests:**
   - Відкрити Network tab
   - Відправити повідомлення в чат
   - Перевірити що запити йдуть на правильний backend URL

3. **Errors:**
   - Перевірити що немає помилок в console
   - Перевірити що немає CORS помилок

### Railway Logs

Перевірити Railway logs:

1. **Web App Logs:**
   - Railway Dashboard → Web Service → Logs
   - Перевірити що app запустився
   - Перевірити що немає помилок

2. **Backend Logs:**
   - Railway Dashboard → Backend Service → Logs
   - Перевірити що API запити обробляються
   - Перевірити що немає помилок

---

## ✅ Success Criteria

Web app вважається успішно задеплоєним якщо:

- [x] App завантажується без помилок
- [ ] API connection працює
- [ ] Chat interface працює
- [ ] Playlist generation працює
- [ ] Spotify OAuth працює (якщо налаштовано)
- [ ] Немає критичних помилок в logs

---

## 📝 Next Steps

Після успішного деплою:

1. **Тестування:**
   - Протестувати всі основні функції
   - Перевірити на різних браузерах
   - Перевірити на мобільних пристроях

2. **Моніторинг:**
   - Налаштувати моніторинг Railway
   - Налаштувати error tracking (якщо потрібно)

3. **Оптимізація:**
   - Перевірити performance
   - Оптимізувати bundle size (якщо потрібно)

---

## 🎯 Висновок

**Web app задеплоївся успішно!** ✅

Потрібно перевірити:
1. Environment variables налаштовані
2. Backend API працює
3. API connection працює
4. Всі функції працюють

**Детальні інструкції:** Див. [docs/DEPLOYMENT_FINAL_CHECKLIST.md](./DEPLOYMENT_FINAL_CHECKLIST.md)

