"""
Детальні тести продуктивності для генерації варіантів плейлистів.
Виявляє bottlenecks та проблеми з швидкістю виконання.
"""
import pytest
import time
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.models.playlist import PlaylistData, Track
from app.models.workout import Workout

client = TestClient(app)


def create_mock_track(track_id: str, duration_ms: int = 200000, bpm: float = 140.0):
    """Створює mock трек для тестування."""
    return Track(
        id=track_id,
        name=f"Track {track_id}",
        artist=f"Artist {track_id}",
        artist_id=f"artist_{track_id}",
        duration_ms=duration_ms,
        spotify_url=f"https://open.spotify.com/track/{track_id}",
        spotify_uri=f"spotify:track:{track_id}",
        tempo=bpm,
        bpm=bpm,
        energy=0.8,
        danceability=0.7,
        valence=0.6,
        genres=["pop"],
    )


def create_mock_playlist_data(track_count: int, duration_per_track_ms: int = 200000):
    """Створює mock PlaylistData з заданою кількістю треків."""
    tracks = [
        create_mock_track(f"track_{i}", duration_per_track_ms, 140.0 + (i % 10))
        for i in range(track_count)
    ]
    total_duration = sum(t.duration_ms for t in tracks) / 1000
    return PlaylistData(
        tracks=tracks,
        total_duration=total_duration,
        total_tracks=track_count,
    )


@pytest.fixture
def mock_workout_short():
    """Короткий воркаут для тестування."""
    return {
        "type": "steady",
        "duration_minutes": 20,
        "intensity": "moderate",
        "hr_zones": [130, 150],
    }


@pytest.fixture
def mock_workout_medium():
    """Середній воркаут для тестування."""
    return {
        "type": "steady",
        "duration_minutes": 40,
        "intensity": "moderate",
        "hr_zones": [130, 150],
    }


@pytest.fixture
def mock_workout_long():
    """Довгий воркаут для тестування."""
    return {
        "type": "steady",
        "duration_minutes": 60,
        "intensity": "moderate",
        "hr_zones": [130, 150],
    }


@pytest.fixture
def mock_workout_intervals():
    """Інтервальний воркаут для тестування."""
    return {
        "type": "intervals",
        "duration_minutes": 30,
        "intensity": "high",
        "hr_zones": [140, 180],
        "interval_stages": [
            {"name": "warmup", "duration_minutes": 5, "hr_zone": 2, "bpm_range": [120, 140]},
            {"name": "work1", "duration_minutes": 3, "hr_zone": 4, "bpm_range": [160, 180]},
            {"name": "rest1", "duration_minutes": 2, "hr_zone": 2, "bpm_range": [120, 140]},
            {"name": "work2", "duration_minutes": 3, "hr_zone": 4, "bpm_range": [160, 180]},
            {"name": "rest2", "duration_minutes": 2, "hr_zone": 2, "bpm_range": [120, 140]},
            {"name": "work3", "duration_minutes": 3, "hr_zone": 4, "bpm_range": [160, 180]},
            {"name": "cooldown", "duration_minutes": 5, "hr_zone": 2, "bpm_range": [120, 140]},
        ],
    }


class PerformanceProfiler:
    """Профілер для вимірювання часу виконання різних частин коду."""

    def __init__(self):
        self.timings = {}
        self.start_times = {}

    def start(self, operation: str):
        """Почати вимірювання операції."""
        self.start_times[operation] = time.time()

    def end(self, operation: str):
        """Завершити вимірювання операції."""
        if operation in self.start_times:
            elapsed = time.time() - self.start_times[operation]
            if operation not in self.timings:
                self.timings[operation] = []
            self.timings[operation].append(elapsed)
            del self.start_times[operation]
            return elapsed
        return 0

    def get_total(self, operation: str) -> float:
        """Отримати загальний час для операції."""
        if operation in self.timings:
            return sum(self.timings[operation])
        return 0

    def get_average(self, operation: str) -> float:
        """Отримати середній час для операції."""
        if operation in self.timings and self.timings[operation]:
            return sum(self.timings[operation]) / len(self.timings[operation])
        return 0

    def print_report(self):
        """Вивести звіт про продуктивність."""
        print("\n" + "=" * 60)
        print("PERFORMANCE REPORT")
        print("=" * 60)
        for operation, times in sorted(self.timings.items()):
            total = sum(times)
            avg = total / len(times) if times else 0
            max_time = max(times) if times else 0
            min_time = min(times) if times else 0
            print(f"{operation}:")
            print(f"  Total: {total:.3f}s")
            print(f"  Average: {avg:.3f}s")
            print(f"  Min: {min_time:.3f}s")
            print(f"  Max: {max_time:.3f}s")
            print(f"  Calls: {len(times)}")
        print("=" * 60)


