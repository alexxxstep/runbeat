"""
Simple test for Spotify API connection.
"""
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Check if credentials are set
client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")

if not client_id or not client_secret:
    print("[ERROR] Spotify credentials not found in environment variables")
    print("Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")
    exit(1)

print(f"[OK] Spotify credentials found")
print(f"Client ID: {client_id[:10]}...")

try:
    # Test client credentials
    client_credentials = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret,
    )

    sp = spotipy.Spotify(client_credentials_manager=client_credentials)

    # Test simple API call
    print("\n[TEST] Testing Spotify API connection...")
    print("Trying to get recommendations...")

    # Simple test - just one genre
    results = sp.recommendations(
        seed_genres=["pop"],
        limit=5,
    )

    tracks = results.get("tracks", [])
    print(f"[OK] Got {len(tracks)} tracks!")

    if tracks:
        print(f"\nFirst track: {tracks[0]['name']} by {tracks[0]['artists'][0]['name']}")

except Exception as e:
    print(f"[ERROR] Spotify API test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n[SUCCESS] Spotify API connection works!")

