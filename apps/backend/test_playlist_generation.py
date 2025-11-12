"""
Script to test playlist generation with real Spotify API.
Usage: python test_playlist_generation.py
"""
import asyncio
import sys
import os
import time

# Fix encoding for Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

from app.services.spotify_service import SpotifyService
from app.services.playlist_generator import PlaylistGenerator
from app.models.workout import Workout


async def test_spotify_service():
    """Test SpotifyService with real API."""
    print("[TEST] Testing SpotifyService...")

    try:
        spotify = SpotifyService()

        # Test recommendations (doesn't require user auth)
        print("Fetching recommendations...")
        tracks = await spotify.get_recommendations(
            seed_genres=["pop", "rock"],
            seed_artists=[],
            target_tempo=140,
            min_tempo=130,
            max_tempo=150,
            target_energy=0.7,
            limit=5,
        )

        print(f"[OK] Got {len(tracks)} recommendations")
        if tracks:
            print(f"First track: {tracks[0].get('name', 'Unknown')} by {tracks[0].get('artists', [{}])[0].get('name', 'Unknown')}")

        return True, spotify

    except Exception as e:
        print(f"[ERROR] SpotifyService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def test_playlist_generation(spotify_service):
    """Test playlist generation."""
    print("\n[TEST] Testing PlaylistGenerator...")

    try:
        generator = PlaylistGenerator(spotify_service)

        # Create test workout
        workout = Workout(
            type="steady",
            duration_minutes=30,
            intensity="low",
            hr_zones=[110, 130],
            confidence=0.95,
            needs_clarification=False,
        )

        # User preferences
        user_prefs = {
            "top_genres": ["pop", "rock"],
            "top_artists": [],
            "avg_bpm": 145,
        }

        print(f"Generating playlist for {workout.type} workout, {workout.duration_minutes} min...")
        start_time = time.time()

        playlist = await generator.generate(workout, user_prefs)

        generation_time = time.time() - start_time

        print(f"[OK] Playlist generated successfully!")
        print(f"Total tracks: {playlist.total_tracks}")
        print(f"Total duration: {playlist.total_duration:.1f} seconds ({playlist.total_duration/60:.1f} minutes)")
        print(f"Generation time: {generation_time:.2f} seconds")

        if playlist.tracks:
            print(f"\nFirst 3 tracks:")
            for i, track in enumerate(playlist.tracks[:3], 1):
                print(f"  {i}. {track.name} - {track.artist} (BPM: {track.bpm:.0f})")

        return True

    except Exception as e:
        print(f"[ERROR] Playlist generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("=" * 50)
    print("Testing Playlist Generation")
    print("=" * 50)

    # Test SpotifyService
    spotify_ok, spotify_service = await test_spotify_service()

    if not spotify_ok:
        print("\n[ERROR] SpotifyService test failed. Check Spotify credentials.")
        sys.exit(1)

    # Test playlist generation
    playlist_ok = await test_playlist_generation(spotify_service)

    if not playlist_ok:
        print("\n[ERROR] Playlist generation test failed.")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("[SUCCESS] All tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())