@pytest.fixture
def profiler():
    """Фікстура для профілера."""
    return PerformanceProfiler()


@patch("app.api.routes.playlists.SupabaseService")
@patch("app.api.routes.playlists.PlaylistGenerator")
def test_variants_generation_timing_short_workout(
    mock_generator,
    mock_supabase_service,
    mock_workout_short,
    profiler,
):
    """Тест часу генерації варіантів для короткого воркаута."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
        []
    )
    mock_supabase_service.return_value = mock_supabase

    # Mock generator з профілюванням
    mock_gen_instance = AsyncMock()
    call_count = {"variant1": 0, "variant2": 0}

    async def mock_generate_with_timing(*args, **kwargs):
        """Mock generate з вимірюванням часу."""
        excluded_ids = kwargs.get("excluded_track_ids") or []
        if len(excluded_ids) == 0:
            call_count["variant1"] += 1
            profiler.start("variant1_generation")
            # Симулюємо затримку генерації
            await asyncio.sleep(0.1)
            profiler.end("variant1_generation")
        else:
            call_count["variant2"] += 1
            profiler.start("variant2_generation")
            # Симулюємо затримку генерації
            await asyncio.sleep(0.1)
            profiler.end("variant2_generation")

        # Повертаємо різні треки для variant 2
        if len(excluded_ids) > 0:
            # Variant 2 - інші треки
            return create_mock_playlist_data(15, 200000)
        else:
            # Variant 1
            return create_mock_playlist_data(15, 200000)

    mock_gen_instance.generate = AsyncMock(side_effect=mock_generate_with_timing)
    mock_generator.return_value = mock_gen_instance

    # Вимірюємо загальний час
    profiler.start("total_request")
    response = client.post(
        "/playlists/preview-variants",
        json={
            "workout": mock_workout_short,
            "user_preferences": {"top_genres": ["pop", "rock"]},
            "user_id": "user_uuid",
        },
    )
    profiler.end("total_request")

    assert response.status_code == 200
    data = response.json()
    assert "variant1" in data
    assert "variant2" in data

    # Перевіряємо, що обидва варіанти були згенеровані
    assert call_count["variant1"] >= 1
    assert call_count["variant2"] >= 1

    profiler.print_report()

    # Перевіряємо, що загальний час не перевищує розумні межі
    total_time = profiler.get_total("total_request")
    print(f"\nTotal request time: {total_time:.3f}s")
    assert total_time < 5.0, f"Total time {total_time:.3f}s is too slow!"


@patch("app.api.routes.playlists.SupabaseService")
@patch("app.api.routes.playlists.PlaylistGenerator")
def test_variants_generation_timing_with_excluded_tracks(
    mock_generator,
    mock_supabase_service,
    mock_workout_medium,
    profiler,
):
    """Тест часу генерації варіантів з виключеними треками."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
        []
    )
    mock_supabase_service.return_value = mock_supabase

    # Mock generator
    mock_gen_instance = AsyncMock()
    call_count = {"variant1": 0, "variant2": 0, "retries": 0}

    async def mock_generate_with_timing(*args, **kwargs):
        """Mock generate з вимірюванням часу."""
        excluded_ids = kwargs.get("excluded_track_ids", [])

        if len(excluded_ids) == 0:
            call_count["variant1"] += 1
            profiler.start("variant1_generation")
            await asyncio.sleep(0.1)
            profiler.end("variant1_generation")
            return create_mock_playlist_data(20, 200000)
        else:
            call_count["variant2"] += 1
            profiler.start("variant2_generation")
            await asyncio.sleep(0.1)
            profiler.end("variant2_generation")

            # Симулюємо можливі retry
            if call_count["variant2"] == 1 and len(excluded_ids) > 10:
                # Перша спроба може не знайти достатньо треків
                call_count["retries"] += 1
                profiler.start("variant2_retry")
                await asyncio.sleep(0.05)
                profiler.end("variant2_retry")

            return create_mock_playlist_data(20, 200000)

    mock_gen_instance.generate = AsyncMock(side_effect=mock_generate_with_timing)
    mock_generator.return_value = mock_gen_instance

    # Генеруємо з багатьма виключеними треками
    excluded_tracks = [f"excluded_{i}" for i in range(30)]

    profiler.start("total_request")
    response = client.post(
        "/playlists/preview-variants",
        json={
            "workout": mock_workout_medium,
            "user_preferences": {"top_genres": ["pop", "rock"]},
            "user_id": "user_uuid",
            "excluded_track_ids": excluded_tracks,
        },
    )
    profiler.end("total_request")

    assert response.status_code == 200
    data = response.json()
    assert "variant1" in data
    assert "variant2" in data

    profiler.print_report()

    total_time = profiler.get_total("total_request")
    print(f"\nTotal request time with {len(excluded_tracks)} excluded tracks: {total_time:.3f}s")
    assert total_time < 10.0, f"Total time {total_time:.3f}s is too slow with excluded tracks!"


