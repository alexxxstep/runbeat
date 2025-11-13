# Остаточна міграція бази даних RunBeat

## 📋 Опис

Цей файл містить **остаточну комплексну міграцію** для бази даних RunBeat. Він створює всі необхідні таблиці, колонки, індекси та політики безпеки.

## ✅ Що включає міграція

### Таблиці:
- ✅ `users` - користувачі з Spotify інтеграцією
- ✅ `workouts` - воркаути з усіма необхідними полями
- ✅ `playlists` - згенеровані плейлисти

### Колонки в таблиці `workouts`:
- ✅ Базові: `id`, `user_id`, `type`, `duration_minutes`, `intensity`, `hr_zones`
- ✅ `genres` (TEXT[]) - масив жанрів музики
- ✅ `interval_stages` (JSONB) - інтервальні етапи
- ✅ `prompt` (TEXT) - промпт користувача для пошуку треків

### Індекси:
- ✅ Для швидкого пошуку по `user_id`
- ✅ Для сортування по `created_at`
- ✅ GIN індекси для JSONB та масивів

### Безпека:
- ✅ Row Level Security (RLS) увімкнено
- ✅ Політики доступу налаштовані

## 🚀 Як виконати міграцію

### Крок 1: Відкрити Supabase SQL Editor

1. Відкрийте [Supabase Dashboard](https://supabase.com/dashboard)
2. Виберіть ваш проект
3. Перейдіть в розділ **"SQL Editor"** (ліва панель)
4. Натисніть **"New query"**

### Крок 2: Виконати міграцію

1. Відкрийте файл `apps/backend/DATABASE_MIGRATION_FINAL.sql`
2. Скопіюйте весь SQL код
3. Вставте в SQL Editor
4. Натисніть **"Run"** або `Ctrl+Enter`

### Крок 3: Перевірка

Після виконання міграції перевірте структуру:

```sql
-- Перевірка таблиць
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('users', 'workouts', 'playlists');

-- Перевірка колонок workouts
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'workouts'
ORDER BY ordinal_position;
```

Ви повинні побачити:
- ✅ Таблиці: `users`, `workouts`, `playlists`
- ✅ Колонки `workouts`: `id`, `user_id`, `type`, `duration_minutes`, `intensity`, `hr_zones`, `genres`, `interval_stages`, `prompt`, `completed_at`, `created_at`

## 🔍 Структура таблиці workouts

```sql
CREATE TABLE workouts (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  type TEXT NOT NULL,                    -- 'steady', 'progressive', 'intervals', 'fartlek'
  duration_minutes INTEGER NOT NULL,
  intensity TEXT NOT NULL,               -- 'low', 'moderate', 'high'
  hr_zones INTEGER[] DEFAULT [110, 180],
  genres TEXT[] DEFAULT [],              -- ✅ Додано
  interval_stages JSONB DEFAULT '[]',    -- ✅ Додано
  prompt TEXT,                           -- ✅ Додано
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 📝 Приклади даних

### genres (TEXT[])
```json
["Pop", "Rock", "Electronic"]
```

### interval_stages (JSONB)
```json
[
  {
    "name": "Розминка",
    "duration_minutes": 5,
    "hr_zone": [110, 130],
    "bpm_range": [120, 140]
  },
  {
    "name": "Інтервали",
    "duration_minutes": 20,
    "hr_zone": [150, 180],
    "bpm_range": [160, 180]
  }
]
```

### prompt (TEXT)
```
"енергійна музика для ранкового бігу"
```

## ⚠️ Важливо

1. **Безпека виконання**: Міграція використовує `IF NOT EXISTS`, тому її можна виконувати кілька разів без помилок
2. **Існуючі дані**: Якщо таблиці вже існують, міграція додасть тільки відсутні колонки
3. **Після міграції**: Перезапустіть backend сервер для оновлення кешу схеми

## 🐛 Якщо виникли проблеми

### Помилка: "relation already exists"
- Це нормально, міграція використовує `IF NOT EXISTS`
- Продовжуйте виконання

### Помилка: "column already exists"
- Це нормально для колонок `genres`, `interval_stages`, `prompt`
- Міграція використовує `ADD COLUMN IF NOT EXISTS`

### Помилка: "permission denied"
- Переконайтеся, що ви використовуєте правильний акаунт
- Перевірте права доступу в Supabase

## ✅ Після успішного виконання

1. ✅ Перезапустіть backend сервер
2. ✅ Перевірте створення воркаута з `genres`, `interval_stages`, `prompt`
3. ✅ Перевірте генерацію плейлистів
4. ✅ Перевірте збереження та завантаження з історії

## 📚 Додаткові файли

- `DATABASE_MIGRATION.sql` - базова міграція (створення таблиць)
- `DATABASE_MIGRATION_ADD_GENRES_AND_STAGES.sql` - додавання genres та interval_stages
- `DATABASE_MIGRATION_ADD_PROMPT.sql` - додавання prompt
- `DATABASE_MIGRATION_COMPLETE.sql` - додавання всіх колонок
- **`DATABASE_MIGRATION_FINAL.sql`** - ⭐ остаточна комплексна міграція (використовуйте цей!)

---

**Рекомендація**: Використовуйте `DATABASE_MIGRATION_FINAL.sql` для нового проекту або для повного оновлення існуючої бази даних.

