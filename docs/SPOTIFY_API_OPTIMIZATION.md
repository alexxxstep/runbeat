# 🎵 Оптимізація запитів до Spotify API

## 📊 Поточний стан

### Проблеми:

1. **Recommendations API повертає 404** - Client Credentials не мають доступу
2. **Search API не знаходить треків** - неправильний формат запитів
3. **Багато запитів** - для кожного сегменту окремий запит
4. **Немає кешування** - повторні запити для однакових параметрів
5. **Неефективне використання batch API** - audio features запитуються окремо

---

## 🎯 Оптимальна стратегія

### 1. **Використання User Authorization для Recommendations API**

**Проблема:** Client Credentials не мають доступу до Recommendations API (404 error)

**Рішення:** Використовувати User Authorization токен користувача

```python
# Поточна реалізація (Client Credentials)
sp = spotipy.Spotify(
    client_credentials_manager=self.client_credentials
)

# Оптимальна реалізація (User Authorization)
sp = spotipy.Spotify(auth=user_access_token)
```

**Переваги:**

- ✅ Recommendations API працює з User Authorization
- ✅ Доступ до персональних рекомендацій
- ✅ Кращі результати на основі історії прослуховування

**Недоліки:**

- ⚠️ Потрібен refresh token для довгострокового використання
- ⚠️ Потрібно зберігати токени користувачів

---

### 2. **Гібридний підхід: User Auth + Client Credentials**

**Стратегія:**

- **User Authorization** для Recommendations API (якщо доступний)
- **Client Credentials** для Search API та Audio Features (fallback)

```python
async def get_tracks_optimized(
    self,
    user_token: Optional[str] = None,
    seed_genres: List[str],
    min_tempo: int,
    max_tempo: int,
    target_energy: float,
    limit: int = 20,
) -> List[Dict]:
    """
    Оптимізований метод отримання треків.

    Strategy:
    1. Якщо є user_token → використовувати Recommendations API
    2. Якщо немає → використовувати Search API з Client Credentials
    3. Batch запити для audio features
    """
    if user_token:
        # Try Recommendations API with User Auth
        try:
            sp = spotipy.Spotify(auth=user_token)
            # Get seed tracks from genres
            seed_tracks = await self._get_seed_tracks_from_genres(
                sp, seed_genres
            )
            recommendations = sp.recommendations(
                seed_tracks=seed_tracks[:5],
                min_tempo=min_tempo,
                max_tempo=max_tempo,
                target_energy=target_energy,
                limit=limit
            )
            return recommendations.get("tracks", [])
        except Exception as e:
            logger.warning(f"Recommendations API failed: {e}, using Search API")

    # Fallback to Search API with Client Credentials
    return await self.get_tracks_by_search(
        seed_genres=seed_genres,
        min_tempo=min_tempo,
        max_tempo=max_tempo,
        target_energy=target_energy,
        limit=limit
    )
```

---

### 3. **Batch запити для Audio Features**

**Поточна проблема:** Запитуємо audio features для кожного треку окремо

**Оптимальне рішення:** Batch запити до 100 треків одночасно

```python
async def get_audio_features_batch_optimized(
    self,
    track_ids: List[str],
    batch_size: int = 100
) -> List[Optional[Dict]]:
    """
    Оптимізований batch запит для audio features.

    Spotify API дозволяє до 100 треків в одному запиті.
    """
    features = []

    # Розбиваємо на батчі по 100
    for i in range(0, len(track_ids), batch_size):
        batch = track_ids[i:i + batch_size]

        try:
            sp = spotipy.Spotify(
                client_credentials_manager=self.client_credentials
            )
            batch_features = sp.audio_features(batch)
            features.extend(batch_features or [None] * len(batch))
        except Exception as e:
            logger.warning(f"Batch {i//batch_size} failed: {e}")
            features.extend([None] * len(batch))

    return features
```

**Економія:** Замість N запитів → N/100 запитів

---

### 4. **Кешування результатів**

**Стратегія кешування:**

```python
from functools import lru_cache
from typing import Tuple
import hashlib
import json

class SpotifyService:
    def __init__(self):
        # ... existing code ...
        self._cache = {}  # In-memory cache
        self._cache_ttl = 3600  # 1 hour

    def _get_cache_key(
        self,
        seed_genres: List[str],
        min_tempo: int,
        max_tempo: int,
        target_energy: float
    ) -> str:
        """Generate cache key from parameters."""
        key_data = {
            "genres": sorted(seed_genres),
            "min_tempo": min_tempo,
            "max_tempo": max_tempo,
            "target_energy": target_energy
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def get_recommendations_cached(
        self,
        seed_genres: List[str],
        min_tempo: int,
        max_tempo: int,
        target_energy: float,
        limit: int = 20,
    ) -> List[Dict]:
        """Get recommendations with caching."""
        cache_key = self._get_cache_key(
            seed_genres, min_tempo, max_tempo, target_energy
        )

        # Check cache
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_data[:limit]

        # Fetch from API
        results = await self.get_recommendations(
            seed_genres=seed_genres,
            seed_artists=[],
            target_tempo=(min_tempo + max_tempo) // 2,
            min_tempo=min_tempo,
            max_tempo=max_tempo,
            target_energy=target_energy,
            limit=limit * 2  # Get more for cache
        )

        # Store in cache
        self._cache[cache_key] = (results, time.time())

        return results[:limit]
```

