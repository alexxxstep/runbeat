# Виправлення CORS помилок

## Проблема

Помилка CORS при запитах з production frontend:
```
Access to XMLHttpRequest at 'https://runbeatbackend-production.up.railway.app/...'
from origin 'https://runbeatweb-production.up.railway.app'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
```

## Рішення

### Варіант 1: Додати через Railway Variables (рекомендовано)

1. Відкрийте [Railway Dashboard](https://railway.app)
2. Виберіть ваш backend проект
3. Перейдіть в **Variables**
4. Додайте або оновіть змінну:

**Змінна:** `CORS_ORIGINS`
**Значення:**
```json
["http://localhost:3000","http://localhost:19006","https://runbeatweb-production.up.railway.app"]
```

Або якщо використовуєте comma-separated:
```
http://localhost:3000,http://localhost:19006,https://runbeatweb-production.up.railway.app
```

5. Перезапустіть backend сервіс

### Варіант 2: Додати через FRONTEND_URL

1. В Railway Variables додайте:

**Змінна:** `FRONTEND_URL`
**Значення:** `https://runbeatweb-production.up.railway.app`

2. Перезапустіть backend сервіс

### Варіант 3: Автоматичне визначення (вже додано в код)

Код тепер автоматично додає production URLs до CORS, якщо:
- `ENVIRONMENT=production`
- Виявлено Railway домен

## Перевірка

Після налаштування перевірте логи backend при старті:
```
CORS allowed origins: ['http://localhost:3000', 'http://localhost:19006', 'https://runbeatweb-production.up.railway.app']
```

## Додаткові налаштування

Якщо використовуєте інший frontend URL, додайте його до `CORS_ORIGINS`:

```json
["http://localhost:3000","http://localhost:19006","https://runbeatweb-production.up.railway.app","https://your-custom-domain.com"]
```

## Примітка про 502 Bad Gateway

Якщо ви бачите `502 Bad Gateway`, це означає що:
1. Backend сервіс не запущений або перезавантажується
2. Перевірте статус сервісу в Railway Dashboard
3. Перевірте логи backend на наявність помилок

