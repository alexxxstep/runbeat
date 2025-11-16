# 🧹 Інструкція з очищення після видалення агентів

## ⚠️ ВАЖЛИВО: Видаліть старі змінні з .env файлу

Якщо ви оновили код і бачите помилку:

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
OPENAI_MODEL_CURATOR
  Extra inputs are not permitted
```

**Рішення:** Видаліть наступні рядки з вашого `.env` файлу:

```env
# ❌ ВИДАЛИТИ ці рядки:
OPENAI_MODEL_CURATOR=gpt-4-turbo-preview
USE_LANGCHAIN_CURATOR=true
```

## Що було видалено

### Агенти:

- ❌ **MusicCuratorAgent** (`apps/backend/app/agents/curator.py`)
- ❌ **WorkoutManagerAgent** (`apps/backend/app/agents/manager.py`)

### Промпти:

- ❌ `apps/backend/app/agents/prompts/curator_prompts.py`
- ❌ `apps/backend/app/agents/prompts/manager_prompts.py`

### Тести:

- ❌ `apps/backend/tests/test_music_curator.py`

### Змінні конфігурації:

- ❌ `OPENAI_MODEL_CURATOR`
- ❌ `USE_LANGCHAIN_CURATOR`

## Що залишилось

### Агенти:

- ✅ **SupervisorAgent** - оркестрація розмови
- ✅ **WorkoutBuilder** - розмова та створення воркаутів

### Сервіси:

- ✅ **PlaylistGenerator** - генерація плейлистів через Spotify API (без AI)
- ✅ **WorkoutProfiler** - аналіз параметрів воркаута

### Змінні конфігурації (залишились):

```env
OPENAI_MODEL=gpt-4  # Основна модель
OPENAI_MODEL_PARSER=gpt-4  # Для parser tools
OPENAI_MODEL_CONVERSATION=gpt-3.5-turbo  # Для WorkoutBuilder
OPENAI_MODEL_SUPERVISOR=gpt-4  # Для SupervisorAgent
USE_LANGCHAIN_PARSER=true
USE_LANGCHAIN_SUPERVISOR=true
```

## Як оновити .env файл

### Крок 1: Відкрийте .env файл

```bash
cd apps/backend
nano .env  # або використайте будь-який текстовий редактор
```

### Крок 2: Знайдіть та видаліть рядки

Знайдіть і видаліть:

- `OPENAI_MODEL_CURATOR=...`
- `USE_LANGCHAIN_CURATOR=...`

### Крок 3: Збережіть файл

### Крок 4: Перезапустіть додаток

```bash
# Якщо використовуєте uvicorn
uvicorn app.main:app --reload

# Якщо використовуєте docker
docker-compose restart
```

## Railway (Production)

Якщо ви використовуєте Railway, видаліть змінні там:

1. Відкрийте Railway Dashboard
2. Перейдіть в **Variables**
3. Знайдіть та видаліть:
   - `OPENAI_MODEL_CURATOR`
   - `USE_LANGCHAIN_CURATOR`
4. Збережіть зміни (Railway автоматично перезапустить сервіс)

## Перевірка

Після очищення, запустіть:

```bash
cd apps/backend
python -c "from app.agents import supervisor_agent; print('✅ Імпорт успішний')"
```

Якщо все пройшло успішно, ви побачите: `✅ Імпорт успішний`

## Причини видалення

### MusicCuratorAgent

- Замінений на **PlaylistGenerator**
- Використовує детермінований алгоритм замість AI
- Більш передбачувані результати
- Менша залежність від OpenAI API

### WorkoutManagerAgent

- Функціональність інтегрована в **WorkoutBuilder**
- Спрощення архітектури
- Менше дублювання коду

## Питання?

Якщо у вас виникли проблеми після оновлення, перевірте:

1. `.env` файл не містить видалених змінних
2. Railway Variables оновлені
3. Код оновлений до останньої версії

Для більше інформації дивіться:

- [ENV_EXAMPLE.md](./ENV_EXAMPLE.md)
- [docs/AGENTS_ANALYSIS.md](./docs/AGENTS_ANALYSIS.md)
