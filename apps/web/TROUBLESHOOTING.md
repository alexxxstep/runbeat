# Troubleshooting Web App

## Помилка "Network Error"

### Можливі причини та рішення:

#### 1. Backend API не доступний

**Перевірка:**
- Відкрийте консоль браузера (F12)
- Перевірте, чи є запити до API
- Перевірте URL в консолі (має бути видно при запуску в dev режимі)

**Рішення:**
- Переконайтеся, що Backend запущений
- Перевірте, чи правильний `VITE_API_URL` в `.env` файлі
- Для production: перевірте Railway domain backend сервісу

#### 2. CORS помилка

**Симптоми:**
- В консолі браузера помилка про CORS
- "Access-Control-Allow-Origin" помилка

**Рішення:**
- Перевірте `CORS_ORIGINS` в Backend environment variables
- Додайте Web App domain до `CORS_ORIGINS`:
  ```bash
  CORS_ORIGINS=["https://your-web-railway-domain.up.railway.app"]
  ```

#### 3. Неправильний API URL

**Перевірка:**
- Відкрийте консоль браузера
- Має бути лог: `API URL: ...`
- Перевірте, чи URL правильний

**Рішення:**
- Створіть/оновіть `.env` файл в `apps/web`:
  ```bash
  VITE_API_URL=https://your-backend-railway-domain.up.railway.app
  ```
- Перезапустіть dev server після зміни `.env`

#### 4. Backend не відповідає

**Перевірка:**
- Відкрийте backend URL в браузері: `https://your-backend-domain/health`
- Має повернутися `{"status": "healthy", ...}`

**Рішення:**
- Перевірте Railway logs для Backend
- Перевірте, чи Backend запущений
- Перевірте environment variables в Railway

#### 5. Timeout помилка

**Симптоми:**
- "Час очікування вичерпано" помилка

**Рішення:**
- Backend може бути перевантажений
- Перевірте Railway metrics
- Спробуйте знову через кілька секунд

### Швидка діагностика

1. **Відкрийте консоль браузера (F12)**
2. **Перевірте Network tab:**
   - Чи є запити до `/chat/message`?
   - Який статус код?
   - Яка помилка?

3. **Перевірте Console tab:**
   - Чи є помилки?
   - Чи є лог `API URL: ...`?

4. **Перевірте Backend:**
   ```bash
   curl https://your-backend-domain/health
   ```

### Environment Variables Checklist

Переконайтеся, що в Railway для Web App service встановлені:

```bash
VITE_API_URL=https://your-backend-railway-domain.up.railway.app
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
NODE_ENV=production
```

**Важливо:** Після зміни environment variables в Railway, потрібно передеплоїти сервіс!

### Локальна розробка

Якщо тестуєте локально:

1. **Backend має бути запущений:**
   ```bash
   cd apps/backend
   uvicorn app.main:app --reload
   ```

2. **Web App має бути запущений:**
   ```bash
   cd apps/web
   npm run dev
   ```

3. **Перевірте `.env` файл:**
   ```bash
   VITE_API_URL=http://localhost:8000
   ```

### Production деплой

1. **Перевірте Railway domains:**
   - Backend domain: `https://your-backend-domain.up.railway.app`
   - Web App domain: `https://your-web-domain.up.railway.app`

2. **Оновіть CORS в Backend:**
   ```bash
   CORS_ORIGINS=["https://your-web-domain.up.railway.app"]
   ```

3. **Перевірте environment variables в обох сервісах**

4. **Передеплойте обидва сервіси після змін**

---

**Якщо проблема залишається:**
1. Перевірте Railway logs для обох сервісів
2. Перевірте консоль браузера для деталей
3. Спробуйте зробити curl запит до backend напряму

