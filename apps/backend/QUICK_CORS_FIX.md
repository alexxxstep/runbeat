# Швидке виправлення CORS

## Проблема: CORS помилка при запитах з Web App

## Рішення (2 кроки):

### 1. Відкрийте Railway Dashboard → Backend Service → Variables

### 2. Додайте/оновіть змінну:

**Назва:** `CORS_ORIGINS`
**Значення:** `["https://runbeatweb-production.up.railway.app"]`

### 3. Передеплойте Backend

Railway автоматично передеплоїть, або натисніть "Redeploy" вручну.

### 4. Перевірте

Після деплою в логах має бути:

```
CORS_ORIGINS configured: ['https://runbeatweb-production.up.railway.app']
```

---

**Готово!** CORS помилка має зникнути.

Якщо не працює:

- Перевірте, що домен правильний (без слешу)
- Очистіть кеш браузера
- Перевірте логи Backend