**Переваги:**

- ✅ Зменшує кількість запитів до Spotify API
- ✅ Швидший відгук для повторних запитів
- ✅ Менше навантаження на API

---

### 5. **Оптимізація пошуку треків**

**Поточна проблема:** Багато окремих запитів для кожного сегменту

**Оптимальне рішення:** Паралельні запити + batch обробка

```python
async def _fetch_candidates_optimized(
    self,
    segments: List[Dict],
    user_prefs: Dict,
    prompt: Optional[str] = None,
    user_token: Optional[str] = None
) -> List[Track]:
    """
    Оптимізований метод отримання кандидатів.

    Strategy:
    1. Паралельні запити для всіх сегментів
    2. Batch запити для audio features
    3. Кешування результатів
    """
    # 1. Паралельні запити для всіх сегментів
    tasks = [
        self._fetch_for_segment_optimized(
            segment, user_prefs, prompt, user_token
        )
        for segment in segments
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 2. Збираємо всі треки
    all_tracks = []
    all_track_ids = set()

    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Segment fetch failed: {result}")
            continue

        for track in result:
            track_id = track.spotify_id
            if track_id and track_id not in all_track_ids:
                all_tracks.append(track)
                all_track_ids.add(track_id)

    # 3. Batch запит для audio features (якщо потрібно)
    if all_tracks and not all_tracks[0].tempo:
        track_ids = [t.spotify_id for t in all_tracks if t.spotify_id]
        features = await self.spotify.get_audio_features_batch_optimized(
            track_ids
        )
        # Merge features with tracks
        for i, track in enumerate(all_tracks):
            if i < len(features) and features[i]:
                track.tempo = features[i].get("tempo", 0)
                track.energy = features[i].get("energy", 0)

    return all_tracks
```

---

### 6. **Використання seed_tracks замість seed_genres**

**Чому seed_tracks краще:**

- ✅ Більш точні рекомендації
- ✅ Працює з Client Credentials
- ✅ Менше залежить від жанрів

**Оптимальна стратегія:**

```python
async def _get_seed_tracks_from_genres(
    self,
    sp: spotipy.Spotify,
    genres: List[str],
    limit_per_genre: int = 5
) -> List[str]:
    """
    Отримати seed tracks з жанрів.

    Strategy:
    1. Пошук популярних треків за жанром
    2. Використання їх як seed для Recommendations API
    """
    seed_tracks = []

    for genre in genres[:2]:
        try:
            # Пошук популярних треків за жанром
            search_results = sp.search(
                q=f"genre:{genre}",
                type="track",
                limit=limit_per_genre,
                market="US"
            )
            tracks = search_results.get("tracks", {}).get("items", [])
            for track in tracks:
                if track.get("id"):
                    seed_tracks.append(track["id"])
        except Exception as e:
            logger.warning(f"Failed to get seed tracks for {genre}: {e}")
            continue

    return seed_tracks[:5]  # Max 5 seeds
```

---

## 🚀 Рекомендована архітектура

### Варіант 1: Покращена поточна реалізація (Рекомендовано)

**Зміни:**

1. ✅ Додати User Authorization для Recommendations API
2. ✅ Оптимізувати batch запити для audio features
3. ✅ Додати кешування результатів
4. ✅ Покращити fallback стратегію

**Переваги:**

- Мінімальні зміни в коді
- Швидка реалізація
- Покращення продуктивності на 50-70%

---

### Варіант 2: MCP сервер для Spotify API

**Що таке MCP:**

- Model Context Protocol - стандартизований протокол для інтеграції з AI
- Дозволяє централізоване управління запитами
- Підтримка кешування та rate limiting

**Архітектура:**

```
┌─────────────────┐
│  Frontend       │
└────────┬────────┘
         │
┌────────▼────────┐
│  Backend API    │
└────────┬────────┘
         │
┌────────▼────────┐      ┌──────────────────┐
│  MCP Server     │◄────►│  Spotify API     │
│  (Spotify)      │      │                  │
│  - Caching      │      │  - Recommendations│
│  - Rate Limit   │      │  - Search        │
│  - Batch Req     │      │  - Audio Features│
└─────────────────┘      └──────────────────┘
```