@patch("app.api.routes.playlists.SupabaseService")
@patch("app.api.routes.playlists.PlaylistGenerator")
def test_variants_generation_sequential_vs_parallel(
    mock_generator,
    mock_supabase_service,
    mock_workout_medium,
    profiler,
):
    """Тест для виявлення, чи варіанти генеруються послідовно чи паралельно."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
        []
    )
    mock_supabase_service.return_value = mock_supabase

    # Mock generator з точковим вимірюванням часу
    mock_gen_instance = AsyncMock()
    generation_times = []

    async def mock_generate_with_timing(*args, **kwargs):
        """Mock generate з точковим вимірюванням часу."""
        start = time.time()
        excluded_ids = kwargs.get("excluded_track_ids") or []

        # Симулюємо реальну затримку генерації (1 секунда)
        await asyncio.sleep(1.0)

        end = time.time()
        generation_times.append({
            "start": start,
            "end": end,
            "duration": end - start,
            "excluded_count": len(excluded_ids),
        })

        return create_mock_playlist_data(20, 200000)

    mock_gen_instance.generate = AsyncMock(side_effect=mock_generate_with_timing)
    mock_generator.return_value = mock_gen_instance

    profiler.start("total_request")
    response = client.post(
        "/playlists/preview-variants",
        json={
            "workout": mock_workout_medium,
            "user_preferences": {"top_genres": ["pop"]},
            "user_id": "user_uuid",
        },
    )
    profiler.end("total_request")

    assert response.status_code == 200

    # Аналізуємо, чи генерації були послідовними
    if len(generation_times) >= 2:
        variant1_time = generation_times[0]
        variant2_time = generation_times[1]

        # Якщо variant2 почався після завершення variant1 - це послідовна генерація
        sequential = variant2_time["start"] >= variant1_time["end"]

        # Якщо variant2 почався до завершення variant1 - це паралельна генерація
        parallel = variant2_time["start"] < variant1_time["end"]

        total_sequential_time = variant1_time["duration"] + variant2_time["duration"]
        actual_total_time = max(g["end"] for g in generation_times) - min(g["start"] for g in generation_times)

        print(f"\nGeneration analysis:")
        print(f"  Variant 1: {variant1_time['duration']:.3f}s")
        print(f"  Variant 2: {variant2_time['duration']:.3f}s")
        print(f"  Sequential time: {total_sequential_time:.3f}s")
        print(f"  Actual total time: {actual_total_time:.3f}s")
        print(f"  Sequential: {sequential}")
        print(f"  Parallel: {parallel}")

        if sequential:
            print(f"  ⚠️  WARNING: Variants are generated SEQUENTIALLY!")
            print(f"  ⚠️  This is a performance bottleneck!")
            print(f"  ⚠️  Consider parallelizing variant generation.")
        else:
            print(f"  ✅ Variants are generated in parallel (or overlapping)")


@patch("app.api.routes.playlists.SupabaseService")
@patch("app.api.routes.playlists.PlaylistGenerator")
def test_variants_generation_with_retries(
    mock_generator,
    mock_supabase_service,
    mock_workout_medium,
    profiler,
):
    """Тест для виявлення проблем з retry логікою."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
        []
    )
    mock_supabase_service.return_value = mock_supabase

    # Mock generator з симуляцією retry
    mock_gen_instance = AsyncMock()
    call_sequence = []

    async def mock_generate_with_retries(*args, **kwargs):
        """Mock generate з симуляцією retry."""
        excluded_ids = kwargs.get("excluded_track_ids") or []
        call_num = len(call_sequence) + 1

        call_sequence.append({
            "call": call_num,
            "excluded_count": len(excluded_ids),
            "timestamp": time.time(),
        })

        # Симулюємо затримку
        await asyncio.sleep(0.5)

        # Симулюємо, що перша спроба variant 2 повертає порожній результат
        if len(excluded_ids) > 0 and call_num == 2:
            # Перша спроба variant 2 - повертаємо порожній плейлист
            return create_mock_playlist_data(0, 200000)
        elif len(excluded_ids) > 0 and call_num == 3:
            # Retry variant 2 - повертаємо нормальний плейлист
            return create_mock_playlist_data(20, 200000)
        else:
            # Variant 1 або успішний variant 2
            return create_mock_playlist_data(20, 200000)

    mock_gen_instance.generate = AsyncMock(side_effect=mock_generate_with_retries)
    mock_generator.return_value = mock_gen_instance

    profiler.start("total_request")
    response = client.post(
        "/playlists/preview-variants",
        json={
            "workout": mock_workout_medium,
            "user_preferences": {"top_genres": ["pop"]},
            "user_id": "user_uuid",
            "excluded_track_ids": [f"excluded_{i}" for i in range(20)],
        },
    )
    profiler.end("total_request")

    assert response.status_code == 200

    print(f"\nCall sequence analysis:")
    for i, call in enumerate(call_sequence):
        print(f"  Call {i+1}: excluded_count={call['excluded_count']}, time={call['timestamp']:.3f}")

    # Перевіряємо, скільки разів викликався generator
    print(f"\nTotal generator calls: {len(call_sequence)}")
    if len(call_sequence) > 2:
        print(f"  ⚠️  WARNING: More than 2 calls detected - retry logic is active")
        print(f"  ⚠️  This may cause performance issues")

    total_time = profiler.get_total("total_request")
    print(f"\nTotal request time: {total_time:.3f}s")


