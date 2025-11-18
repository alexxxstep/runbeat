# План перевірки і виправлення механізму збереження помилок в БД

**Дата створення:** 2025-11-18
**Статус:** В процесі виконання

---

## 📋 Зміст

1. [Поточний стан системи](#поточний-стан-системи)
2. [Етап 1: Аудит](#етап-1-аудит-поточної-системи)
3. [Етап 2: Виявлені проблеми](#етап-2-виявлені-проблеми)
4. [Етап 3: План виправлень](#етап-3-план-виправлень)
5. [Етап 4: Тестування](#етап-4-тестування)
6. [Етап 5: Документація](#етап-5-документація)
7. [Етап 6: Моніторинг](#етап-6-моніторинг)
8. [Етап 7: Чеклист перед деплоєм](#етап-7-чеклист-перед-деплоєм)
9. [Пріоритети виконання](#пріоритети-виконання)

---

## 🔍 Поточний стан системи

### Компоненти:

1. ✅ **Таблиця `error_logs`** в БД (Supabase)
2. ✅ **Backend: `ErrorLoggingService`** (синхронний)
3. ✅ **Backend: `DatabaseLogHandler`** (автоматичне логування через loguru)
4. ✅ **Backend: API endpoint** `/api/v1/error-logs` (для фронтенду)
5. ✅ **Frontend: `errorLogger.ts`** (клієнтський логер)

### Архітектура:

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  errorLogger.ts                                       │   │
│  │  - logError()                                         │   │
│  │  - logWarning()                                       │   │
│  │  - Queue mechanism                                    │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │ HTTP POST                              │
└─────────────────────┼────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API: /api/v1/error-logs                             │   │
│  │  - POST (create)                                      │   │
│  │  - GET (read)                                         │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                        │
│  ┌──────────────────┴───────────────────────────────────┐   │
│  │  ErrorLoggingService                                  │   │
│  │  - log_error() (sync)                                 │   │
│  │  - get_error_logs()                                   │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                        │
│  ┌──────────────────┴───────────────────────────────────┐   │
│  │  DatabaseLogHandler (loguru)                          │   │
│  │  - Auto-captures ERROR/CRITICAL/WARNING               │   │
│  │  - Uses threading.Thread                              │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                        │
└─────────────────────┼────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    SUPABASE DATABASE                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Table: error_logs                                    │   │
│  │  - id (UUID)                                          │   │
│  │  - level (TEXT)                                       │   │
│  │  - message (TEXT)                                     │   │
│  │  - error_type (TEXT)                                  │   │
│  │  - error_details (JSONB)                              │   │
│  │  - stack_trace (TEXT)                                 │   │
│  │  - user_id (UUID)                                     │   │
│  │  - request_path (TEXT)                                │   │
│  │  - request_method (TEXT)                              │   │
│  │  - request_body (JSONB)                               │   │
│  │  - response_status (INTEGER)                          │   │
│  │  - environment (TEXT)                                 │   │
│  │  - service_name (TEXT)                                │   │
│  │  - created_at (TIMESTAMPTZ)                           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Етап 1: Аудит поточної системи

### 1.1. Перевірка таблиці в БД

- [ ] Підключитися до Supabase Dashboard
- [ ] Перевірити існування таблиці `error_logs`
- [ ] Перевірити структуру колонок (відповідність схемі)
- [ ] Перевірити індекси
- [ ] Перевірити RLS policies
- [ ] Перевірити наявність записів (чи працює взагалі?)

### 1.2. Перевірка Backend логування

- [ ] Перевірити ініціалізацію `DatabaseLogHandler` в `main.py`
- [ ] Перевірити чи спрацьовує handler при помилках
- [ ] Перевірити чи `error_logging_service` коректно підключається до Supabase
- [ ] Перевірити threading механізм (чи не блокується?)

### 1.3. Перевірка Frontend логування

- [ ] Перевірити чи `errorLogger.ts` відправляє запити
- [ ] Перевірити чи API endpoint `/api/v1/error-logs` працює
- [ ] Перевірити queue механізм
- [ ] Перевірити чи не блокуються запити через CORS

### 1.4. Перевірка інтеграції

- [ ] Викликати тестову помилку на backend
- [ ] Викликати тестову помилку на frontend
- [ ] Перевірити чи з'являються записи в БД
- [ ] Перевірити чи всі поля заповнюються коректно

---

## 🐛 Етап 2: Виявлені проблеми

### 2.1. Потенційні проблеми Backend

#### ⚠️ CRITICAL: Threading в async контексті

**Проблема:** Використання `threading.Thread` в async FastAPI може бути проблемним

- Блокує event loop
- Може призвести до race conditions
- Не масштабується

**Рішення:** Перейти на `asyncio.create_task()`

#### ⚠️ HIGH: Синхронний Supabase client

**Проблема:** Блокує event loop при записі в БД
**Рішення:** Використати `asyncio.run_in_executor()` або async Supabase client

#### ⚠️ MEDIUM: Відсутність retry механізму

**Проблема:** Якщо БД недоступна, помилка втрачається
**Рішення:** Додати retry з exponential backoff

#### ⚠️ LOW: Відсутність валідації

**Проблема:** Не перевіряється чи user_id існує
**Рішення:** Додати валідацію перед записом

### 2.2. Потенційні проблеми Frontend

#### ⚠️ HIGH: Queue не персистентний

**Проблема:** При перезавантаженні сторінки втрачається
**Рішення:** Зберігати в localStorage

#### ⚠️ MEDIUM: Відсутність batch sending

**Проблема:** Кожна помилка = окремий запит
**Рішення:** Збирати в batch і відправляти раз на 5 секунд

#### ⚠️ MEDIUM: Відсутність rate limiting

**Проблема:** Можливий spam
**Рішення:** Максимум 10 помилок на хвилину

#### ⚠️ LOW: Не логуються всі помилки

**Проблема:** Тільки ті, що явно викликають `errorLogger.logError()`
**Рішення:** Додати global error handler

### 2.3. Потенційні проблеми API

#### ⚠️ CRITICAL: Відсутність rate limiting

**Проблема:** Хтось може заспамити БД
**Рішення:** Додати slowapi rate limiter

#### ⚠️ HIGH: Відсутність валідації розміру даних

**Проблема:** Можна відправити велике `request_body`
**Рішення:** Обмежити розмір полів

#### ⚠️ MEDIUM: Відсутність аутентифікації

**Проблема:** Публічний endpoint
**Рішення:** Вимагати user token (опціонально)

---

## 🔧 Етап 3: План виправлень

### 3.1. Backend виправлення (пріоритет: HIGH)

#### 3.1.1. Перейти на async логування

**Файл:** `apps/backend/app/utils/database_log_handler.py`

**До:**

```python
def log_to_db():
    error_logging_service.log_error(...)

thread = threading.Thread(target=log_to_db, daemon=True)
thread.start()
```

**Після:**

```python
async def log_to_db_async():
    await error_logging_service.log_error_async(...)

asyncio.create_task(log_to_db_async())
```

#### 3.1.2. Зробити ErrorLoggingService async

**Файл:** `apps/backend/app/services/error_logging_service.py`

**Додати:**

```python
async def log_error_async(
    self,
    level: str,
    message: str,
    exception: Optional[Exception] = None,
    ...
) -> Optional[str]:
    """Async version of log_error."""

    loop = asyncio.get_event_loop()

    # Run sync Supabase call in executor
    def _insert():
        return self.supabase.table("error_logs").insert(error_log_data).execute()

    response = await loop.run_in_executor(None, _insert)
    ...
```

#### 3.1.3. Додати retry механізм

**Файл:** `apps/backend/app/services/error_logging_service.py`

**Додати:**

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def log_error_with_retry(...):
    return await self.log_error_async(...)
```

#### 3.1.4. Додати валідацію та обмеження

**Файл:** `apps/backend/app/services/error_logging_service.py`

**Додати:**

```python
# Обмежити розмір stack_trace (макс 10KB)
if stack_trace and len(stack_trace) > 10000:
    stack_trace = stack_trace[:10000] + "\n... (truncated)"

# Обмежити розмір request_body (макс 50KB)
if request_body:
    body_str = str(request_body)
    if len(body_str) > 50000:
        request_body = {"truncated": True, "size": len(body_str)}
```

### 3.2. Frontend виправлення (пріоритет: MEDIUM)

#### 3.2.1. Додати batch sending

**Файл:** `apps/web/src/services/errorLogger.ts`

**Додати:**

```typescript
private batchInterval = 5000; // 5 seconds
private batchTimer: NodeJS.Timeout | null = null;

private startBatchTimer() {
  if (this.batchTimer) return;

  this.batchTimer = setInterval(() => {
    this.processQueue();
  }, this.batchInterval);
}
```

#### 3.2.2. Додати localStorage persistence

**Файл:** `apps/web/src/services/errorLogger.ts`

**Додати:**

```typescript
private loadQueueFromStorage() {
  try {
    const stored = localStorage.getItem('error_queue');
    if (stored) {
      this.queue = JSON.parse(stored);
    }
  } catch (e) {
    console.error('Failed to load error queue from storage');
  }
}

private saveQueueToStorage() {
  try {
    localStorage.setItem('error_queue', JSON.stringify(this.queue));
  } catch (e) {
    console.error('Failed to save error queue to storage');
  }
}
```

#### 3.2.3. Додати rate limiting

**Файл:** `apps/web/src/services/errorLogger.ts`

**Додати:**

```typescript
private maxErrorsPerMinute = 10;
private errorTimestamps: number[] = [];

private checkRateLimit(): boolean {
  const now = Date.now();
  const oneMinuteAgo = now - 60000;

  // Remove old timestamps
  this.errorTimestamps = this.errorTimestamps.filter(t => t > oneMinuteAgo);

  if (this.errorTimestamps.length >= this.maxErrorsPerMinute) {
    console.warn('Error logging rate limit exceeded');
    return false;
  }

  this.errorTimestamps.push(now);
  return true;
}
```

#### 3.2.4. Додати global error handler

**Файл:** `apps/web/src/services/errorLogger.ts`

**Додати:**

```typescript
setupGlobalHandlers() {
  // Catch unhandled errors
  window.addEventListener('error', (event) => {
    this.logError(event.error || event.message, {
      error_details: {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
      },
    });
  });

  // Catch unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    this.logError(event.reason, {
      error_details: {
        type: 'unhandledRejection',
      },
    });
  });
}
```

### 3.3. API виправлення (пріоритет: HIGH)

#### 3.3.1. Додати rate limiting

**Файл:** `apps/backend/app/api/routes/error_logs.py`

**Додати:**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/")
@limiter.limit("10/minute")
async def create_error_log(error_log: ErrorLog):
    ...
```

#### 3.3.2. Додати валідацію розміру

**Файл:** `apps/backend/app/models/error_log.py`

**Оновити:**

```python
from pydantic import BaseModel, Field, validator

class ErrorLog(BaseModel):
    message: str = Field(..., max_length=5000)
    stack_trace: Optional[str] = Field(None, max_length=10000)
    request_body: Optional[Dict[str, Any]] = Field(None)

    @validator('request_body')
    def validate_request_body_size(cls, v):
        if v and len(str(v)) > 50000:
            raise ValueError('request_body too large (max 50KB)')
        return v

    @validator('error_details')
    def validate_error_details_size(cls, v):
        if v and len(str(v)) > 50000:
            raise ValueError('error_details too large (max 50KB)')
        return v
```

---

## 🧪 Етап 4: Тестування

### 4.1. Unit тести

**Файл:** `apps/backend/tests/test_error_logging.py`

```python
import pytest
from app.services.error_logging_service import ErrorLoggingService

@pytest.mark.asyncio
async def test_log_error_async():
    service = ErrorLoggingService()
    error_id = await service.log_error_async(
        level="ERROR",
        message="Test error",
        exception=ValueError("Test exception"),
    )
    assert error_id is not None

@pytest.mark.asyncio
async def test_log_error_with_large_data():
    service = ErrorLoggingService()
    large_body = {"data": "x" * 100000}  # 100KB
    error_id = await service.log_error_async(
        level="ERROR",
        message="Test error",
        request_body=large_body,
    )
    # Should truncate
    assert error_id is not None
```

### 4.2. Integration тести

**Файл:** `apps/backend/tests/test_error_logging_integration.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_error_log_via_api():
    response = client.post("/api/v1/error-logs/", json={
        "level": "ERROR",
        "message": "Test error from API",
        "error_type": "TestError",
    })
    assert response.status_code == 200
    assert "id" in response.json()

def test_rate_limiting():
    # Send 15 requests (limit is 10/minute)
    for i in range(15):
        response = client.post("/api/v1/error-logs/", json={
            "level": "ERROR",
            "message": f"Test error {i}",
        })
        if i < 10:
            assert response.status_code == 200
        else:
            assert response.status_code == 429  # Too Many Requests
```

### 4.3. Load тести

**Файл:** `apps/backend/tests/test_error_logging_load.py`

```python
import asyncio
import pytest

@pytest.mark.asyncio
async def test_concurrent_error_logging():
    service = ErrorLoggingService()

    async def log_error(i):
        return await service.log_error_async(
            level="ERROR",
            message=f"Concurrent error {i}",
        )

    # Simulate 100 concurrent errors
    tasks = [log_error(i) for i in range(100)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Check that most succeeded
    successful = sum(1 for r in results if r is not None and not isinstance(r, Exception))
    assert successful >= 90  # At least 90% success rate
```

### 4.4. Manual тести

**Чеклист:**

- [ ] Викликати помилку в `/api/v1/playlists/generate`
- [ ] Перевірити чи з'явився запис в Supabase
- [ ] Перевірити чи всі поля заповнені
- [ ] Викликати помилку на frontend (throw new Error)
- [ ] Перевірити чи відправився запит до `/api/v1/error-logs`
- [ ] Перевірити чи працює rate limiting (спробувати 15 помилок)
- [ ] Перевірити чи працює фільтрація в GET `/api/v1/error-logs?level=ERROR`

---

## 📝 Етап 5: Документація

### 5.1. Створити документацію

**Файли для створення:**

- [ ] `docs/ERROR_LOGGING_GUIDE.md` - як використовувати систему
- [ ] `docs/ERROR_LOGGING_ARCHITECTURE.md` - архітектура системи
- [ ] `docs/ERROR_LOGGING_TROUBLESHOOTING.md` - вирішення проблем

### 5.2. Додати коментарі в код

**Приклад:**

```python
async def log_error_async(
    self,
    level: str,
    message: str,
    exception: Optional[Exception] = None,
    ...
) -> Optional[str]:
    """
    Log error to database asynchronously.

    This method uses asyncio.run_in_executor to avoid blocking
    the event loop when writing to Supabase.

    Args:
        level: Log level (ERROR, CRITICAL, WARNING)
        message: Error message (max 5000 chars)
        exception: Exception object (optional)
        ...

    Returns:
        Error log ID if successful, None otherwise

    Example:
        >>> error_id = await error_logging_service.log_error_async(
        ...     level="ERROR",
        ...     message="Failed to generate playlist",
        ...     exception=e,
        ...     user_id=user.id,
        ... )
    """
```

---

## 📊 Етап 6: Моніторинг

### 6.1. Додати метрики

**Файл:** `apps/backend/app/api/routes/analytics.py`

**Додати endpoint:**

```python
@router.get("/error-stats")
async def get_error_stats(
    hours: int = Query(24, ge=1, le=168),
):
    """Get error statistics for the last N hours."""

    # Query error_logs table
    # Group by hour, level, error_type
    # Return statistics

    return {
        "total_errors": 123,
        "errors_by_level": {
            "ERROR": 100,
            "CRITICAL": 20,
            "WARNING": 3,
        },
        "top_errors": [
            {"error_type": "ValueError", "count": 50},
            {"error_type": "HTTPException", "count": 30},
        ],
        "errors_by_hour": [...],
    }
```

### 6.2. Додати алерти

**Файл:** `apps/backend/app/services/alert_service.py`

**Створити:**

```python
class AlertService:
    async def check_error_rate(self):
        """Check if error rate is too high."""
        # Query last hour errors
        # If > 100 errors, send alert
        pass

    async def check_critical_errors(self):
        """Check for critical errors."""
        # Query last 5 minutes
        # If any CRITICAL, send alert
        pass
```

---

## ✅ Етап 7: Чеклист перед деплоєм

- [ ] Всі тести пройдені (unit, integration, load)
- [ ] Код пройшов code review
- [ ] Документація оновлена
- [ ] RLS policies перевірені в Supabase
- [ ] Rate limiting налаштований і протестований
- [ ] Cleanup job працює (видалення старих логів)
- [ ] Моніторинг налаштований
- [ ] Rollback план готовий
- [ ] Environment variables налаштовані
- [ ] Logs перевірені (немає критичних помилок)

---

## 🎯 Пріоритети виконання

### CRITICAL (робити зараз):

1. ✅ Перевірити чи взагалі працює логування в БД
2. ✅ Виправити async/threading проблеми
3. ✅ Додати rate limiting на API

### HIGH (робити цього тижня):

4. Додати retry механізм
5. Додати валідацію розміру даних
6. Додати global error handler на frontend

### MEDIUM (робити цього місяця):

7. Додати batch sending на frontend
8. Додати localStorage persistence
9. Створити документацію

### LOW (можна відкласти):

10. Додати метрики та алерти
11. Додати unit тести
12. Оптимізувати performance

---

## 📈 Прогрес виконання

| Етап                 | Статус       | Дата завершення |
| -------------------- | ------------ | --------------- |
| 1. Аудит             | 🔄 В процесі | -               |
| 2. Виявлені проблеми | ✅ Завершено | 2025-11-18      |
| 3. План виправлень   | ✅ Завершено | 2025-11-18      |
| 4. Тестування        | ⏳ Очікує    | -               |
| 5. Документація      | ⏳ Очікує    | -               |
| 6. Моніторинг        | ⏳ Очікує    | -               |
| 7. Деплой            | ⏳ Очікує    | -               |

---

## 📝 Примітки

- Всі зміни робляться покроково з тестуванням після кожного кроку
- Після кожного успішного тестування робиться commit на GitHub
- Документація оновлюється паралельно з розробкою
- Критичні виправлення мають пріоритет над оптимізаціями

---

**Останнє оновлення:** 2025-11-18
**Автор:** AI Assistant
**Статус документа:** Активний
