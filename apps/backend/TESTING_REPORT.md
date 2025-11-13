# Звіт про тестування RunBeat Backend

## Огляд тестів

Проект містить комплексний набір тестів для всіх основних компонентів системи.

## Статистика тестів

### Загальна кількість тестів: 30+

### Розподіл по модулях:

1. **Health Endpoints** - 3 тести
2. **Chat Endpoints** - 4 тести
3. **Playlist Generator** - 8 тестів (включаючи 2 нові)
4. **Playlist Endpoints** - 6 тестів (включаючи нові функції)
5. **Playlist Generation** - 4 тести (нові)
6. **Workout Endpoints** - 6 тестів
7. **Auth Endpoints** - 6 тестів
8. **User Endpoints** - 4 тести
9. **Playlist History** - 2 тести

## Оновлені тести для нових функцій

### 1. Selected Tracks Support
✅ **test_generate_playlist_with_selected_tracks**
- Перевіряє передачу обраних треків з варіанту
- Перевіряє, що треки використовуються напряму без генерації
- Перевіряє коректність передачі всіх необхідних полів

### 2. Excluded Track IDs
✅ **test_generate_with_excluded_tracks**
- Перевіряє виключення треків з попередніх генерацій
- Перевіряє, що виключені треки не потрапляють у результат

✅ **test_preview_playlist_variants_with_excluded_tracks**
- Перевіряє передачу excluded_track_ids при генерації варіантів
- Перевіряє, що генератор отримує excluded_track_ids

### 3. Workout ID Reuse
✅ **test_generate_playlist_with_workout_id**
- Перевіряє повторне використання існуючого workout_id
- Перевіряє, що новий воркаут не створюється

✅ **test_generate_playlist_creates_new_workout**
- Перевіряє створення нового воркаута при відсутності workout_id

✅ **test_generate_playlist_invalid_workout_id_fallback**
- Перевіряє fallback при невалідному workout_id (створює новий)

### 4. Duration Validation
✅ **test_preview_variants_duration_validation**
- Перевіряє, що варіанти мають тривалість >= тривалості воркаута

✅ **test_generate_playlist_duration_validation**
- Перевіряє, що згенерований плейлист має тривалість >= тривалості воркаута

## Покриття функцій

### Playlist Generator
- ✅ `generate()` - генерація з excluded_track_ids
- ✅ `_calculate_target_bpm()` - розрахунок BPM з інтенсивності
- ✅ `_create_segments()` - створення сегментів для різних типів воркаутів
- ✅ `_bpm_match_score()` - розрахунок відповідності BPM
- ✅ `_calculate_affinity()` - розрахунок відповідності користувачу
- ✅ `_optimize_selection()` - оптимізація з перевіркою тривалості

### Playlist Endpoints
- ✅ `/playlists/generate` - з selected_tracks
- ✅ `/playlists/generate` - з workout_id (повторне використання)
- ✅ `/playlists/generate` - створення нового воркаута
- ✅ `/playlists/preview-variants` - з excluded_track_ids
- ✅ `/playlists/preview-variants` - валідація тривалості варіантів
- ✅ `/playlists/history` - отримання з workout даними
- ✅ `/playlists/{id}` - видалення плейлиста

### Workout Endpoints
- ✅ `/workouts` - створення, отримання списку, отримання по ID
- ✅ `/workouts/{id}` - видалення, завершення

### Auth Endpoints
- ✅ `/auth/spotify` - ініціація OAuth
- ✅ `/auth/spotify/callback` - обробка callback
- ✅ `/auth/spotify/status` - перевірка статусу

## Запуск тестів

```bash
cd apps/backend
pip install -r requirements.txt
pytest tests/ -v
```

## Примітки

- Всі тести використовують моки для Supabase та Spotify API
- Тести не вимагають реальних підключень до баз даних або сервісів
- Нові тести покривають всі додані функції:
  - Selected tracks support
  - Excluded track IDs
  - Workout ID reuse
  - Duration validation

