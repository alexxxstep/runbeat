# Інструкція для тестування Error Logging System

**Дата:** 2025-11-18
**Мета:** Перевірити чи працює система логування помилок в БД

---

## 🔧 Крок 1: Підготовка

### 1.1. Перезапустити backend
```bash
cd apps/backend
docker-compose restart backend
# або
docker-compose up -d --build backend
```

### 1.2. Перевірити логи
```bash
docker-compose logs -f backend
```

Ви повинні побачити:
```
INFO: Database log handler added successfully
INFO: SpotifyService initialized
```

---

## 🧪 Крок 2: Тестування через API

### 2.1. Перевірити чи endpoint доступний

**Запит:**
```bash
curl http://localhost:8000/api/v1/test-error-logging/trigger-error
```

**Очікувана відповідь:**
```json
{
  "status": "error_logged",
  "message": "Test error has been logged. Check Supabase error_logs table.",
  "note": "This error was logged via logger.error() and should appear in the database."
}
```

### 2.2. Перевірити CRITICAL помилку

**Запит:**
```bash
curl http://localhost:8000/api/v1/test-error-logging/trigger-critical
```

**Очікувана відповідь:**
```json
{
  "status": "critical_logged",
  "message": "Test critical error has been logged."
}
```

### 2.3. Перевірити WARNING

**Запит:**
```bash
curl http://localhost:8000/api/v1/test-error-logging/trigger-warning
```

**Очікувана відповідь:**
```json
{
  "status": "warning_logged",
  "message": "Test warning has been logged."
}
```

### 2.4. Перевірити exception логування

**Запит:**
```bash
curl http://localhost:8000/api/v1/test-error-logging/trigger-exception
```

**Очікувана відповідь:**
```json
{
  "status": "exception_logged",
  "message": "Test exception has been logged.",
  "exception_type": "ValueError"
}
```

### 2.5. Прямий виклик error_logging_service

**Запит:**
```bash
curl -X POST "http://localhost:8000/api/v1/test-error-logging/direct-log?message=Direct%20test%20log&level=ERROR"
```

**Очікувана відповідь:**
```json
{
  "status": "logged",
  "error_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Error logged directly with ID: 550e8400-..."
}
```

### 2.6. Перевірити останні логи

**Запит:**
```bash
curl http://localhost:8000/api/v1/test-error-logging/check-recent-logs?limit=5
```

**Очікувана відповідь:**
```json
{
  "status": "success",
  "count": 5,
  "logs": [
    {
      "id": "...",
      "level": "ERROR",
      "message": "TEST ERROR: This is a test error...",
      "created_at": "2025-11-18T18:30:00Z",
      ...
    }
  ]
}
```

---

## 🗄️ Крок 3: Перевірка в Supabase

### 3.1. Відкрити Supabase Dashboard
1. Перейти на https://supabase.com/dashboard
2. Вибрати проект RunBeat
3. Перейти в розділ **Table Editor**
4. Вибрати таблицю **error_logs**

### 3.2. Перевірити записи

**Що перевіряти:**
- [ ] Чи з'явилися нові записи після тестів?
- [ ] Чи заповнені всі поля (level, message, created_at)?
- [ ] Чи є user_id, request_path, request_method?
- [ ] Чи є error_details (JSONB)?
- [ ] Чи правильний environment (development/production)?

**SQL запит для перевірки:**
```sql
SELECT
  id,
  level,
  message,
  error_type,
  user_id,
  request_path,
  created_at
FROM error_logs
WHERE created_at > NOW() - INTERVAL '10 minutes'
ORDER BY created_at DESC
LIMIT 10;
```

### 3.3. Перевірити індекси

**SQL запит:**
```sql
SELECT
  indexname,
  indexdef
FROM pg_indexes
WHERE tablename = 'error_logs';
```

**Очікувані індекси:**
- `idx_error_logs_level`
- `idx_error_logs_created_at`
- `idx_error_logs_user_id`
- `idx_error_logs_error_type`
- `idx_error_logs_environment`

---

## 📊 Крок 4: Аналіз результатів

### 4.1. Успішний сценарій ✅

