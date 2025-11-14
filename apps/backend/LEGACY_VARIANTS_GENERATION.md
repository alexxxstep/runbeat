# Legacy код генерації варіантів плейлистів (до LangChain)

## Огляд

Це документ описує попередній код, який використовувався для генерації варіантів плейлистів до інтеграції LangChain. Цей код все ще використовується як fallback метод в `PlaylistGenerator`.

## Основні методи

### 1. `generate()` - Головний метод генерації

**Файл**: `apps/backend/app/services/playlist_generator.py:54-311`

```python
async def generate(
    self,
    workout: Workout,
    user_preferences: Dict,
    interval_stages: Optional[List[Dict]] = None,
    prompt: Optional[str] = None,
    user_token: Optional[str] = None,
    excluded_track_ids: Optional[List[str]] = None,
    workout_intent: Optional[Any] = None,
) -> PlaylistData:
    """
    Legacy generation method (fallback or default)
    """
    # 1. Create workout segments
    segments = self._create_segments(workout, interval_stages)

    # 2. Fetch candidate tracks (parallel)
    candidates = await self._fetch_candidates(
        segments, user_preferences, prompt, user_token
    )

    # Filter out excluded tracks if provided
    if excluded_track_ids:
        excluded_set = set(excluded_track_ids)
        candidates = [c for c in candidates if c.id not in excluded_set]

    # 3. Score tracks
    scored = self._score_tracks(candidates, segments, user_preferences)

    # 4. Optimize selection
    target_duration = workout.duration_minutes * 60
    selected = self._optimize_selection(scored, target_duration)

    total_duration = sum(t.duration_ms for t in selected) / 1000

    return PlaylistData(
        tracks=selected,
        total_duration=total_duration,
        total_tracks=len(selected),
    )
```

### 2. `_create_segments()` - Створення сегментів воркауту

**Файл**: `apps/backend/app/services/playlist_generator.py:313-427`

Створює сегменти воркауту з BPM діапазонами залежно від типу:

- **Steady**: warm-up, main, cool-down
- **Progressive**: 5 сегментів з поступовим збільшенням BPM
- **Intervals**: work/rest сегменти або кастомні стадії
- **Fartlek**: варіативні сегменти з різною інтенсивністю

```python
def _create_segments(
    self, workout: Workout, interval_stages: Optional[List[Dict]] = None
) -> List[Dict]:
    """
    Create workout segments with BPM ranges.
    """
    if workout.type == "steady":
        target_bpm = self._calculate_target_bpm(workout.intensity)
        return [
            {"name": "warm-up", "duration": 5, "bpm_range": [target_bpm - 20, target_bpm - 10]},
            {"name": "main", "duration": max(5, workout.duration_minutes - 10), "bpm_range": [target_bpm - 5, target_bpm + 5]},
            {"name": "cool-down", "duration": 5, "bpm_range": [target_bpm - 25, target_bpm - 15]},
        ]
    # ... інші типи воркаутів
```

### 3. `_fetch_candidates()` - Паралельне отримання кандидатів

**Файл**: `apps/backend/app/services/playlist_generator.py:446-483`

Отримує треки для всіх сегментів паралельно:

```python
async def _fetch_candidates(
    self,
    segments: List[Dict],
    user_prefs: Dict,
    prompt: Optional[str] = None,
    user_token: Optional[str] = None,
) -> List[Track]:
    """
    Fetch candidate tracks for all segments (parallel).
    """
    tasks = [
        self._fetch_for_segment(seg, user_prefs, prompt, user_token)
        for seg in segments
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_candidates = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Error fetching tracks for segment {i}: {result}")
            continue
        if isinstance(result, list):
            all_candidates.extend(result)

    return all_candidates
```

### 4. `_fetch_for_segment()` - Отримання треків для сегменту

**Файл**: `apps/backend/app/services/playlist_generator.py:485-640`

Отримує треки для одного сегменту через Spotify Recommendations API:

```python
async def _fetch_for_segment(
    self,
    segment: Dict,
    user_prefs: Dict,
    prompt: Optional[str] = None,
    user_token: Optional[str] = None,
) -> List[Track]:
    """
    Fetch tracks for one segment.
    """
    bpm_min, bpm_max = segment["bpm_range"]
    target_bpm = int((bpm_min + bpm_max) / 2)

    # Use Spotify Recommendations API
    if hasattr(self.spotify, 'get_recommendations_optimized'):
        spotify_tracks = await self.spotify.get_recommendations_optimized(
            seed_genres=user_prefs.get("top_genres", [])[:2],
            seed_artists=user_prefs.get("top_artists", [])[:2],
            target_tempo=target_bpm,
            min_tempo=int(bpm_min),
            max_tempo=int(bpm_max),
            target_energy=0.7,
            limit=50,
            user_token=user_token,
        )
    else:
        spotify_tracks = await self.spotify.get_recommendations(
            seed_genres=user_prefs.get("top_genres", [])[:2],
            seed_artists=user_prefs.get("top_artists", [])[:2],
            target_tempo=target_bpm,
            min_tempo=int(bpm_min),
            max_tempo=int(bpm_max),
            target_energy=0.7,
            limit=50,
        )

    # Convert Spotify tracks to Track objects
    tracks = []
    for spotify_track in spotify_tracks:
        track = Track(
            id=spotify_track.get("id", ""),
            name=spotify_track.get("name", ""),
            artist=", ".join([a["name"] for a in spotify_track.get("artists", [])]),
            # ... інші поля
        )
        tracks.append(track)

    return tracks
```

