# RunBeat API Documentation

**Base URL:** `https://your-railway-domain.up.railway.app` (production)
**Local URL:** `http://localhost:8000` (development)

## Authentication

RunBeat API використовує Spotify OAuth для автентифікації користувачів.

### Initiate Spotify OAuth

```http
GET /auth/spotify
```

**Response:**
```json
{
  "auth_url": "https://accounts.spotify.com/authorize?...",
  "state": "random_state_string"
}
```

### Spotify OAuth Callback

```http
GET /auth/spotify/callback?code={code}&state={state}
```

**Response:** Redirects to frontend success/error page

### Check Auth Status

```http
GET /auth/spotify/status?user_id={user_id}
```

**Response:**
```json
{
  "authenticated": true,
  "spotify_user_id": "spotify_user_123",
  "expires_at": "2025-12-12T10:00:00Z",
  "is_expired": false
}
```

---

## Chat Endpoints

### Send Message

```http
POST /chat/message
Content-Type: application/json

{
  "message": "Хочу пробігти 40 хв з інтервалами",
  "user_id": "optional_user_id"
}
```

**Response:**
```json
{
  "message": "Зрозумів! Генерую плейлист на 40 хв...",
  "workout": {
    "type": "intervals",
    "duration_minutes": 40,
    "intensity": "moderate",
    "hr_zones": [130, 180],
    "confidence": 0.8,
    "needs_clarification": false
  },
  "needs_clarification": false
}
```

**Clarification Response:**
```json
{
  "message": "Який буде інтервал роботи/відпочинку?",
  "workout": null,
  "needs_clarification": true
}
```

---

## Playlist Endpoints

### Generate Playlist

```http
POST /playlists/generate
Content-Type: application/json

{
  "workout": {
    "type": "steady",
    "duration_minutes": 30,
    "intensity": "low",
    "hr_zones": [110, 130]
  },
  "user_preferences": {
    "top_genres": ["pop", "rock"],
    "top_artists": ["artist_id_1"],
    "avg_bpm": 145
  }
}
```

**Response:**
```json
{
  "playlist_id": null,
  "spotify_url": null,
  "tracks": [
    {
      "id": "track_id",
      "name": "Song Name",
      "artist": "Artist Name",
      "bpm": 120.0,
      "energy": 0.8,
      "duration_ms": 200000,
      "spotify_url": "https://open.spotify.com/track/..."
    }
  ],
  "total_duration": 1800.0,
  "total_tracks": 15,
  "generation_time_seconds": 8.5
}
```

### Get Playlist History

```http
GET /playlists/history?user_id={user_id}&limit=10&offset=0
```

**Response:**
```json
{
  "playlists": [
    {
      "id": "playlist_uuid",
      "workout_id": "workout_uuid",
      "spotify_playlist_id": "spotify_playlist_123",
      "spotify_url": "https://open.spotify.com/playlist/...",
      "total_tracks": 15,
      "total_duration_seconds": 1800,
      "generation_time_seconds": 8.5,
      "created_at": "2025-11-12T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

## Workout Endpoints

### Create Workout

```http
POST /workouts
Content-Type: application/json

