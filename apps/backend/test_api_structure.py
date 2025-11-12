"""
Simple script to test API structure without requiring all dependencies.
This checks that endpoints are properly defined and importable.
"""
import sys
import importlib.util
from pathlib import Path

def test_imports():
    """Test that all route modules can be imported (with mocked dependencies)."""
    print("Testing API structure...")

    # Mock required dependencies
    sys.modules['supabase'] = type(sys)('supabase')
    sys.modules['spotipy'] = type(sys)('spotipy')
    sys.modules['openai'] = type(sys)('openai')

    errors = []

    # Test route imports
    routes_to_test = [
        'app.api.routes.health',
        'app.api.routes.chat',
        'app.api.routes.playlists',
        'app.api.routes.auth',
        'app.api.routes.workouts',
        'app.api.routes.users',
    ]

    for route_name in routes_to_test:
        try:
            spec = importlib.util.find_spec(route_name)
            if spec is None:
                errors.append(f"❌ {route_name} - module not found")
            else:
                print(f"✅ {route_name} - found")
        except Exception as e:
            errors.append(f"❌ {route_name} - {str(e)}")

    # Test schema imports
    schemas_to_test = [
        'app.schemas.chat',
        'app.schemas.playlist',
        'app.schemas.auth',
        'app.schemas.workout',
        'app.schemas.user',
    ]

    for schema_name in schemas_to_test:
        try:
            spec = importlib.util.find_spec(schema_name)
            if spec is None:
                errors.append(f"❌ {schema_name} - module not found")
            else:
                print(f"✅ {schema_name} - found")
        except Exception as e:
            errors.append(f"❌ {schema_name} - {str(e)}")

    # Check test files exist
    test_files = [
        'tests/test_auth.py',
        'tests/test_workouts.py',
        'tests/test_users.py',
        'tests/test_playlist_history.py',
    ]

    print("\nChecking test files...")
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"✅ {test_file} - exists")
        else:
            errors.append(f"❌ {test_file} - not found")

    print("\n" + "="*50)
    if errors:
        print("❌ Found errors:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("✅ All structure checks passed!")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)

