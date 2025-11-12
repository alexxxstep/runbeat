# 🧪 Тестування Playlist Generator

## Статус тестування

### ✅ Unit тести - PASSED

```bash
pytest tests/test_playlist_generator.py -v
```

**Результати:**

- ✅ test_calculate_target_bpm - PASSED
- ✅ test_create_segments_steady - PASSED
- ✅ test_bpm_match_score - PASSED
- ✅ test_calculate_affinity - PASSED

### ⚠️ Інтеграційні тести - Потребують Spotify credentials

Для тестування з реальним Spotify API потрібні credentials в `.env`:

- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`

---

## Тестування з реальним Spotify API

### Крок 1: Перевірка credentials

```bash
python test_spotify_simple.py
```

Якщо credentials правильні, ви побачите:

```
[OK] Spotify credentials found
[OK] Got 5 tracks!
```

### Крок 2: Тестування генерації плейлисту

```bash
python test_playlist_generation.py
```

Очікуваний результат:

```
[OK] Playlist generated successfully!
Total tracks: 15
Total duration: 1800.0 seconds (30.0 minutes)
Generation time: 8.5 seconds
```

### Крок 3: Тестування через HTTP endpoint

1. **Запустіть сервер:**

   ```bash
   uvicorn app.main:app --reload
   ```

2. **Тестуйте через curl:**

   ```bash
   curl -X POST "http://localhost:8000/playlists/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "workout": {
         "type": "steady",
         "duration_minutes": 30,
         "intensity": "low",
         "hr_zones": [110, 130],
         "confidence": 0.95,
         "needs_clarification": false
       },
       "user_preferences": {
         "top_genres": ["pop", "rock"],
         "top_artists": [],
         "avg_bpm": 145
       }
     }'
   ```

3. **Або через Swagger UI:**
   - Відкрийте: http://localhost:8000/docs
   - Знайдіть `/playlists/generate`
   - Натисніть "Try it out"
   - Введіть тестові дані
   - Натисніть "Execute"

---

## Тестові сценарії

### 1. Steady Workout (30 min, low intensity)

```json
{
  "workout": {
    "type": "steady",
    "duration_minutes": 30,
    "intensity": "low",
    "hr_zones": [110, 130]
  },
  "user_preferences": {
    "top_genres": ["pop"],
    "top_artists": []
  }
}
```

**Очікуваний результат:**

- 3 сегменти (warm-up, main, cool-down)
- BPM ranges: 105-115, 120-130, 100-110
- ~15-20 треків
- Total duration: ~30 хвилин

### 2. Progressive Workout (45 min)

```json
{
  "workout": {
    "type": "progressive",
    "duration_minutes": 45,
    "intensity": "moderate",
    "hr_zones": [120, 160]
  },
  "user_preferences": {
    "top_genres": ["rock", "pop"],
    "top_artists": []
  }
}
```

**Очікуваний результат:**

- 5 сегментів з прогресією BPM
- BPM ranges: 120-130 → 160-170
- ~20-25 треків
- Total duration: ~45 хвилин

### 3. Intervals Workout (40 min)

```json
{
  "workout": {
    "type": "intervals",
    "duration_minutes": 40,
    "intensity": "moderate",
    "hr_zones": [130, 180]
  },
  "user_preferences": {
    "top_genres": ["pop"],
    "top_artists": []
  }
}
```

**Очікуваний результат:**

- 8 сегментів (4 work + 4 rest)
- Work BPM: 140-155, Rest BPM: 115-125
- ~20-25 треків
- Total duration: ~40 хвилин

---

## Troubleshooting

### Помилка: "Spotify credentials not found"

**Рішення:**

1. Перевірте що `.env` файл існує в `apps/backend/`
2. Перевірте що `SPOTIFY_CLIENT_ID` та `SPOTIFY_CLIENT_SECRET` встановлені
3. Перезапустіть сервер після додавання credentials

### Помилка: "404 Not Found" від Spotify API

**Можливі причини:**

1. Неправильні credentials
2. Spotify API змінив формат запитів
3. Rate limit досягнуто

**Рішення:**

1. Перевірте credentials в Spotify Dashboard
2. Перевірте що credentials активні
3. Зачекайте кілька хвилин якщо rate limit

### Помилка: "Empty playlist generated"

**Можливі причини:**

1. BPM ranges занадто вузькі
2. Немає треків що відповідають критеріям
3. Помилка в алгоритмі оптимізації

**Рішення:**

1. Спробуйте ширші BPM ranges
2. Додайте більше genres в user_preferences
3. Перевірте логи для деталей

---

## Метрики успішного тестування

- ✅ Playlist генерується за < 10 секунд
- ✅ Кількість треків: 10-30 (залежить від duration)
- ✅ Total duration: 95-115% від target duration
- ✅ BPM transitions: плавні (< 15 BPM jump)
- ✅ Artist diversity: max 2 треки на артиста
- ✅ Всі треки мають audio features (BPM, energy, etc.)

---

## Production тестування

Для тестування на Railway:

```bash
# Замініть на ваш Railway URL
curl -X POST "https://ваш-проект.railway.app/playlists/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "workout": {
      "type": "steady",
      "duration_minutes": 30,
      "intensity": "low",
      "hr_zones": [110, 130]
    },
    "user_preferences": {
      "top_genres": ["pop"]
    }
  }'
```

**Важливо:** Переконайтесь що `SPOTIFY_CLIENT_ID` та `SPOTIFY_CLIENT_SECRET` встановлені в Railway Variables!

---

**Статус:** ✅ Playlist Generator готовий до тестування з реальними Spotify credentials!