### 5. `_score_tracks()` - Оцінка треків

**Файл**: `apps/backend/app/services/playlist_generator.py:647-737`

Оцінює треки на основі:
- Відповідності BPM сегменту
- Енергії треку
- Жанрових переваг користувача
- Danceability та valence

```python
def _score_tracks(
    self,
    candidates: List[Track],
    segments: List[Dict],
    user_prefs: Dict,
) -> List[Tuple[Track, float]]:
    """
    Score tracks based on segment requirements and user preferences.
    """
    scored = []

    for track in candidates:
        score = 0.0

        # Find best matching segment
        best_segment = None
        best_segment_score = 0.0

        for segment in segments:
            bpm_min, bpm_max = segment["bpm_range"]
            if bpm_min <= track.bpm <= bpm_max:
                segment_score = 1.0 - abs(track.bpm - (bpm_min + bpm_max) / 2) / 20.0
                if segment_score > best_segment_score:
                    best_segment_score = segment_score
                    best_segment = segment

        if best_segment:
            score += best_segment_score * 0.4  # BPM match weight

        # Energy score
        if track.energy:
            score += track.energy * 0.2

        # Genre match
        if user_prefs.get("top_genres") and track.genres:
            user_genres = set(g.lower() for g in user_prefs["top_genres"])
            track_genres = set(g.lower() for g in track.genres)
            if user_genres & track_genres:
                score += 0.2

        # Danceability
        if track.danceability:
            score += track.danceability * 0.1

        # Valence (positive mood)
        if track.valence:
            score += track.valence * 0.1

        scored.append((track, score))

    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    return scored
```

### 6. `_optimize_selection()` - Оптимізація вибору

**Файл**: `apps/backend/app/services/playlist_generator.py:738-902`

Вибір треків для плейлиста з урахуванням:
- Цільової тривалості
- Розподілу по сегментах
- Мінімальної кількості треків

```python
def _optimize_selection(
    self,
    scored: List[Tuple[Track, float]],
    target_duration: float,
) -> List[Track]:
    """
    Optimize track selection to match target duration.
    """
    selected = []
    current_duration = 0.0

    for track, score in scored:
        track_duration = track.duration_ms / 1000.0

        # Check if adding this track would exceed target too much
        if current_duration + track_duration > target_duration * 1.2:
            break

        selected.append(track)
        current_duration += track_duration

        # Stop if we have enough duration
        if current_duration >= target_duration:
            break

    return selected
```

## Генерація варіантів

**Файл**: `apps/backend/app/api/routes/playlists.py:714-1161`

Варіанти генеруються через виклик `generator.generate()` двічі з різними параметрами:

```python
async def _generate_variants_internal(
    request: PlaylistGenerateRequest,
    generator: PlaylistGenerator,
) -> PlaylistVariantsResponse:
    """
    Generate 2 variants by calling generator.generate() twice with different preferences.
    """
    # Variant 1: Original preferences
    user_prefs_variant1 = request.user_preferences or {}

    # Variant 2: Modified preferences (rotated genres, adjusted BPM)
    user_prefs_variant2 = user_prefs_variant1.copy()
    if "top_genres" in user_prefs_variant2:
        genres = user_prefs_variant2["top_genres"].copy()
        genres = genres[1:] + genres[:1]  # Rotate
        user_prefs_variant2["top_genres"] = genres

    # Generate both variants in parallel
    variant1_task = generator.generate(
        workout=request.workout,
        user_preferences=user_prefs_variant1,
        interval_stages=interval_stages,
        prompt=request.prompt,
        user_token=user_token,
        excluded_track_ids=excluded_track_ids_from_request,
    )

    variant2_task = generator.generate(
        workout=request.workout,
        user_preferences=user_prefs_variant2,
        interval_stages=interval_stages,
        prompt=request.prompt,
        user_token=user_token,
        excluded_track_ids=excluded_track_ids_from_request,
    )

    # Execute in parallel
    playlist_data_variant1, playlist_data_variant2 = await asyncio.gather(
        variant1_task,
        variant2_task,
        return_exceptions=True
    )

    # Filter duplicates from variant 2
    variant1_track_ids = {track.id for track in playlist_data_variant1.tracks}
    variant2_tracks_filtered = [
        track for track in playlist_data_variant2.tracks
        if track.id not in variant1_track_ids
    ]

    return PlaylistVariantsResponse(
        variant1=TrackVariant(...),
        variant2=TrackVariant(...),
    )
```

## Переваги legacy методу

1. **Швидкість**: Паралельна обробка сегментів та варіантів
2. **Надійність**: Простий алгоритм без залежності від LLM
3. **Контроль**: Точний контроль над BPM, енергією, жанрами
4. **Масштабованість**: Легко додавати нові критерії оцінки

## Недоліки legacy методу

1. **Обмежена інтелектуальність**: Не використовує контекст розмови
2. **Жорсткі правила**: Фіксовані алгоритми оцінки
3. **Відсутність адаптації**: Не навчається на попередніх виборах

## Використання зараз

Legacy метод використовується як:
1. **Fallback**: Коли LangChain MusicCuratorAgent не працює
2. **За замовчуванням**: Якщо `USE_LANGCHAIN_CURATOR=False`
3. **Для варіантів**: Генерація варіантів через `preview_playlist_variants` endpoint

## Висновок

Legacy код все ще працює і використовується як надійний fallback. Він оптимізований для швидкої генерації плейлистів з точним контролем параметрів, але не має інтелектуальності LangChain агентів.

