# Тестування RunBeat Backend

## Встановлення залежностей

```bash
cd apps/backend
pip install -r requirements.txt
```

## Запуск тестів

### Всі тести
```bash
pytest tests/ -v
```

### Конкретний тестовий файл
```bash
pytest tests/test_health.py -v
pytest tests/test_chat.py -v
pytest tests/test_playlist_generator.py -v
pytest tests/test_playlist_endpoints.py -v
pytest tests/test_playlist_generation.py -v
```

### З покриттям
```bash
pytest tests/ --cov=app --cov-report=html
```

## Оновлені тести

### 1. Health Endpoints (`test_health.py`)
- ✅ Health check endpoint
- ✅ Readiness check
- ✅ Liveness check

### 2. Chat Endpoints (`test_chat.py`)
- ✅ Successful chat message parsing
- ✅ Chat message requiring clarification
- ✅ Empty message validation
- ✅ Missing field validation

### 3. Playlist Generator (`test_playlist_generator.py`)
- ✅ BPM calculation from intensity
- ✅ Segment creation for steady workouts
- ✅ Segment creation for progressive workouts
- ✅ BPM match score calculation
- ✅ User affinity calculation
- ✅ **NEW**: Playlist generation with excluded tracks
- ✅ **NEW**: Playlist duration validation (duration >= workout duration)

### 4. Playlist Endpoints (`test_playlist_endpoints.py`)
- ✅ Generate playlist with selected tracks from variant
- ✅ Generate playlist with existing workout_id
- ✅ Generate playlist creates new workout when no workout_id
- ✅ Generate playlist reuses existing workout
- ✅ Invalid workout_id fallback (creates new workout)
- ✅ Delete playlist
- ✅ Delete playlist not found

### 5. Playlist Generation (`test_playlist_generation.py`)
- ✅ Generate playlist with pre-selected tracks
- ✅ Generate playlist with workout_id (reuses existing)
- ✅ Preview variants with excluded tracks
- ✅ Variants duration validation (>= workout duration)

### 6. Workout Endpoints (`test_workouts.py`)
- ✅ Create workout
- ✅ Get workouts list
- ✅ Get workout by ID
- ✅ Get workout not found
- ✅ Delete workout
- ✅ Complete workout

### 7. Auth Endpoints (`test_auth.py`)
- ✅ Spotify OAuth initiation
- ✅ Spotify callback missing code
- ✅ Spotify callback invalid state
- ✅ Spotify callback success
- ✅ Spotify auth status authenticated
- ✅ Spotify auth status user not found

### 8. User Endpoints (`test_users.py`)
- ✅ Get user preferences
- ✅ Get user preferences not found
- ✅ Update user preferences
- ✅ Update user preferences not found

### 9. Playlist History (`test_playlist_history.py`)
- ✅ Get playlist history with workout data
- ✅ Get playlist history empty

## Нові функції, що тестуються

### 1. Selected Tracks Support
- Тестування передачі обраних треків з варіанту
- Перевірка, що треки використовуються напряму без генерації

### 2. Excluded Track IDs
- Тестування виключення треків з попередніх генерацій
- Перевірка, що виключені треки не потрапляють у нові варіанти

### 3. Workout ID Reuse
- Тестування повторного використання існуючого воркаута
- Перевірка створення нового воркаута при відсутності ID
- Перевірка fallback при невалідному ID

### 4. Duration Validation
- Перевірка, що варіанти мають тривалість >= тривалості воркаута
- Перевірка адаптивної логіки для забезпечення мінімальної тривалості

## Примітки

- Всі тести використовують моки для Supabase та Spotify API
- Тести не вимагають реальних підключень до баз даних або сервісів
- Для запуску тестів потрібні: pytest, pytest-asyncio

