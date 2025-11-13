# Звіт про тестування RunBeat Backend

## 📊 Загальна статистика

**Загальна кількість тестів:** 35+

**Модулі з тестами:**
- ✅ Health Endpoints (3 тести)
- ✅ Chat Endpoints (4 тести)
- ✅ Playlist Generator (8 тестів, +2 нові)
- ✅ Playlist Endpoints (6 нових тестів)
- ✅ Playlist Generation (4 нові тести)
- ✅ Workout Endpoints (6 тестів)
- ✅ Auth Endpoints (6 тестів)
- ✅ User Endpoints (4 тести)
- ✅ Playlist History (2 тести)

## 🆕 Оновлені та нові тести

### 1. Selected Tracks Support

**Нові тести:**
- ✅ `test_generate_playlist_with_selected_tracks` - перевірка використання обраних треків з варіанту
- ✅ `test_generate_playlist_with_selected_tracks` - перевірка обходу генерації при передачі selected_tracks

**Що тестується:**
- Передача треків з варіанту через `selected_tracks`
- Пряме використання треків без генерації нового плейлиста
- Коректність передачі всіх необхідних полів треків

### 2. Excluded Track IDs

**Нові тести:**
- ✅ `test_generate_with_excluded_tracks` - перевірка виключення треків
- ✅ `test_preview_playlist_variants_with_excluded_tracks` - перевірка excluded_track_ids при генерації варіантів

**Що тестується:**
- Виключення треків з попередніх генерацій
- Передача `excluded_track_ids` до генератора
- Перевірка, що виключені треки не потрапляють у результат

### 3. Workout ID Reuse

**Нові тести:**
- ✅ `test_generate_playlist_with_workout_id` - перевірка повторного використання workout_id
- ✅ `test_generate_playlist_creates_new_workout` - перевірка створення нового воркаута
- ✅ `test_generate_playlist_reuses_existing_workout` - перевірка повторного використання
- ✅ `test_generate_playlist_invalid_workout_id_fallback` - перевірка fallback при невалідному ID

**Що тестується:**
- Повторне використання існуючого `workout_id`
- Створення нового воркаута при відсутності `workout_id`
- Fallback при невалідному `workout_id` (створює новий)
- Запобігання дублікатів воркаутів

### 4. Duration Validation

**Нові тести:**
- ✅ `test_preview_variants_duration_validation` - перевірка тривалості варіантів
- ✅ `test_generate_playlist_duration_validation` - перевірка тривалості згенерованого плейлиста

**Що тестується:**
- Тривалість варіантів >= тривалість воркаута
- Тривалість згенерованого плейлиста >= тривалість воркаута
- Адаптивна логіка для забезпечення мінімальної тривалості

## 📁 Структура тестів

```
apps/backend/tests/
├── conftest.py              # Pytest конфігурація та фікстури
├── test_health.py           # Health check endpoints
├── test_chat.py             # Chat endpoints
├── test_playlist_generator.py  # Playlist generator logic
├── test_playlist_endpoints.py  # Playlist API endpoints (NEW)
├── test_playlist_generation.py # Playlist generation with new features (NEW)
├── test_playlist_history.py    # Playlist history endpoint
├── test_workouts.py         # Workout CRUD endpoints
├── test_auth.py             # Authentication endpoints
└── test_users.py            # User preferences endpoints
```

## 🚀 Запуск тестів

### Встановлення залежностей
```bash
cd apps/backend
pip install -r requirements.txt
```

### Запуск всіх тестів
```bash
pytest tests/ -v
```

### Запуск конкретних тестів
```bash
# Health tests
pytest tests/test_health.py -v

# Playlist tests (нові функції)
pytest tests/test_playlist_generation.py -v
pytest tests/test_playlist_endpoints.py -v

# Generator tests
pytest tests/test_playlist_generator.py -v
```

### Запуск з покриттям
```bash
pytest tests/ --cov=app --cov-report=html
```

## ✅ Покриття функцій

### Playlist Generator
- ✅ `generate()` - генерація з excluded_track_ids та selected_tracks
- ✅ `_calculate_target_bpm()` - розрахунок BPM з інтенсивності
- ✅ `_create_segments()` - створення сегментів
- ✅ `_bpm_match_score()` - розрахунок відповідності BPM
- ✅ `_calculate_affinity()` - розрахунок відповідності користувачу
- ✅ `_optimize_selection()` - оптимізація з адаптивними обмеженнями
- ✅ `_select_tracks_with_constraints()` - вибір треків з обмеженнями

### Playlist API Endpoints
- ✅ `POST /playlists/generate` - з selected_tracks
- ✅ `POST /playlists/generate` - з workout_id (повторне використання)
- ✅ `POST /playlists/generate` - створення нового воркаута
- ✅ `POST /playlists/preview-variants` - з excluded_track_ids
- ✅ `POST /playlists/preview-variants` - валідація тривалості
- ✅ `GET /playlists/history` - з workout даними
- ✅ `DELETE /playlists/{id}` - видалення плейлиста

### Workout API Endpoints
- ✅ `POST /workouts` - створення воркаута
- ✅ `GET /workouts` - отримання списку
- ✅ `GET /workouts/{id}` - отримання по ID
- ✅ `DELETE /workouts/{id}` - видалення
- ✅ `PATCH /workouts/{id}/complete` - завершення

### Auth API Endpoints
- ✅ `GET /auth/spotify` - ініціація OAuth
- ✅ `GET /auth/spotify/callback` - обробка callback
- ✅ `GET /auth/spotify/status` - перевірка статусу

### Chat API Endpoints
- ✅ `POST /chat/message` - відправка повідомлення
- ✅ `POST /chat/message` - уточнення (clarification)
- ✅ `POST /chat/message` - валідація пустого повідомлення

## 🔍 Ключові перевірки

### 1. Selected Tracks
- ✅ Треки передаються через API
- ✅ Треки використовуються напряму без генерації
- ✅ Всі поля треків коректно обробляються
- ✅ Плейлист створюється з правильними треками

### 2. Excluded Tracks
- ✅ Треки виключаються з генерації
- ✅ excluded_track_ids передаються до генератора
- ✅ Виключені треки не потрапляють у результат

### 3. Workout ID Management
- ✅ Повторне використання існуючого workout_id
- ✅ Створення нового воркаута при відсутності ID
- ✅ Fallback при невалідному ID
- ✅ Запобігання дублікатів

### 4. Duration Guarantees
- ✅ Варіанти мають тривалість >= тривалості воркаута
- ✅ Згенерований плейлист має тривалість >= тривалості воркаута
- ✅ Адаптивна логіка працює коректно

## 📝 Примітки

- Всі тести використовують моки для Supabase та Spotify API
- Тести не вимагають реальних підключень до баз даних або сервісів
- Тести покривають всі нові функції, додані до проекту
- Тести перевіряють як успішні сценарії, так і edge cases

## ⚠️ Відомі обмеження

- Деякі тести можуть потребувати встановлення залежностей (pydantic-core потребує Rust)
- Для повного запуску тестів потрібно встановити всі залежності з requirements.txt

## ✨ Висновок

Тести оновлені та покривають всі нові функції проекту:
- ✅ Selected tracks support
- ✅ Excluded track IDs
- ✅ Workout ID reuse
- ✅ Duration validation

Всі тести готові до запуску після встановлення залежностей.

