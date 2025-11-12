# Виправлення CORS помилки

## Проблема

```
Access to XMLHttpRequest at 'https://runbeatbackend-production.up.railway.app/chat/message'
from origin 'https://runbeatweb-production.up.railway.app'
has been blocked by CORS policy: Response to preflight request doesn't pass access control check
```

**Причина:** Backend не дозволяє запити з Web App домену через CORS policy.

## Рішення

### Варіант 1: Через Railway Dashboard (Рекомендовано)

1. **Відкрийте Railway Dashboard**

   - Перейдіть до **Backend service** (не Web App service!)
   - Відкрийте вкладку **"Variables"**

2. **Додайте або оновіть `CORS_ORIGINS`**

   **Значення (JSON масив):**

   ```
   ["https://runbeatweb-production.up.railway.app"]
   ```

   **Або з кількома доменами:**

   ```
   ["https://runbeatweb-production.up.railway.app", "http://localhost:3000"]
   ```

3. **Передеплойте Backend service**

   - Railway автоматично передеплоїть після зміни variables
   - Або натисніть **"Redeploy"** вручну
   - Дочекайтеся завершення деплою

4. **Перевірте логи**
   - Після деплою в логах має з'явитися:
   ```
   CORS_ORIGINS configured: ['https://runbeatweb-production.up.railway.app']
   ```

### Варіант 2: Через Railway CLI

```bash
railway variables set CORS_ORIGINS='["https://runbeatweb-production.up.railway.app"]' --service backend
```

### Варіант 3: Через .env файл (локально)

```env
CORS_ORIGINS=["http://localhost:3000","http://localhost:19006"]
```

## Перевірка

Після деплою перевірте логи Backend:

```bash
# В Railway Dashboard → Backend service → Logs
# Має бути:
# CORS_ORIGINS configured: ['https://runbeatweb-production.up.railway.app']
```

## Важливо

1. **Змінну потрібно додавати в Backend service**, не в Web App!
2. **Формат має бути JSON масив** з подвійними лапками
3. **Після зміни variables потрібен redeploy Backend**
4. **Перевірте, що домен Web App правильний** (без слешу в кінці)
5. **Очистіть кеш браузера** після виправлення

## Приклади правильного формату

✅ **Один домен:**

```
["https://runbeatweb-production.up.railway.app"]
```

✅ **Кілька доменів:**

```
["https://runbeatweb-production.up.railway.app", "http://localhost:3000"]
```

✅ **З пробілами (також працює):**

```
["https://runbeatweb-production.up.railway.app", "http://localhost:3000"]
```

## Приклади неправильного формату

❌ `https://runbeatweb-production.up.railway.app` (без лапок і дужок)
❌ `"https://runbeatweb-production.up.railway.app"` (без дужок)
❌ `['https://runbeatweb-production.up.railway.app']` (одинарні лапки)
❌ `https://runbeatweb-production.up.railway.app/` (зі слешем в кінці)

## Додаткові домени

Якщо потрібно додати кілька доменів:

```json
[
  "https://runbeatweb-production.up.railway.app",
  "https://your-mobile-app.expo.dev",
  "http://localhost:3000"
]
```

## Troubleshooting

### CORS все ще не працює

1. **Перевірте логи Backend:**

   - Має бути лог: `CORS_ORIGINS configured: [...]`
   - Переконайтеся, що домен правильний

2. **Перевірте формат:**

   - Має бути JSON масив
   - Без пробілів після коми (або з пробілами - обидва працюють)

3. **Очистіть кеш браузера:**

   - CORS налаштування кешуються браузером
   - Спробуйте в режимі інкогніто

4. **Перевірте, що Backend передеплоївся:**
   - Подивіться на Railway deployment history
   - Переконайтеся, що останній деплой був після зміни variables

---

**Після виправлення CORS помилка "Network Error" має зникнути!**
