# Алгоритм генерації плейлистів RunBeat

## 📊 Параметри воркаута в базі даних

### ✅ Зберігаються в таблиці `workouts`:

- `type` - Тип тренування (steady, progressive, intervals, fartlek)
- `duration_minutes` - Тривалість в хвилинах
- `intensity` - Інтенсивність (low, moderate, high)
- `hr_zones` - Частота серцебиття [мінімум, максимум]

### ❌ НЕ зберігаються (беруться з поточних налаштувань):

- `genres` - Жанри музики (беруться з `workoutSettings.genres`)
- `interval_stages` - Етапи інтервального тренування (беруться з `workoutSettings.intervalStages`)

**Проблема:** При активації існуючого воркаута використовуються поточні налаштування жанрів та етапів, а не збережені.

---

## 🔄 Алгоритм генерації плейлистів

### Крок 1: Створення сегментів тренування (`_create_segments`)

На основі типу тренування створюються сегменти з BPM діапазонами:

#### **Steady (Стабільна)**

```python
target_bpm = calculate_target_bpm(intensity)
# low: ~130 BPM, moderate: ~145 BPM, high: ~165 BPM

Сегменти:
1. Warm-up (5 хв): [target_bpm - 20, target_bpm - 10]
2. Main (duration - 10 хв): [target_bpm - 5, target_bpm + 5]
3. Cool-down (5 хв): [target_bpm - 25, target_bpm - 15]
```

#### **Progressive (Прогресивна)**

```python
start_bpm = calculate_target_bpm("low")  # ~130
end_bpm = calculate_target_bpm("high")   # ~165
num_segments = 5

Сегменти: 5 рівномірних сегментів від start_bpm до end_bpm
Кожен сегмент: [current_bpm - 5, current_bpm + 5]
```

#### **Intervals (Інтервальна)**

```python
Якщо є interval_stages:
  Використовуються кастомні етапи з bpm_range та duration_minutes
Інакше:
  За замовчуванням: 8 сегментів (4 робочих + 4 відпочинку)
  Робочі: [target_bpm - 5, target_bpm + 5]
  Відпочинок: [target_bpm - 30, target_bpm - 20]
```

#### **Fartlek (Фартлек)**

```python
target_bpm = calculate_target_bpm(intensity)
num_segments = 6-8 (випадкові)

Сегменти з випадковими BPM в діапазоні:
[target_bpm - 15, target_bpm + 15]
```

### Крок 2: Пошук кандидатів (`_fetch_candidates`)

Для кожного сегменту виконується паралельний пошук треків:

```python
async def _fetch_for_segment(segment, user_prefs):
    bpm_min, bpm_max = segment["bpm_range"]
    target_bpm = (bpm_min + bpm_max) / 2

    # Використання Spotify Recommendations API
    tracks = await spotify.get_recommendations(
        seed_genres=user_prefs.get("top_genres", [])[:2],  # Перші 2 жанри
        seed_artists=user_prefs.get("top_artists", [])[:2], # Перші 2 виконавці
        target_tempo=target_bpm,
        min_tempo=bpm_min,
        max_tempo=bpm_max,
        target_energy=0.7,  # Висока енергія для тренувань
        limit=20
    )
```

**Промпт пошуку:**

- **Жанри:** Використовуються з `user_preferences.top_genres` (з поточних налаштувань)
- **BPM:** Розраховується на основі `intensity` та `hr_zones`
- **Енергія:** Фіксована 0.7 (висока для тренувань)

### Крок 3: Оцінка треків (`_score_tracks`)

Кожен трек отримує оцінку на основі:

```python
score = (
    bpm_match_score * 0.4 +      # Відповідність BPM сегменту
    energy_score * 0.3 +          # Енергійність треку
    danceability_score * 0.2 +    # Танцювальність
    genre_match_score * 0.1       # Відповідність жанрам
)
```

### Крок 4: Оптимізація вибору (`_optimize_selection`)

```python
1. Сортування треків за оцінкою (від найвищої)
2. Вибір треків до досягнення duration_minutes * 60 секунд
3. Перевірка на унікальність назв (case-insensitive)
4. Балансування по сегментах
```

---

## 🎯 Як параметри воркаута використовуються

### ✅ Використовуються з бази даних:

1. **`type`** → Визначає стратегію створення сегментів
2. **`duration_minutes`** → Загальна тривалість плейлисту
3. **`intensity`** → Розрахунок target_bpm:
   - low: ~130 BPM
   - moderate: ~145 BPM
   - high: ~165 BPM
4. **`hr_zones`** → Може використовуватися для додаткової валідації (зараз не використовується напряму)

### ⚠️ Беруться з поточних налаштувань (НЕ з бази):

1. **`genres`** → `workoutSettings.genres` → `user_preferences.top_genres`
2. **`interval_stages`** → `workoutSettings.intervalStages`

---

## 🔧 Рекомендації для покращення

### 1. Збереження жанрів в базі даних

```sql
ALTER TABLE workouts
ADD COLUMN genres TEXT[] DEFAULT ARRAY[]::TEXT[];
```

### 2. Збереження етапів інтервального тренування

```sql
ALTER TABLE workouts
ADD COLUMN interval_stages JSONB DEFAULT '[]'::jsonb;
```

### 3. Використання збережених параметрів

При активації воркаута з історії:

- Використовувати `workout.genres` замість `workoutSettings.genres`
- Використовувати `workout.interval_stages` замість `workoutSettings.intervalStages`

---

## 📝 Приклад використання параметрів

```python
# При активації воркаута з історії:
workout = {
    "type": "intervals",
    "duration_minutes": 45,
    "intensity": "high",
    "hr_zones": [140, 180],
    # Ці параметри беруться з поточних налаштувань:
    "genres": workoutSettings.genres,  # ❌ Може відрізнятися від оригіналу
    "interval_stages": workoutSettings.intervalStages  # ❌ Може відрізнятися
}

# Алгоритм:
1. Створює сегменти на основі type + interval_stages
2. Для кожного сегменту шукає треки з BPM в діапазоні
3. Використовує genres для seed_genres в Spotify API
4. Фільтрує та оцінює треки
5. Вибірає оптимальний набір до duration_minutes
```
