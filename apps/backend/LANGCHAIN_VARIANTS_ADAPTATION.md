# Адаптація генерації варіантів під LangChain інтеграцію

## Огляд

Код генерації варіантів плейлистів було адаптовано для роботи з LangChain MusicCuratorAgent. Тепер варіанти генеруються з використанням різних `WorkoutIntent` об'єктів, що забезпечує різноманітність плейлистів.

## Основні зміни

### 1. Створення WorkoutIntent для кожного варіанту

**Файл**: `apps/backend/app/api/routes/playlists.py:813-893`

Для кожного варіанту створюється окремий `WorkoutIntent` з різними параметрами:

```python
# Variant 1: Original preferences
workout_intent_variant1 = WorkoutIntent(
    workout_type=workout_type,
    duration_minutes=request.workout.duration_minutes,
    target_bpm_min=bpm_min,
    target_bpm_max=bpm_max,
    music_genres=music_genres_v1,
    music_prompt=request.prompt,
    ...
)

# Variant 2: Modified preferences (different genres, slightly different BPM)
bpm_adjustment = random.choice([-5, 5])
bpm_min_v2 = max(60, min(200, bpm_min + bpm_adjustment))
bpm_max_v2 = max(60, min(200, bpm_max + bpm_adjustment))
prompt_v2 = f"{request.prompt} (alternative style)" if request.prompt else None

workout_intent_variant2 = WorkoutIntent(
    workout_type=workout_type,
    duration_minutes=request.workout.duration_minutes,
    target_bpm_min=bpm_min_v2,
    target_bpm_max=bpm_max_v2,
    music_genres=music_genres_v2,  # Rotated genres
    music_prompt=prompt_v2,  # Modified prompt
    ...
)
```

### 2. Варіації між варіантами

#### Варіації жанрів
- **Variant 1**: Оригінальні жанри (можливо перемішані, якщо є excluded tracks)
- **Variant 2**: Ротація жанрів (перший переміщується в кінець)

#### Варіації BPM
- **Variant 1**: Оригінальний BPM діапазон
- **Variant 2**: BPM діапазон зміщений на ±5 BPM

#### Варіації промпту
- **Variant 1**: Оригінальний промпт
- **Variant 2**: Промпт з додатком "(alternative style)"

### 3. Передача WorkoutIntent до генератора

**Файл**: `apps/backend/app/api/routes/playlists.py:895-914`

```python
variant1_task = generator.generate(
    workout=request.workout,
    user_preferences=user_prefs_variant1,
    interval_stages=interval_stages,
    prompt=request.prompt,
    user_token=user_token,
    excluded_track_ids=excluded_track_ids_from_request,
    workout_intent=workout_intent_variant1,  # ← Передаємо WorkoutIntent для LangChain
)

variant2_task = generator.generate(
    workout=request.workout,
    user_preferences=user_prefs_variant2,
    interval_stages=interval_stages,
    prompt=request.prompt,
    user_token=user_token,
    excluded_track_ids=excluded_track_ids_from_request,
    workout_intent=workout_intent_variant2,  # ← Різний WorkoutIntent для варіанту 2
)
```

### 4. Підтримка інтервальних воркаутів

Якщо воркаут має інтервальні стадії, вони додаються до обох `WorkoutIntent`:

```python
if interval_stages and workout_type in ["intervals", "fartlek"]:
    from app.schemas.llm_responses import IntervalPhase
    intervals = []
    for stage in interval_stages:
        phase_type = "work" if stage.get("hr_zone", 3) >= 3 else "rest"
        bpm_range = stage.get("bpm_range", [bpm_min, bpm_max])
        target_bpm = int((bpm_range[0] + bpm_range[1]) / 2)
        intervals.append(IntervalPhase(
            type=phase_type,
            duration_minutes=stage.get("duration_minutes", 5),
            target_bpm=target_bpm,
        ))
    workout_intent_variant1.intervals = intervals
    workout_intent_variant2.intervals = intervals
```

## Як це працює з LangChain

### 1. MusicCuratorAgent отримує WorkoutIntent

Коли `generator.generate()` викликається з `workout_intent`, він передає його до `MusicCuratorAgent.generate_playlist()`:

```python
# В PlaylistGenerator.generate()
if self.use_langchain_curator and self.curator_agent:
    playlist_response = await self.curator_agent.generate_playlist(
        workout_intent=workout_intent,  # ← Використовується WorkoutIntent
        user_id=user_preferences.get("user_id"),
        user_preferences=user_preferences,
    )
```

### 2. Agent генерує різні плейлисти

Оскільки кожен варіант має різний `WorkoutIntent`:
- Різні жанри → Agent шукає різні треки
- Різний BPM → Agent підбирає треки з іншим темпом
- Різний промпт → Agent інтерпретує запит по-іншому

### 3. Fallback до legacy методу

Якщо LangChain не працює або `USE_LANGCHAIN_CURATOR=False`, використовується legacy метод з `user_preferences` варіаціями.

## Переваги адаптації

1. **Різноманітність**: Кожен варіант має унікальні параметри, що забезпечує різні плейлисти
2. **Інтелектуальність**: LangChain агент може інтерпретувати різні промпти та генерувати більш релевантні плейлисти
3. **Гнучкість**: Легко додавати нові типи варіацій (наприклад, різні energy profiles)
4. **Сумісність**: Працює як з LangChain, так і з legacy методом

## Приклад роботи

### Вхідні дані:
- Workout: steady, 30 min, BPM 130-150
- Genres: ["techno", "house"]
- Prompt: "energetic electronic music"

### Variant 1:
- WorkoutIntent: genres=["techno", "house"], BPM=130-150, prompt="energetic electronic music"
- Agent генерує: техно/хаус плейлист з BPM 130-150

### Variant 2:
- WorkoutIntent: genres=["house", "techno"] (ротація), BPM=135-155 (±5), prompt="energetic electronic music (alternative style)"
- Agent генерує: альтернативний плейлист з іншим балансом жанрів та BPM

## Висновок

Адаптація забезпечує:
- ✅ Правильну роботу з LangChain MusicCuratorAgent
- ✅ Різноманітність між варіантами
- ✅ Зворотну сумісність з legacy методом
- ✅ Паралельну генерацію варіантів для швидкості

