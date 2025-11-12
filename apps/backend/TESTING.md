# 🧪 Тестування Backend

## Локальне тестування

### Запуск тестів

```bash
cd apps/backend

# Всі тести
pytest

# З детальним виводом
pytest -v

# Конкретний тест
pytest tests/test_health.py -v

# З покриттям коду
pytest --cov=app --cov-report=html
```

### Запуск сервера локально

```bash
cd apps/backend

# Переконайтесь що .env файл заповнений
cp .env.example .env
# Заповніть .env з вашими ключами

# Запуск сервера
uvicorn app.main:app --reload

# Сервер буде доступний на http://localhost:8000
```

### Тестування endpoints локально

```bash
# Health check
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/health/ready

# Liveness check
curl http://localhost:8000/health/live

# API документація (тільки в development)
# Відкрийте в браузері: http://localhost:8000/docs
```

---

## Production тестування (Railway)

### Health Check

```bash
# Замініть на ваш Railway URL
curl https://ваш-проект.railway.app/health

# Очікуваний результат:
# {"status":"healthy","timestamp":"2025-11-12T...","service":"runbeat-api"}
```

### Readiness Check

```bash
curl https://ваш-проект.railway.app/health/ready
```

### Liveness Check

```bash
curl https://ваш-проект.railway.app/health/live
```

### Перевірка через браузер

Відкрийте в браузері:
```
https://ваш-проект.railway.app/health
```

---

## Структура тестів

```
tests/
├── __init__.py
├── conftest.py          # Pytest конфігурація та fixtures
├── test_health.py       # Health check endpoints тести
└── test_*.py            # Інші тести (будуть додані)
```

---

## Написання нових тестів

### Приклад тесту для нового endpoint:

```python
# tests/test_example.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_example_endpoint():
    """Test example endpoint."""
    response = client.get("/api/example")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
```

---

## Перевірка після deployment

### Чеклист:

- [ ] Локальні тести проходять (`pytest`)
- [ ] Сервер запускається локально (`uvicorn app.main:app --reload`)
- [ ] Health endpoint працює локально (`curl http://localhost:8000/health`)
- [ ] Deployment на Railway успішний
- [ ] Health endpoint працює на production (`curl https://...`)
- [ ] Всі environment variables встановлені в Railway
- [ ] Логи не містять критичних помилок

---

## Troubleshooting

### Проблема: Тести не проходять

**Рішення:**
1. Перевірте що всі залежності встановлені: `pip install -r requirements.txt`
2. Перевірте що Python версія правильна: `python --version` (потрібно 3.11+)
3. Перевірте логи: `pytest -v --tb=short`

### Проблема: Сервер не запускається

**Рішення:**
1. Перевірте що `.env` файл існує та заповнений
2. Перевірте що всі required environment variables встановлені
3. Перевірте логи: `uvicorn app.main:app --reload --log-level debug`

### Проблема: Production endpoint не працює

**Рішення:**
1. Перевірте Railway deployment статус
2. Перевірте Railway логи (Dashboard → Deployments → View Logs)
3. Перевірте що всі environment variables встановлені
4. Перевірте Railway URL правильний

---

**Готово!** Backend протестовано та готовий до використання! 🎉

