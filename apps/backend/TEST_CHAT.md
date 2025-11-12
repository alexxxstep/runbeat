# 🧪 Тестування Chat Endpoints

## Спосіб 1: Unit тести (Mock)

Вже створені unit тести з моками:

```bash
pytest tests/test_chat.py -v
```

## Спосіб 2: Тестування з реальним OpenAI API

### Варіант A: Python скрипт

```bash
python test_chat_endpoint.py
```

**Вимоги:**
- OpenAI API key в `.env` або environment variables
- `OPENAI_API_KEY` має бути встановлений

### Варіант B: HTTP запити (коли сервер запущений)

#### 1. Запустіть сервер:

```bash
uvicorn app.main:app --reload
```

#### 2. Тестуйте через curl:

```bash
# Test 1: Simple workout
curl -X POST "http://localhost:8000/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "Легке відновлення 30 хвилин"}'

# Test 2: Workout requiring clarification
curl -X POST "http://localhost:8000/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "Хочу пробігти 40 хв з інтервалами"}'

# Test 3: Progressive workout
curl -X POST "http://localhost:8000/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "Прогресивний біг 45 хвилин від легкого до швидкого"}'
```

#### 3. Або використайте скрипт:

```bash
bash test_chat_http.sh
# або з production URL:
bash test_chat_http.sh https://ваш-проект.railway.app
```

## Спосіб 3: Через Swagger UI

1. Запустіть сервер: `uvicorn app.main:app --reload`
2. Відкрийте: http://localhost:8000/docs
3. Знайдіть `/chat/message` endpoint
4. Натисніть "Try it out"
5. Введіть тестове повідомлення
6. Натисніть "Execute"

## Тестові повідомлення

### 1. Просте тренування (без clarification):
```
"Легке відновлення 30 хвилин"
"Спокійний біг 45 хвилин"
"Темповий біг 20 хвилин"
```

### 2. Тренування з clarification:
```
"Хочу пробігти 40 хв з інтервалами"
"Потрібен інтервальний біг"
"Фартлек 50 хвилин"
```

### 3. Прогресивне тренування:
```
"Прогресивний біг 45 хвилин від легкого до швидкого"
"Від легкого до темпового за 30 хвилин"
```

## Очікувані результати

### Успішний парсинг (без clarification):
```json
{
  "message": "Зрозумів! Генерую плейлист на 30 хв...",
  "workout": {
    "type": "steady",
    "duration_minutes": 30,
    "intensity": "low",
    "hr_zones": [110, 130],
    "confidence": 0.95,
    "needs_clarification": false
  },
  "needs_clarification": false
}
```

### З clarification:
```json
{
  "message": "Який буде інтервал роботи/відпочинку?",
  "workout": null,
  "needs_clarification": true
}
```

## Troubleshooting

### Помилка: "OpenAI API key not found"
**Рішення:** Перевірте що `OPENAI_API_KEY` встановлений в `.env` або environment variables

### Помилка: "Invalid API key"
**Рішення:** Перевірте що API key правильний та активний

### Помилка: "Rate limit exceeded"
**Рішення:** Зачекайте кілька хвилин або перевірте баланс OpenAI акаунту

### Помилка: "Connection timeout"
**Рішення:** Перевірте інтернет з'єднання та що OpenAI API доступний

## Production тестування

Для тестування на Railway:

```bash
# Замініть на ваш Railway URL
curl -X POST "https://ваш-проект.railway.app/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "Легке відновлення 30 хвилин"}'
```

**Важливо:** Переконайтесь що `OPENAI_API_KEY` встановлений в Railway Variables!