@patch("app.api.routes.playlists.SupabaseService")
@patch("app.api.routes.playlists.PlaylistGenerator")
def test_variants_generation_long_workout(
    mock_generator,
    mock_supabase_service,
    mock_workout_long,
    profiler,
):
    """Тест для довгого воркаута - перевірка timeout."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
        []
    )
    mock_supabase_service.return_value = mock_supabase

    # Mock generator з довгою затримкою
    mock_gen_instance = AsyncMock()

    async def mock_generate_slow(*args, **kwargs):
        """Mock generate з довгою затримкою."""
        # Симулюємо повільну генерацію (2 секунди на варіант)
        await asyncio.sleep(2.0)
        return create_mock_playlist_data(30, 200000)

    mock_gen_instance.generate = AsyncMock(side_effect=mock_generate_slow)
    mock_generator.return_value = mock_gen_instance

    profiler.start("total_request")
    response = client.post(
        "/playlists/preview-variants",
        json={
            "workout": mock_workout_long,
            "user_preferences": {"top_genres": ["pop"]},
            "user_id": "user_uuid",
        },
    )
    profiler.end("total_request")

    total_time = profiler.get_total("total_request")
    print(f"\nLong workout (60 min) generation time: {total_time:.3f}s")

    # Для 60-хвилинного воркаута timeout = max(180, min(300, 60 * 2.5)) = 180 секунд
    expected_timeout = max(180.0, min(300.0, 60 * 2.5))
    print(f"Expected timeout: {expected_timeout}s")

    if response.status_code == 504:
        print(f"  ⚠️  Request timed out (expected for slow generation)")
    else:
        assert response.status_code == 200
        assert total_time < expected_timeout, f"Generation took {total_time:.3f}s, timeout is {expected_timeout}s"


@patch("app.api.routes.playlists.SupabaseService")
@patch("app.api.routes.playlists.PlaylistGenerator")
def test_variants_generation_intervals_workout(
    mock_generator,
    mock_supabase_service,
    mock_workout_intervals,
    profiler,
):
    """Тест для інтервального воркаута - багато сегментів."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
        []
    )
    mock_supabase_service.return_value = mock_supabase

    # Mock generator
    mock_gen_instance = AsyncMock()
    segment_fetch_count = {"count": 0}

    async def mock_generate_with_segments(*args, **kwargs):
        """Mock generate з підрахунком сегментів."""
        # Симулюємо, що для кожного сегменту робиться запит
        # Для інтервального воркаута з 7 сегментами це 7 запитів
        segment_fetch_count["count"] += 7
        await asyncio.sleep(0.1 * 7)  # 0.1s на сегмент
        return create_mock_playlist_data(25, 200000)

    mock_gen_instance.generate = AsyncMock(side_effect=mock_generate_with_segments)
    mock_generator.return_value = mock_gen_instance

    profiler.start("total_request")
    response = client.post(
        "/playlists/preview-variants",
        json={
            "workout": mock_workout_intervals,
            "user_preferences": {"top_genres": ["pop", "rock"]},
            "user_id": "user_uuid",
        },
    )
    profiler.end("total_request")

    assert response.status_code == 200

    total_time = profiler.get_total("total_request")
    print(f"\nIntervals workout generation time: {total_time:.3f}s")
    print(f"Segment fetch operations: {segment_fetch_count['count']}")

    # Для інтервального воркаута з багатьма сегментами час може бути більшим
    # Але все одно не повинен перевищувати розумні межі
    assert total_time < 30.0, f"Intervals workout took too long: {total_time:.3f}s"