{
  "workout": {
    "type": "steady",
    "duration_minutes": 30,
    "intensity": "low",
    "hr_zones": [110, 130]
  },
  "user_id": "user_uuid"
}
```

**Response:**
```json
{
  "id": "workout_uuid",
  "user_id": "user_uuid",
  "type": "steady",
  "duration_minutes": 30,
  "intensity": "low",
  "hr_zones": [110, 130],
  "completed_at": null,
  "created_at": "2025-11-12T10:00:00Z"
}
```

### Get Workouts

```http
GET /workouts?user_id={user_id}&limit=10&offset=0
```

**Response:**
```json
{
  "workouts": [
    {
      "id": "workout_uuid",
      "user_id": "user_uuid",
      "type": "steady",
      "duration_minutes": 30,
      "intensity": "low",
      "hr_zones": [110, 130],
      "completed_at": null,
      "created_at": "2025-11-12T10:00:00Z"
    }
  ],
  "total": 1
}
```

### Get Workout by ID

```http
GET /workouts/{workout_id}?user_id={user_id}
```

### Delete Workout

```http
DELETE /workouts/{workout_id}?user_id={user_id}
```

**Response:** `204 No Content`

### Complete Workout

```http
PATCH /workouts/{workout_id}/complete?user_id={user_id}
```

**Response:**
```json
{
  "id": "workout_uuid",
  "completed_at": "2025-11-12T11:00:00Z",
  ...
}
```

---

## User Endpoints

### Get User Preferences

```http
GET /users/{user_id}/preferences
```

**Response:**
```json
{
  "user_id": "user_uuid",
  "preferences": {
    "top_genres": ["pop", "rock"],
    "top_artists": ["artist_id_1", "artist_id_2"],
    "avg_bpm": 145
  }
}
```

### Update User Preferences

```http
PUT /users/{user_id}/preferences
Content-Type: application/json

{
  "preferences": {
    "top_genres": ["pop", "rock", "electronic"],
    "top_artists": ["artist_id_1"],
    "avg_bpm": 150
  }
}
```

**Response:** Same as Get User Preferences

---

## Analytics Endpoints

### Get Conversation Insights

```http
GET /analytics/conversation-insights?days=30
```

**Response:**
```json
{
  "success": true,
  "insights": {
    "total_analyzed": 150,
    "completion_rate": 82.5,
    "abandonment_rate": 12.3,
    "most_common_genres": {
      "electronic": 45,
      "rock": 38,
      "pop": 32
    },
    "average_messages_per_conversation": 6.2
  }
}
```

### Get User Patterns

```http
GET /analytics/user-patterns/{user_id}
```

**Response:**
```json
{
  "success": true,
  "user_id": "user_uuid",
  "patterns": {
    "has_history": true,
    "total_conversations": 25,
    "favorite_genres": ["electronic", "rock", "pop"],
    "typical_duration": 45,
    "preferred_type": "fartlek",
    "common_intensity": "moderate"
  }
}
```

### Get Recommendations

```http
GET /analytics/recommendations?days=30
```

**Response:**
```json
{
  "success": true,
  "insights": {
    "total_analyzed": 150,
    "completion_rate": 82.5,
    "abandonment_rate": 12.3
  },
  "recommendations": [
    {
      "type": "healthy",
      "severity": "success",
      "message": "Conversation flow is healthy! Keep up the good work."
    },
    {
      "type": "popular_genres",
      "severity": "info",
      "message": "Most popular genres: electronic, rock, pop. Ensure these are well-supported."
    }
  ],
  "analyzed_days": 30
}
```

---

## Error Logging Endpoints

### Log Error

```http
POST /error-logs/
Content-Type: application/json

{
  "level": "ERROR",
  "message": "Failed to generate playlist",
  "error_type": "ValueError",
  "error_details": {},
  "stack_trace": "...",
  "user_id": "user_uuid",
  "request_path": "/api/v1/playlists/generate",
  "request_method": "POST",
  "request_body": {},
  "response_status": 500
}
```

### Get Error Logs

```http
GET /error-logs/?level=ERROR&limit=100&offset=0
```

### Get Error Statistics

```http
GET /error-logs/statistics?days=7
```

---

## Health Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "runbeat-api",
  "timestamp": "2025-11-12T10:00:00Z"
}
```

### Readiness Check

```http
GET /health/ready
```

### Liveness Check

```http
GET /health/live
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error message"
}
```

---

## Rate Limiting

Currently, there are no rate limits implemented. This will be added in future versions.

---

## API Versioning

Current API version: `3.3.0`

All API endpoints are prefixed with `/api/v1/` in the current implementation.

---

## Interactive API Documentation

When running in development mode, visit:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

These provide interactive documentation with the ability to test endpoints directly.

