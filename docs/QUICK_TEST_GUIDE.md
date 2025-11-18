# Швидкий гайд для тестування Error Logging

## 🚀 Крок 1: Запустити Backend

```bash
# Перейти в директорію backend
cd apps/backend

# Запустити через Docker
docker-compose up -d

# Або перезапустити якщо вже запущений
docker-compose restart backend

# Перевірити логи
docker-compose logs -f backend
```

**Очікувані логи:**
```
INFO: Database log handler added successfully
INFO: SpotifyService initialized
INFO: Application startup complete
```

---

## 🧪 Крок 2: Запустити автоматичні тести

```bash
# З кореневої директорії проекту
./scripts/test_error_logging.sh
```

**Очікуваний результат:**
```
🧪 Testing Error Logging System
================================

1️⃣  Testing Health Endpoint
----------------------------
Testing Health Check... ✓ PASSED (HTTP 200)

2️⃣  Testing Error Logging Endpoints
------------------------------------
Testing Trigger ERROR... ✓ PASSED (HTTP 200)
Testing Trigger CRITICAL... ✓ PASSED (HTTP 200)
Testing Trigger WARNING... ✓ PASSED (HTTP 200)
Testing Trigger Exception... ✓ PASSED (HTTP 200)
Testing Direct Log... ✓ PASSED (HTTP 200)

3️⃣  Checking Recent Logs
------------------------
✓ Found 5 recent logs

📊 Test Results
===============
Passed: 6
Failed: 0

✅ All tests passed!
```

---

## 🗄️ Крок 3: Перевірити в Supabase

1. Відкрити https://supabase.com/dashboard
2. Вибрати проект RunBeat
3. Перейти в **Table Editor** → **error_logs**
4. Перевірити чи з'явилися нові записи

**SQL запит:**
```sql
SELECT
  id,
  level,
  message,
  error_type,
  created_at
FROM error_logs
WHERE created_at > NOW() - INTERVAL '5 minutes'
ORDER BY created_at DESC;
```

---

## ✅ Критерії успіху

- [ ] Backend запущений без помилок
- [ ] Всі 6 тестів пройшли успішно
- [ ] В Supabase з'явилося 5+ нових записів
- [ ] Записи містять правильні дані (level, message, created_at)

---

## 🐛 Якщо щось не працює

### Backend не запускається
```bash
# Перевірити логи
docker-compose logs backend

# Перебудувати контейнер
docker-compose up -d --build backend
```

### Тести падають
```bash
# Перевірити чи працює health endpoint
curl http://localhost:8000/health

# Перевірити чи доступний test endpoint
curl http://localhost:8000/api/v1/test-error-logging/trigger-error
```

### Записи не з'являються в БД
```bash
# Перевірити логи на помилки
docker-compose logs backend | grep "Failed to log to database"

# Перевірити Supabase credentials
docker-compose exec backend env | grep SUPABASE
```

---

## 📝 Після успішного тестування

**Готовий до commit?**

```bash
git add .
git commit -m "feat: add error logging test endpoints and documentation"
git push
```

**Наступний крок:** Виправлення async/threading проблем