def test_playlist_generator_fetch_candidates_performance():
    """Тест продуктивності _fetch_candidates методу."""
    from app.services.playlist_generator import PlaylistGenerator
    from app.services.spotify_service import SpotifyService
    from unittest.mock import AsyncMock, MagicMock

    # Mock Spotify service
    mock_spotify = MagicMock(spec=SpotifyService)

    # Mock get_recommendations_optimized
    async def mock_recommendations(*args, **kwargs):
        """Mock рекомендацій з затримкою."""
        await asyncio.sleep(0.1)  # Симулюємо затримку API
        return [
            {
                "id": f"track_{i}",
                "name": f"Track {i}",
                "artists": [{"name": f"Artist {i}", "id": f"artist_{i}"}],
                "duration_ms": 200000,
                "external_urls": {"spotify": f"https://open.spotify.com/track/track_{i}"},
                "uri": f"spotify:track:track_{i}",
                "tempo": 140.0 + i,
                "energy": 0.8,
                "danceability": 0.7,
                "valence": 0.6,
            }
            for i in range(50)
        ]

    mock_spotify.get_recommendations_optimized = AsyncMock(side_effect=mock_recommendations)
    mock_spotify.get_tracks_by_search_optimized = AsyncMock(return_value=[])

    generator = PlaylistGenerator(mock_spotify)

    # Створюємо сегменти (наприклад, для інтервального воркаута)
    segments = [
        {"name": f"segment_{i}", "duration": 5, "bpm_range": [130 + i*5, 150 + i*5]}
        for i in range(7)
    ]

    user_prefs = {"top_genres": ["pop", "rock"]}

    # Вимірюємо час
    start = time.time()
    candidates = asyncio.run(generator._fetch_candidates(segments, user_prefs))
    elapsed = time.time() - start

    print(f"\n_fetch_candidates performance:")
    print(f"  Segments: {len(segments)}")
    print(f"  Candidates fetched: {len(candidates)}")
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Time per segment: {elapsed/len(segments):.3f}s")

    # Перевіряємо, що запити виконуються паралельно
    # Якщо паралельно, час має бути близький до часу одного запиту
    # Якщо послідовно, час має бути близький до часу одного запиту * кількість сегментів
    expected_parallel_time = 0.1  # Час одного запиту
    expected_sequential_time = 0.1 * len(segments)  # Час одного запиту * кількість

    print(f"  Expected parallel time: ~{expected_parallel_time:.3f}s")
    print(f"  Expected sequential time: ~{expected_sequential_time:.3f}s")

    if elapsed < expected_sequential_time * 0.5:
        print(f"  ✅ Requests are likely parallelized")
    else:
        print(f"  ⚠️  WARNING: Requests may be sequential (took {elapsed:.3f}s)")

    assert len(candidates) > 0, "Should fetch some candidates"


if __name__ == "__main__":
    # Запуск тестів з детальним виводом
    pytest.main([__file__, "-v", "-s"])

