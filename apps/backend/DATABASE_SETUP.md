# Налаштування бази даних Supabase

## Проблема

Помилка: `Could not find the table 'public.users' in the schema cache`

**Причина:** Таблиця `users` не створена в базі даних Supabase.

---

## ✅ Рішення: Створити таблиці в Supabase

### Крок 1: Відкрийте Supabase SQL Editor

1. Перейдіть в [Supabase Dashboard](https://supabase.com/dashboard)
2. Виберіть ваш проект
3. В лівому меню перейдіть в **SQL Editor**
4. Натисніть **"New query"**

### Крок 2: Виконайте міграцію

1. Відкрийте файл `apps/backend/DATABASE_MIGRATION.sql`
2. Скопіюйте весь SQL код
3. Вставте в SQL Editor в Supabase
4. Натисніть **"Run"** (або `Ctrl+Enter`)

### Крок 3: Перевірка

Після виконання міграції перевірте:

1. В Supabase Dashboard → **Table Editor**
2. Мають з'явитися таблиці:
   - ✅ `users`
   - ✅ `workouts`
   - ✅ `playlists`

---

## 📋 Структура таблиць

### Таблиця `users`

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE,
  spotify_user_id TEXT UNIQUE,
  spotify_access_token TEXT,
  spotify_refresh_token TEXT,
  spotify_token_expires_at TIMESTAMPTZ,
  preferences JSONB,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
);
```

### Таблиця `workouts`

```sql
CREATE TABLE workouts (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  type TEXT,
  duration_minutes INTEGER,
  intensity TEXT,
  hr_zones INTEGER[],
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ
);
```

### Таблиця `playlists`

```sql
CREATE TABLE playlists (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  workout_id UUID REFERENCES workouts(id),
  spotify_playlist_id TEXT,
  spotify_url TEXT,
  tracks JSONB,
  total_duration_seconds INTEGER,
  generation_time_seconds FLOAT,
  shared BOOLEAN,
  share_url TEXT,
  created_at TIMESTAMPTZ
);
```

---

## 🔐 Row Level Security (RLS)

RLS увімкнено для всіх таблиць. Створені політики:

1. **Service role** - повний доступ (для backend)
2. **Users** - доступ тільки до своїх даних (якщо використовується Supabase Auth)
3. **Public** - доступ до shared playlists

---

## ⚠️ Важливо

1. **Service Key** - Backend використовує `SUPABASE_SERVICE_KEY`, який обходить RLS
2. **Anon Key** - Frontend використовує `SUPABASE_ANON_KEY`, який підпорядковується RLS
3. **Після міграції** - перезапустіть backend, щоб перевірити підключення

---

## 🧪 Тестування

Після створення таблиць:

1. Перезапустіть backend
2. Спробуйте авторизуватися через Spotify
3. Перевірте, що користувач створюється в таблиці `users`

---

## 📚 Корисні посилання

- [Supabase SQL Editor](https://supabase.com/dashboard/project/_/sql)
- [Supabase RLS Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL UUID Extension](https://www.postgresql.org/docs/current/uuid-ossp.html)
