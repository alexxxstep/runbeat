# Інструкції з виконання міграції бази даних

## ⚠️ Важливо: Виконайте міграцію перед використанням

Якщо ви отримуєте помилку:
```
Could not find the 'genres' column of 'workouts' in the schema cache
```

Це означає, що потрібно виконати міграцію бази даних.

---

## 📋 Крок 1: Відкрити Supabase SQL Editor

1. Відкрийте [Supabase Dashboard](https://supabase.com/dashboard)
2. Виберіть ваш проект
3. Перейдіть в розділ **"SQL Editor"** (ліва панель)
4. Натисніть **"New query"**

---

## 📋 Крок 2: Виконати міграцію

### Варіант А: Комплексна міграція (рекомендовано)

Скопіюйте та виконайте весь SQL з файлу:
```
apps/backend/DATABASE_MIGRATION_COMPLETE.sql
```

Ця міграція додасть всі необхідні колонки:
- `genres` (TEXT[])
- `interval_stages` (JSONB)
- `prompt` (TEXT)

### Варіант Б: Окремі міграції

Якщо потрібно виконати окремі міграції:

1. Спочатку виконайте:
   ```
   apps/backend/DATABASE_MIGRATION_ADD_GENRES_AND_STAGES.sql
   ```

2. Потім виконайте:
   ```
   apps/backend/DATABASE_MIGRATION_ADD_PROMPT.sql
   ```

---

## 📋 Крок 3: Перевірка

Після виконання міграції перевірте, що колонки створені:

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'workouts'
AND column_name IN ('genres', 'interval_stages', 'prompt');
```

Ви повинні побачити всі три колонки:
- `genres` (ARRAY)
- `interval_stages` (jsonb)
- `prompt` (text)

---

## 🔍 Якщо міграція не спрацювала

### Проблема 1: Таблиця workouts не існує

Якщо таблиця `workouts` не існує, спочатку виконайте базову міграцію:
```
apps/backend/DATABASE_MIGRATION.sql
```

### Проблема 2: Помилка "column already exists"

Якщо колонка вже існує, міграція використає `IF NOT EXISTS` і не видасть помилку. Це нормально.

### Проблема 3: Помилка прав доступу

Переконайтеся, що ви використовуєте правильний акаунт з правами на зміну схеми бази даних.

---

## ✅ Після виконання міграції

1. Перезапустіть backend сервер (якщо він запущений)
2. Спробуйте створити воркаут знову
3. Помилка повинна зникнути

---

## 📝 Структура таблиці workouts після міграції

```sql
CREATE TABLE workouts (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  type TEXT NOT NULL,
  duration_minutes INTEGER NOT NULL,
  intensity TEXT NOT NULL,
  hr_zones INTEGER[],
  genres TEXT[] DEFAULT ARRAY[]::TEXT[],           -- ✅ Додано
  interval_stages JSONB DEFAULT '[]'::jsonb,        -- ✅ Додано
  prompt TEXT,                                      -- ✅ Додано
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🆘 Підтримка

Якщо після виконання міграції проблема залишається:
1. Перевірте логи backend
2. Переконайтеся, що Supabase кеш оновився (може знадобитися кілька секунд)
3. Перезапустіть backend сервер