**Якщо все працює:**
- ✅ Всі 5 тестових запитів повернули статус 200
- ✅ В Supabase з'явилося 5+ нових записів
- ✅ Всі поля заповнені коректно
- ✅ Логи backend не містять помилок

**Висновок:** Система логування працює коректно!

### 4.2. Проблемний сценарій ❌

**Якщо щось не працює:**

#### Проблема 1: Записи не з'являються в БД
**Можливі причини:**
- DatabaseLogHandler не ініціалізувався
- Supabase credentials неправильні
- RLS policies блокують запис
- Threading не працює

**Перевірити:**
```bash
# Перевірити логи backend
docker-compose logs backend | grep "Database log handler"
docker-compose logs backend | grep "Failed to log to database"
```

#### Проблема 2: Endpoint не доступний
**Можливі причини:**
- Backend не запущений
- ENVIRONMENT != "development"
- Роутер не підключений

**Перевірити:**
```bash
# Перевірити чи працює backend
curl http://localhost:8000/health

# Перевірити environment
docker-compose exec backend env | grep ENVIRONMENT
```

#### Проблема 3: Помилка при записі в БД
**Можливі причини:**
- Supabase недоступний
- Таблиця error_logs не існує
- RLS policies занадто обмежувальні

**Перевірити:**
```bash
# Перевірити Supabase connection
docker-compose logs backend | grep "Supabase"
```

---

## 🔍 Крок 5: Детальна діагностика

### 5.1. Перевірити DatabaseLogHandler

**Додати тимчасовий debug log:**
```python
# В apps/backend/app/utils/database_log_handler.py
def __call__(self, message: Dict[str, Any]) -> None:
    print(f"DEBUG: DatabaseLogHandler called with level: {message.get('level')}")
    ...
```

### 5.2. Перевірити ErrorLoggingService

**Додати тимчасовий debug log:**
```python
# В apps/backend/app/services/error_logging_service.py
def log_error(self, ...):
    print(f"DEBUG: log_error called with level: {level}, message: {message[:50]}")
    ...
```

### 5.3. Перевірити Supabase connection

**Створити тестовий endpoint:**
```python
@router.get("/test-supabase-connection")
async def test_supabase():
    try:
        from app.services.supabase_service import supabase_service
        client = supabase_service.get_client()

        # Try to query error_logs
        response = client.table("error_logs").select("id").limit(1).execute()

        return {
            "status": "connected",
            "table_accessible": True,
            "sample_count": len(response.data) if response.data else 0,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }
```

---

## ✅ Чеклист тестування

### Базові тести:
- [ ] Backend запущений і доступний
- [ ] Endpoint `/api/v1/test-error-logging/trigger-error` працює
- [ ] Endpoint `/api/v1/test-error-logging/trigger-critical` працює
- [ ] Endpoint `/api/v1/test-error-logging/trigger-warning` працює
- [ ] Endpoint `/api/v1/test-error-logging/trigger-exception` працює
- [ ] Endpoint `/api/v1/test-error-logging/direct-log` працює

### Перевірка БД:
- [ ] Записи з'являються в таблиці error_logs
- [ ] Поле `level` заповнене (ERROR/CRITICAL/WARNING)
- [ ] Поле `message` заповнене
- [ ] Поле `created_at` заповнене
- [ ] Поле `user_id` заповнене (якщо передано)
- [ ] Поле `request_path` заповнене
- [ ] Поле `error_details` заповнене (JSONB)
- [ ] Поле `environment` = "development"

### Перевірка логів:
- [ ] В логах backend немає помилок "Failed to log to database"
- [ ] В логах backend є "Database log handler added successfully"
- [ ] В логах backend є записи про тестові помилки

### Фінальна перевірка:
- [ ] Всі тести пройшли успішно
- [ ] Система готова до виправлення async/threading проблем

---

## 📝 Результати тестування

**Дата тестування:** _____________
**Тестував:** _____________

**Результат:**
- [ ] ✅ Всі тести пройшли успішно
- [ ] ⚠️ Частково працює (вказати проблеми)
- [ ] ❌ Не працює (вказати причину)

**Проблеми (якщо є):**
```
1.
2.
3.
```

**Наступні кроки:**
```
1.
2.
3.
```

---

**Примітка:** Після успішного тестування можна переходити до виправлення async/threading проблем.

