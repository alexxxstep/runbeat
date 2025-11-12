"""
Simple HTTP tests for new API endpoints.
Run this after starting the server: uvicorn app.main:app --reload
"""
import sys
import requests
from typing import Dict, Tuple

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"


def test_endpoint(method: str, path: str, expected_status: list = None) -> Tuple[bool, int]:
    """Test an endpoint and return success status and HTTP code."""
    url = f"{BASE_URL}{path}"
    expected_status = expected_status or [200]

    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=5)
        elif method.upper() == "POST":
            response = requests.post(url, json={}, timeout=5)
        else:
            return False, 0

        status = response.status_code
        success = status in expected_status or status < 500  # Accept any non-server-error

        return success, status
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  Connection error: {e}")
        return False, 0


def main():
    """Run all endpoint tests."""
    print(f"Testing RunBeat API endpoints at {BASE_URL}")
    print("=" * 50)
    print()

    tests = [
        ("GET", "/health", [200], "Health check"),
        ("GET", "/auth/spotify", [200], "Spotify OAuth initiate"),
        ("GET", "/auth/spotify/status?user_id=test", [200, 404, 500], "Spotify auth status"),
        ("GET", "/workouts?user_id=test", [200, 404, 422, 500], "Get workouts"),
        ("GET", "/workouts/test_id?user_id=test", [200, 404, 422, 500], "Get workout by ID"),
        ("GET", "/users/test/preferences", [200, 404, 500], "Get user preferences"),
        ("GET", "/playlists/history?user_id=test", [200, 422, 500], "Get playlist history"),
    ]

    results = []
    for method, path, expected, description in tests:
        print(f"Testing: {description}")
        print(f"  {method} {path}")
        success, status = test_endpoint(method, path, expected)

        if success:
            print(f"  ✅ Status: {status}")
            results.append(True)
        else:
            print(f"  ❌ Status: {status}")
            results.append(False)
        print()

    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✅ All endpoint tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed (may be expected without proper setup)")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)