**Переваги:**

- ✅ Централізоване управління запитами
- ✅ Автоматичне кешування
- ✅ Rate limiting
- ✅ Можливість використання в інших проектах

**Недоліки:**

- ⚠️ Додаткова складність
- ⚠️ Потрібна додаткова інфраструктура

---

### Варіант 3: AI агент для оптимізації запитів

**Концепція:**
AI агент аналізує параметри воркаута та оптимізує запити до Spotify API

**Функції агента:**

1. **Аналіз параметрів воркаута** → оптимальна стратегія пошуку
2. **Передбачення потрібних треків** → попереднє кешування
3. **Оптимізація запитів** → мінімізація кількості запитів

**Приклад:**

```python
class SpotifyQueryOptimizer:
    """
    AI агент для оптимізації запитів до Spotify API.
    """

    async def optimize_query(
        self,
        workout: Workout,
        user_prefs: Dict
    ) -> Dict:
        """
        Оптимізує запити на основі параметрів воркаута.

        Returns:
            {
                "strategy": "recommendations" | "search" | "hybrid",
                "seed_tracks": [...],
                "batch_size": 100,
                "cache_key": "..."
            }
        """
        # Аналіз параметрів
        if workout.type == "steady":
            # Для стабільних тренувань - використовувати Recommendations
            strategy = "recommendations"
        elif workout.type == "intervals":
            # Для інтервальних - комбінований підхід
            strategy = "hybrid"
        else:
            strategy = "search"

        # Генерація seed tracks
        seed_tracks = await self._generate_seed_tracks(
            workout, user_prefs
        )

        return {
            "strategy": strategy,
            "seed_tracks": seed_tracks,
            "batch_size": 100,
            "cache_key": self._generate_cache_key(workout, user_prefs)
        }
```

**Переваги:**

- ✅ Адаптивна стратегія пошуку
- ✅ Оптимізація на основі контексту
- ✅ Можливість навчання на історії

**Недоліки:**

- ⚠️ Складність реалізації
- ⚠️ Потрібні додаткові ресурси

---

## 📋 План впровадження

### Етап 1: Швидкі перемоги (1-2 дні)

1. ✅ Додати User Authorization для Recommendations API
2. ✅ Оптимізувати batch запити для audio features
3. ✅ Покращити fallback стратегію

### Етап 2: Кешування (2-3 дні)

1. ✅ Додати in-memory кеш
2. ✅ Реалізувати TTL для кешу
3. ✅ Додати метрики кешування

### Етап 3: Оптимізація (3-5 днів)

1. ✅ Паралельні запити для сегментів
2. ✅ Оптимізація seed_tracks
3. ✅ Покращення обробки помилок

### Етап 4: Розширення (опціонально)

1. ⚪ MCP сервер для Spotify API
2. ⚪ AI агент для оптимізації
3. ⚪ Redis для розподіленого кешування

---

## 🎯 Очікувані результати

### До оптимізації:

- ❌ Recommendations API: 404 errors
- ❌ Search API: порожні результати
- ❌ Кількість запитів: ~20-30 на плейлист
- ❌ Час генерації: 10-15 секунд

### Після оптимізації:

- ✅ Recommendations API: працює з User Auth
- ✅ Search API: знаходить треки
- ✅ Кількість запитів: ~5-10 на плейлист (з кешем)
- ✅ Час генерації: 3-5 секунд

**Покращення продуктивності: 60-70%**

---

## 🔧 Рекомендації

### Найоптимальніший варіант:

**Гібридний підхід:**

1. **User Authorization** для Recommendations API (якщо доступний)
2. **Client Credentials** для Search API (fallback)
3. **Batch запити** для audio features
4. **In-memory кеш** для часто використовуваних запитів
5. **Паралельні запити** для сегментів

**Чому не MCP/AI агент зараз:**

- ⚠️ Додаткова складність без критичної потреби
- ⚠️ Поточна реалізація може бути оптимізована простіше
- ⚠️ MCP/AI агент має сенс при масштабуванні

**Коли розглянути MCP/AI агент:**

- 📈 При збільшенні навантаження (>1000 запитів/день)
- 📈 При потребі в розподіленому кешуванні
- 📈 При інтеграції з іншими сервісами

---

## 📚 Додаткові ресурси

- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
- [Spotify Recommendations API](https://developer.spotify.com/documentation/web-api/reference/get-recommendations)
- [Spotify Rate Limits](https://developer.spotify.com/documentation/web-api/concepts/rate-limits)
- [Model Context Protocol](https://modelcontextprotocol.io/)
