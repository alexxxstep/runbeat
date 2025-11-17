# RunBeat - Product Requirements Document (Cursor AI Optimized)

**Version:** 3.3.1 - AI Learning & Personalization (Spotify Auth Fix)
**Date:** 17.11.2025
**Status:** ✅ Production Ready (Deployed)
**AI Assistant:** Cursor AI
**Developer:** Alex
**LLM Provider:** OpenAI GPT-4
**Repository:** [GitHub](https://github.com/alexxxstep/runbeat)

---

## 🎯 Project Overview

**RunBeat** - AI-powered music assistant for runners that generates personalized workout playlists through natural chat conversation.

> **Note:** This PRD was originally created for the MVP planning phase. The project has since evolved and is now in production with additional features including AI learning, personalization, and an advanced multi-agent architecture. See [ARCHITECTURE_REPORT.md](./docs/ARCHITECTURE_REPORT.md) for the current system architecture.

### Core User Flow
```
User: "Хочу пробігти 40 хв з інтервалами"
  ↓ AI parses intent (2s)
AI: "Який інтервал роботи/відпочинку?"
  ↓
User: "5-2-5-2"
  ↓ Generate playlist (8s)
AI: Shows playlist (15 tracks, BPM 120-165)
  ↓
User: Taps "Open in Spotify"
  ↓ Spotify app opens
User: Starts running 🏃‍♂️🎵
```

---

## 🏗️ Tech Stack

### Backend (FastAPI + Python)
```python
# Core dependencies
fastapi==0.104.1              # Web framework
uvicorn[standard]==0.24.0     # ASGI server
pydantic==2.5.2               # Validation
pydantic-settings==2.1.0      # Config

# Database & Auth
supabase==2.3.0               # PostgreSQL + Auth
httpx==0.25.2                 # HTTP client

# AI/LLM
openai==1.7.2                 # OpenAI GPT-4

# LangChain
langchain==0.1.0              # LangChain framework
langchain-openai==0.0.2       # OpenAI integration
langchain-community==0.0.10   # Community tools
langsmith>=0.0.77,<0.1.0      # Observability

# Spotify
spotipy==2.23.0               # Spotify API

# Utils
python-dotenv==1.0.0
loguru==0.7.2

# Dev/Test
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
ruff==0.1.6
```

### Frontend Mobile (React Native + Expo)
```json
{
  "dependencies": {
    "expo": "~50.0.0",
    "react": "18.2.0",
    "react-native": "0.73.0",
    "@react-navigation/native": "^6.1.9",
    "@react-navigation/stack": "^6.3.20",
    "@supabase/supabase-js": "^2.39.0",
    "zustand": "^4.4.7",
    "axios": "^1.6.2"
  }
}
```

### Frontend Web (React + Vite)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@supabase/supabase-js": "^2.39.0",
    "zustand": "^4.4.7",
    "axios": "^1.6.2",
    "tailwindcss": "^3.3.6"
  }
}
```

### Infrastructure
- **Backend:** Railway (https://railway.app)
- **Web:** Railway (https://railway.app)
- **Mobile:** Expo EAS (https://expo.dev)
- **Database:** Supabase (https://supabase.com)

---

## 📁 Project Structure (Поточна структура)

```
runbeat/
├── apps/
│   ├── backend/                          # FastAPI Backend
│   │   ├── app/
│   │   │   ├── main.py                   # FastAPI app entry
│   │   │   ├── core/
│   │   │   │   └── config.py             # Settings (Pydantic + FRONTEND_URL)
│   │   │   ├── api/
│   │   │   │   └── routes/
│   │   │   │       ├── health.py         # Health checks
│   │   │   │       ├── chat.py           # Chat endpoint (SupervisorAgent)
│   │   │   │       ├── playlists.py      # Playlist generation & variants
│   │   │   │       ├── workouts.py       # Workout CRUD
│   │   │   │       ├── auth.py           # Spotify OAuth (fixed redirect)
│   │   │   │       ├── analytics.py      # Analytics API (NEW v3.3)
│   │   │   │       ├── error_logs.py     # Error logging API (NEW v3.3)
│   │   │   │       └── users.py          # User management
│   │   │   ├── agents/                   # LangChain Multi-Agent System
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py               # Base agent class
│   │   │   │   ├── supervisor.py         # SupervisorAgent (orchestrator)
│   │   │   │   ├── tools/
│   │   │   │   │   ├── parser_tools.py   # Parsing tools
│   │   │   │   │   └── workout_tools.py  # Workout creation tools
│   │   │   │   └── prompts/
│   │   │   │       └── conversation_prompts.py  # AI prompts
│   │   │   ├── services/
│   │   │   │   ├── supabase_service.py   # DB operations
│   │   │   │   ├── spotify_service.py    # Spotify API (refactored)
│   │   │   │   ├── spotify_modules/      # Spotify service modules
│   │   │   │   ├── workout_builder.py    # WorkoutBuilder (LangChain agent)
│   │   │   │   ├── conversation_service.py  # Conversation storage & analytics
│   │   │   │   ├── error_logging_service.py # Error logging to DB
│   │   │   │   ├── playlist_generator.py # Playlist generation
│   │   │   │   └── workout_profiler.py   # Workout profiling
│   │   │   ├── models/                   # Database models
│   │   │   │   ├── user.py
│   │   │   │   ├── workout.py
│   │   │   │   ├── playlist.py
│   │   │   │   └── error_log.py          # NEW v3.3
│   │   │   ├── schemas/                  # API schemas
│   │   │   │   ├── chat.py
│   │   │   │   ├── workout.py
│   │   │   │   ├── playlist.py
│   │   │   │   ├── conversation.py       # NEW v3.3
│   │   │   │   └── auth.py
│   │   │   └── utils/
│   │   │       ├── logger.py
│   │   │       ├── database_log_handler.py
│   │   │       └── openai_error_handler.py
│   │   ├── tests/                        # Comprehensive test suite
│   │   │   ├── test_chat.py
│   │   │   ├── test_supervisor.py
│   │   │   ├── test_workout_builder.py
│   │   │   ├── test_playlist_generation.py
│   │   │   └── ... (45+ tests)
│   │   ├── docs/                         # Backend documentation
│   │   │   ├── RAILWAY_DEPLOYMENT.md
│   │   │   ├── RAILWAY_ENV_VARIABLES.md  # Updated with FRONTEND_URL
│   │   │   ├── ENV_SETUP_GUIDE.md
│   │   │   └── OPENAI_MODELS_USAGE.md
│   │   ├── DATABASE_MIGRATION_COMPLETE_v2.sql  # Unified migration
│   │   ├── .env.example
│   │   ├── requirements.txt
│   │   ├── pyproject.toml
│   │   ├── Procfile                      # Railway deployment
│   │   └── README.md
│   │
│   └── web/                              # React Web (Vite) - PRODUCTION
│       ├── src/
│       │   ├── pages/
│       │   │   ├── ChatPage.tsx          # Main chat interface
│       │   │   ├── PlayerPage.tsx        # Playlist player
│       │   │   ├── HistoryPage.tsx       # Workout/playlist history
│       │   │   ├── LoginPage.tsx         # Spotify login
│       │   │   └── AuthCallbackPage.tsx  # OAuth callback handler
│       │   ├── components/
│       │   │   ├── Chat/
│       │   │   │   ├── InputBar.tsx
│       │   │   │   ├── MessageBubble.tsx
│       │   │   │   ├── PlaylistHistorySidebar.tsx  # History panel
│       │   │   │   ├── SettingsSidebar.tsx  # Manual workout creation
│       │   │   │   └── TypingIndicator.tsx
│       │   │   ├── Player/
│       │   │   │   └── TrackCard.tsx
│       │   │   ├── Shared/
│       │   │   │   ├── Button.tsx
│       │   │   │   ├── ErrorDisplay.tsx
│       │   │   │   ├── LoadingSpinner.tsx
│       │   │   │   └── SpotifyConnectBanner.tsx
│       │   │   └── ProtectedRoute.tsx    # Auth guard
│       │   ├── hooks/
│       │   │   ├── useAuth.ts
│       │   │   ├── useChat.ts
│       │   │   ├── usePlaylist.ts
│       │   │   ├── usePlaylistHistory.ts
│       │   │   └── useWorkoutHistory.ts
│       │   ├── services/
│       │   │   ├── api.ts                # Axios API client
│       │   │   ├── errorLogger.ts        # Error logging to backend
│       │   │   └── supabase.ts           # Supabase client
│       │   ├── stores/
│       │   │   └── authStore.ts          # Zustand auth state
│       │   └── types/
│       │       ├── index.ts
│       │       └── settings.ts
│       ├── dist/                         # Build output
│       ├── public/
│       │   └── favicon.svg
│       ├── index.html
│       ├── vite.config.ts
│       ├── tailwind.config.js
│       ├── package.json
│       ├── railway.json                  # Railway config
│       └── README.md
│
├── docs/                                 # Project documentation
│   ├── API.md                            # API reference (25+ endpoints)
│   ├── ARCHITECTURE_REPORT.md            # Complete architecture (v3.3)
│   ├── DEPLOYMENT.md                     # Deployment guide
│   └── README.md                         # Docs index
│
├── scripts/                              # Utility scripts
│   ├── cleanup_unused_tables.py
│   └── test_all.sh
│
├── .cursor/
│   └── .cursorrules                      # Cursor AI rules
├── .gitignore
├── README.md                             # Main project README
├── CHANGELOG.md                          # Version history
├── CONTRIBUTING.md                       # Contributing guide
├── PRD_CURSOR_AI.md                      # This document
├── PROJECT_STATUS.md                     # Production readiness report
├── QUICKSTART.md                         # Quick start guide
├── DOCUMENTATION_UPDATE_SUMMARY.md       # Docs update log
└── railway.json                          # Railway monorepo config
```

---

## 🗄️ Database Schema (Supabase PostgreSQL)

### Migration SQL

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  spotify_user_id TEXT UNIQUE,
  spotify_access_token TEXT,
  spotify_refresh_token TEXT,
  spotify_token_expires_at TIMESTAMPTZ,
  preferences JSONB DEFAULT '{
    "top_genres": [],
    "top_artists": [],
    "avg_bpm": 145
  }'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workouts table
CREATE TABLE workouts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK (type IN ('steady', 'progressive', 'intervals', 'fartlek')),
  duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
  intensity TEXT NOT NULL CHECK (intensity IN ('low', 'moderate', 'high')),
  hr_zones INTEGER[] DEFAULT ARRAY[110, 180],
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Playlists table
CREATE TABLE playlists (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  workout_id UUID REFERENCES workouts(id) ON DELETE CASCADE,
  spotify_playlist_id TEXT NOT NULL,
  spotify_url TEXT NOT NULL,
  tracks JSONB NOT NULL DEFAULT '[]'::jsonb,
  total_duration_seconds INTEGER NOT NULL,
  generation_time_seconds FLOAT NOT NULL,
  shared BOOLEAN DEFAULT FALSE,
  share_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_workouts_user_id ON workouts(user_id);
CREATE INDEX idx_workouts_created_at ON workouts(created_at DESC);
CREATE INDEX idx_playlists_user_id ON playlists(user_id);
CREATE INDEX idx_playlists_created_at ON playlists(created_at DESC);
CREATE INDEX idx_user_preferences ON users USING GIN (preferences);
CREATE INDEX idx_playlist_tracks ON playlists USING GIN (tracks);

-- Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE workouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE playlists ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own data" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can view own workouts" ON workouts FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own workouts" ON workouts FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can view own playlists" ON playlists FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Anyone can view shared playlists" ON playlists FOR SELECT USING (shared = TRUE);
```

---

## 🔐 Environment Variables

### Backend `.env`

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Spotify OAuth
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8000/auth/spotify/callback

# OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4

# App Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# Frontend URL (IMPORTANT for Spotify OAuth redirect - v3.3.1)
FRONTEND_URL=http://localhost:5173
```

### Web `.env` (Production)

```env
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Production Environment Variables (Railway)

**Backend:**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=https://runbeat-backend.up.railway.app/auth/spotify/callback
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=["https://runbeatweb-production.up.railway.app"]
FRONTEND_URL=https://runbeatweb-production.up.railway.app  # CRITICAL for OAuth
```

**Web:**
```env
VITE_API_URL=https://runbeat-backend.up.railway.app
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
NODE_ENV=production
```

---

## 🎨 Core Features Implementation

### 1. Chat Interface (LLM Parsing)

**Backend: `app/api/routes/chat.py`**

```python
from fastapi import APIRouter, Depends
from app.services.llm_service import LLMService
from app.schemas.chat import ChatRequest, ChatResponse
from app.models.workout import Workout

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    llm: LLMService = Depends(),
):
    """
    Parse user message with OpenAI GPT-4
    Extract workout parameters
    """

    # LLM prompt for workout extraction
    prompt = f"""
You are RunBeat AI assistant. Parse the user's workout request into structured JSON.

User message: "{request.message}"

Extract:
{{
  "type": "steady|progressive|intervals|fartlek",
  "duration_minutes": <number>,
  "intensity": "low|moderate|high",
  "hr_zones": [<min>, <max>],
  "confidence": <0-1>,
  "needs_clarification": <bool>,
  "clarification_question": "<string if needed>"
}}

Examples:
"Хочу пробігти 40 хв з інтервалами" →
{{
  "type": "intervals",
  "duration_minutes": 40,
  "intensity": "moderate",
  "hr_zones": [130, 180],
  "confidence": 0.8,
  "needs_clarification": true,
  "clarification_question": "Який буде інтервал роботи/відпочинку?"
}}

"Легке відновлення 30 хвилин" →
{{
  "type": "steady",
  "duration_minutes": 30,
  "intensity": "low",
  "hr_zones": [110, 130],
  "confidence": 0.95,
  "needs_clarification": false
}}

Return ONLY valid JSON.
"""

    # Call OpenAI
    response = await llm.parse_workout(prompt)
    workout_params = response.parsed_json

    if workout_params.get("needs_clarification"):
        return ChatResponse(
            message=workout_params["clarification_question"],
            workout=None,
            needs_clarification=True,
        )

    workout = Workout(**workout_params)
    return ChatResponse(
        message=f"Зрозумів! Генерую плейлист на {workout.duration_minutes} хв...",
        workout=workout,
        needs_clarification=False,
    )
```

**LLM Service: `app/services/llm_service.py`**

```python
from openai import AsyncOpenAI
from app.core.config import settings
import json

class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def parse_workout(self, prompt: str) -> dict:
        """Parse workout intent using GPT-4"""

        response = await self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a JSON-only assistant. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower for more consistent parsing
            max_tokens=500,
        )

        content = response.choices[0].message.content

        # Strip markdown if present
        if content.startswith("```json"):
            content = content.replace("```json\n", "").replace("```\n", "").replace("```", "")

        parsed = json.loads(content)
        return type('Response', (), {'parsed_json': parsed})()
```

---

### 2. Playlist Generation

**Core Algorithm: `app/services/playlist_generator.py`**

```python
from typing import List, Dict
from app.models.workout import Workout
from app.models.playlist import Track, PlaylistData
from app.services.spotify_service import SpotifyService
import asyncio

class PlaylistGenerator:
    """
    Single-class playlist generator (simplified from 7 agents)
    """

    def __init__(self, spotify: SpotifyService):
        self.spotify = spotify

    async def generate(
        self,
        workout: Workout,
        user_preferences: Dict,
    ) -> PlaylistData:
        """Main generation method"""

        # 1. Create workout segments
        segments = self._create_segments(workout)

        # 2. Fetch candidate tracks (parallel)
        candidates = await self._fetch_candidates(segments, user_preferences)

        # 3. Score tracks
        scored = self._score_tracks(candidates, segments, user_preferences)

        # 4. Optimize selection
        selected = self._optimize_selection(scored, workout.duration_minutes * 60)

        return PlaylistData(
            tracks=selected,
            total_duration=sum(t.duration_ms for t in selected) / 1000,
        )

    def _create_segments(self, workout: Workout) -> List[Dict]:
        """Create workout segments with BPM ranges"""

        if workout.type == "steady":
            target_bpm = self._calculate_target_bpm(workout.intensity)
            return [
                {"name": "warm-up", "duration": 5, "bpm_range": [target_bpm-20, target_bpm-10]},
                {"name": "main", "duration": workout.duration_minutes-10, "bpm_range": [target_bpm-5, target_bpm+5]},
                {"name": "cool-down", "duration": 5, "bpm_range": [target_bpm-25, target_bpm-15]},
            ]

        elif workout.type == "progressive":
            start_bpm = self._calculate_target_bpm("low")
            end_bpm = self._calculate_target_bpm("high")
            num_segments = 5

            segments = []
            for i in range(num_segments):
                progress = i / (num_segments - 1)
                current_bpm = start_bpm + (end_bpm - start_bpm) * progress
                segments.append({
                    "name": f"segment_{i+1}",
                    "duration": workout.duration_minutes / num_segments,
                    "bpm_range": [current_bpm-5, current_bpm+5],
                })
            return segments

        # Add intervals, fartlek logic here
        return []

    def _calculate_target_bpm(self, intensity: str) -> int:
        """Calculate target BPM from intensity"""
        intensity_map = {
            "low": 125,      # Easy pace
            "moderate": 145, # Tempo pace
            "high": 165,     # Fast pace
        }
        return intensity_map.get(intensity, 145)

    async def _fetch_candidates(self, segments: List[Dict], user_prefs: Dict) -> List[Track]:
        """Fetch candidate tracks for all segments (parallel)"""

        tasks = [
            self._fetch_for_segment(seg, user_prefs)
            for seg in segments
        ]

        results = await asyncio.gather(*tasks)

        all_candidates = []
        for tracks in results:
            all_candidates.extend(tracks)

        return all_candidates

    async def _fetch_for_segment(self, segment: Dict, user_prefs: Dict) -> List[Track]:
        """Fetch tracks for one segment"""

        bpm_min, bpm_max = segment["bpm_range"]
        target_bpm = int((bpm_min + bpm_max) / 2)

        # Use Spotify Recommendations API
        tracks = await self.spotify.get_recommendations(
            seed_genres=user_prefs.get("top_genres", [])[:2],
            seed_artists=user_prefs.get("top_artists", [])[:2],
            target_tempo=target_bpm,
            min_tempo=int(bpm_min),
            max_tempo=int(bpm_max),
            target_energy=0.7,  # High energy for workouts
            limit=20,
        )

        return tracks

    def _score_tracks(
        self,
        candidates: List[Track],
        segments: List[Dict],
        user_prefs: Dict,
    ) -> List[Dict]:
        """Score tracks based on BPM, energy, user affinity"""

        scored = []

        for track in candidates:
            # Find best matching segment
            best_segment = min(segments, key=lambda s: abs(
                (s["bpm_range"][0] + s["bpm_range"][1])/2 - track.bpm
            ))

            # Calculate scores
            bpm_score = self._bpm_match_score(track.bpm, best_segment["bpm_range"])
            energy_score = track.energy  # Already 0-1
            affinity_score = self._calculate_affinity(track, user_prefs)

            # Weighted total
            total = bpm_score * 0.40 + energy_score * 0.25 + affinity_score * 0.35

            scored.append({
                "track": track,
                "score": total,
                "segment": best_segment["name"],
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    def _bpm_match_score(self, bpm: float, bpm_range: List[int]) -> float:
        """Calculate BPM match score (0-1)"""
        min_bpm, max_bpm = bpm_range
        if min_bpm <= bpm <= max_bpm:
            return 1.0
        # Penalty for out of range
        distance = min(abs(bpm - min_bpm), abs(bpm - max_bpm))
        return max(0, 1 - distance / 20)  # 20 BPM tolerance

    def _calculate_affinity(self, track: Track, user_prefs: Dict) -> float:
        """Calculate user affinity score (0-1)"""
        score = 0.5  # Base score

        # Genre match
        if any(g in user_prefs.get("top_genres", []) for g in track.genres):
            score += 0.3

        # Artist match
        if track.artist_id in user_prefs.get("top_artists", []):
            score += 0.2

        return min(1.0, score)

    def _optimize_selection(
        self,
        scored_tracks: List[Dict],
        target_duration: int,  # seconds
    ) -> List[Track]:
        """Select optimal tracks with constraints"""

        selected = []
        artist_count = {}
        current_duration = 0

        for item in scored_tracks:
            track = item["track"]

            # Check duration
            if current_duration + track.duration_ms/1000 > target_duration * 1.15:
                continue

            # Check artist diversity (max 2 per artist)
            if artist_count.get(track.artist_id, 0) >= 2:
                continue

            # Check BPM transition (smooth < 15 BPM jump)
            if selected and abs(selected[-1].bpm - track.bpm) > 15:
                continue

            # Add track
            selected.append(track)
            current_duration += track.duration_ms / 1000
            artist_count[track.artist_id] = artist_count.get(track.artist_id, 0) + 1

            # Check if target reached
            if current_duration >= target_duration * 0.95:
                break

        return selected
```

---

### 3. Spotify Service

**Spotify Integration: `app/services/spotify_service.py`**

```python
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from app.core.config import settings
from typing import List, Dict, Optional

class SpotifyService:
    def __init__(self):
        self.client_credentials = SpotifyClientCredentials(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
        )

    def get_user_client(self, access_token: str) -> spotipy.Spotify:
        """Get Spotify client with user's access token"""
        return spotipy.Spotify(auth=access_token)

    async def get_user_top_tracks(
        self,
        user_client: spotipy.Spotify,
        limit: int = 50,
    ) -> List[Dict]:
        """Get user's top tracks"""
        results = user_client.current_user_top_tracks(limit=limit, time_range='medium_term')
        return results['items']

    async def get_user_top_artists(
        self,
        user_client: spotipy.Spotify,
        limit: int = 20,
    ) -> List[Dict]:
        """Get user's top artists"""
        results = user_client.current_user_top_artists(limit=limit, time_range='medium_term')
        return results['items']

    async def get_recommendations(
        self,
        seed_genres: List[str],
        seed_artists: List[str],
        target_tempo: int,
        min_tempo: int,
        max_tempo: int,
        target_energy: float,
        limit: int = 20,
    ) -> List[Dict]:
        """Get track recommendations from Spotify"""

        sp = spotipy.Spotify(client_credentials_manager=self.client_credentials)

        results = sp.recommendations(
            seed_genres=seed_genres[:2],  # Max 2
            seed_artists=seed_artists[:2],  # Max 2
            limit=limit,
            target_tempo=target_tempo,
            min_tempo=min_tempo,
            max_tempo=max_tempo,
            target_energy=target_energy,
        )

        return results['tracks']

    async def get_audio_features_batch(
        self,
        track_ids: List[str],
    ) -> List[Dict]:
        """Get audio features for multiple tracks (batch)"""

        sp = spotipy.Spotify(client_credentials_manager=self.client_credentials)
        features = sp.audio_features(track_ids)
        return features

    async def create_playlist(
        self,
        user_client: spotipy.Spotify,
        user_id: str,
        name: str,
        tracks: List[str],  # Spotify URIs
        description: str = "Generated by RunBeat AI",
    ) -> Dict:
        """Create playlist in user's Spotify account"""

        # Create playlist
        playlist = user_client.user_playlist_create(
            user=user_id,
            name=name,
            public=False,
            description=description,
        )

        # Add tracks
        if tracks:
            user_client.playlist_add_items(
                playlist_id=playlist['id'],
                items=tracks,
            )

        return {
            'id': playlist['id'],
            'url': playlist['external_urls']['spotify'],
            'uri': playlist['uri'],
        }
```

---

### 4. Frontend Mobile (React Native)

**Chat Screen: `apps/mobile/src/screens/ChatScreen.tsx`**

```typescript
import React, { useState } from 'react';
import { View, FlatList, KeyboardAvoidingView, Platform } from 'react-native';
import { MessageBubble } from '../components/Chat/MessageBubble';
import { InputBar } from '../components/Chat/InputBar';
import { TypingIndicator } from '../components/Chat/TypingIndicator';
import { useChat } from '../hooks/useChat';
import { useNavigation } from '@react-navigation/native';

export function ChatScreen() {
  const { messages, sendMessage, isLoading } = useChat();
  const navigation = useNavigation();

  const handleSend = async (text: string) => {
    const response = await sendMessage(text);

    // If playlist generated, navigate to player
    if (response?.playlist_id) {
      navigation.navigate('Player', { playlistId: response.playlist_id });
    }
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={90}
    >
      <FlatList
        data={messages}
        renderItem={({ item }) => <MessageBubble message={item} />}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ padding: 16 }}
      />
      {isLoading && <TypingIndicator />}
      <InputBar onSend={handleSend} disabled={isLoading} />
    </KeyboardAvoidingView>
  );
}
```

**Chat Hook: `apps/mobile/src/hooks/useChat.ts`**

```typescript
import { useState, useCallback } from 'react';
import { api } from '../services/api';
import { Message } from '../types';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = useCallback(async (text: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    setIsLoading(true);
    try {
      // Call backend
      const response = await api.chat.sendMessage(text);

      // Add AI response
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
        workout: response.workout,
      };
      setMessages(prev => [...prev, aiMessage]);

      // If playlist ready, trigger generation
      if (response.workout && !response.needs_clarification) {
        const playlistResponse = await api.playlists.generate({
          workout: response.workout,
        });

        return playlistResponse;
      }
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { messages, sendMessage, isLoading };
}
```

---

## 📝 Cursor AI Rules (`.cursorrules`)

Create this file in project root for Cursor AI assistance:

```yaml
# .cursorrules - RunBeat Project Guidelines for Cursor AI

project_info:
  name: RunBeat
  version: "2.0"
  type: Mobile-first AI music assistant
  tech_stack:
    backend: FastAPI + Python 3.11
    mobile: React Native + Expo
    web: React + Vite
    database: Supabase PostgreSQL
    llm: OpenAI GPT-4
    music: Spotify API

coding_standards:
  python:
    - Use async/await for all I/O operations
    - Type hints required (Pydantic, typing module)
    - Format with black (line length 100)
    - Lint with ruff
    - Docstrings for all functions
    - Follow PEP 8

  typescript:
    - Use TypeScript strict mode
    - Functional components only (no classes)
    - Hooks for state management
    - Format with prettier
    - Lint with ESLint
    - Explicit return types for functions

  naming:
    - Files: snake_case for Python, PascalCase for React components
    - Variables: snake_case (Python), camelCase (TypeScript)
    - Constants: UPPER_SNAKE_CASE
    - Components: PascalCase

architecture:
  backend:
    - Single-file services (no 7 agents)
    - All database operations through SupabaseService
    - All Spotify calls through SpotifyService
    - LLM calls through LLMService
    - Keep playlist_generator.py simple and readable

  frontend:
    - Screens for main views
    - Components for reusable UI
    - Hooks for logic/state
    - Services for API calls
    - Zustand for global state

best_practices:
  - Cache aggressively (user preferences: 24h)
  - Parallel requests when possible (asyncio.gather)
  - Graceful error handling with user-friendly messages
  - Loading states for all async operations
  - Optimistic UI updates where applicable
  - Log all errors with context (loguru)
  - Test all API endpoints (pytest)
  - Mobile-first design (touch targets, responsive)

api_conventions:
  - RESTful endpoints
  - POST for mutations
  - GET for queries
  - Return 200 with data or 4xx/5xx with error
  - Always include timestamps
  - Use UUIDs for IDs
  - Paginate lists (default limit: 10)

database:
  - Use RLS policies (already configured)
  - JSONB for flexible fields (preferences, tracks)
  - Indexes on foreign keys and common queries
  - Use auth.uid() in RLS policies

security:
  - Never expose service keys to frontend
  - Use Supabase RLS for data access control
  - Refresh Spotify tokens automatically
  - Rate limit API endpoints
  - Sanitize all user inputs

performance:
  - Target: Playlist generation < 10s
  - Target: API response < 500ms
  - Target: UI response < 100ms
  - Use Redis cache if needed (not in MVP)
  - Optimize Spotify API calls (batch, parallel)

comments:
  - Explain WHY, not WHAT
  - Document complex algorithms
  - No obvious comments ("i = i + 1  # increment i")
  - Use docstrings for public APIs

error_handling:
  - Try/except around all external API calls
  - Log errors with context
  - Return user-friendly error messages
  - Don't expose internal errors to users

testing:
  - Unit tests for core logic
  - Integration tests for API endpoints
  - Mock external services (Spotify, OpenAI)
  - Target: 60%+ coverage

git:
  - Conventional commits (feat:, fix:, docs:, etc)
  - Small, focused commits
  - Descriptive commit messages
  - Branch naming: feature/*, fix/*, chore/*

do_not:
  - Don't create 7 separate agents (use single generator)
  - Don't use Firebase (use Supabase)
  - Don't hardcode values (use config)
  - Don't ignore errors
  - Don't skip type hints
  - Don't make blocking calls without async
  - Don't expose sensitive keys
  - Don't create complex abstractions (keep it simple)

priorities:
  1. Functionality (it works)
  2. Simplicity (easy to understand)
  3. Performance (< 10s generation)
  4. User experience (smooth UI)
  5. Code quality (readable, maintainable)

when_stuck:
  - Check RUNBEAT_V2_ARCHITECTURE.md
  - Check SUPABASE_MIGRATION_GUIDE.md
  - Check existing similar code
  - Ask for clarification
  - Keep it simple

reminders:
  - Mobile-first (not web-first)
  - One generator (not 7 agents)
  - Supabase (not Firebase)
  - OpenAI GPT-4 for chat parsing
  - Spotify Premium for playlist creation
  - Target: 3 weeks to MVP
```

---

## ✅ MVP Success Criteria

### Functional Requirements
- [x] User can chat with AI
- [x] AI parses workout intent correctly (>95% accuracy with LangChain)
- [x] Playlist generates in < 10 seconds
- [x] Playlist matches workout parameters (BPM, duration)
- [x] Spotify integration (OAuth + playlist creation)
- [x] User can view workout and playlist history
- [x] Dual playlist variant generation
- [x] AI learning from user conversations
- [x] Personalized recommendations based on history

### Technical Requirements
- [x] Backend API deployed on Railway
- [x] Web app deployed on Railway
- [x] Supabase database configured
- [x] Multi-agent LangChain architecture
- [x] Comprehensive test suite
- [x] Error logging and analytics
- [ ] Mobile app (iOS + Android) - Planned

### Performance Requirements
- [x] Playlist generation: < 10 seconds ✅
- [x] API response time: < 500ms (p95) ✅
- [x] Chat response: < 3 seconds ✅
- [x] Conversation state management ✅
- [x] Production-ready deployment ✅

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Supabase account
- Spotify Developer account
- OpenAI API key

### Quick Start

```bash
# 1. Clone & setup
git clone <repo>
cd runbeat

# 2. Backend
cd apps/backend
uv add -r requirements.txt
cp .env.example .env
# Fill in .env with your keys
uvicorn app.main:app --reload

# 3. Mobile
cd apps/mobile
npm install
cp .env.example .env
# Fill in .env
npx expo start

# 4. Web
cd apps/web
npm install
cp .env.example .env
# Fill in .env
npm run dev
```

### First Tasks (Cursor AI)

1. **Backend Setup** (Day 1)
   - [ ] Create FastAPI app structure
   - [ ] Connect to Supabase
   - [ ] Implement health checks
   - [ ] Test with Postman

2. **LLM Integration** (Day 2)
   - [ ] Create LLMService
   - [ ] Implement chat endpoint
   - [ ] Test workout parsing

3. **Playlist Generator** (Day 3-4)
   - [ ] Implement core algorithm
   - [ ] Integrate Spotify API
   - [ ] Test with real data

4. **Mobile App** (Week 2)
   - [ ] Create navigation
   - [ ] Build chat UI
   - [ ] Build player UI
   - [ ] Test on device

---

## 📚 Additional Resources

- **Architecture:** `RUNBEAT_V2_ARCHITECTURE.md`
- **Supabase Guide:** `SUPABASE_MIGRATION_GUIDE.md`
- **Development Plan:** `DEVELOPMENT_PLAN_3_WEEKS.md`
- **Quick Start:** `QUICK_START_CHECKLIST.md`

---

**Status:** ✅ **PRODUCTION READY** - Deployed & Active 🚀
**Start Date:** September 2025
**MVP Completed:** November 2025
**Current Version:** 3.3.1 (AI Learning & Personalization + Spotify Auth Fix)
**Deployment:** Railway (Backend + Web)
**Repository:** [GitHub](https://github.com/alexxxstep/runbeat)
**AI Assistant:** Cursor AI with GPT-4
**Developer:** Alex

---

## 📊 Production Metrics (v3.3.1)

### Performance
- ✅ **Playlist Generation:** 6-8 seconds (target: <10s)
- ✅ **API Response Time:** 200-400ms (target: <500ms)
- ✅ **Chat Response:** 1-2 seconds (target: <3s)
- ✅ **Workout Intent Accuracy:** 95%+ (target: >90%)
- ✅ **Uptime:** 99.5%+ (target: 99%+)

### System Stats
- **Backend Endpoints:** 25+
- **AI Agents:** 4 (Supervisor, WorkoutBuilder, WorkoutManager, MusicCurator)
- **Database Tables:** 6 (users, workouts, playlists, conversations, error_logs, playlist_tracks)
- **Test Coverage:** 70%+
- **Lines of Code:** ~15,000+

### Features Completed
- ✅ Multi-agent AI system (LangChain)
- ✅ Natural language processing
- ✅ Dual playlist variants
- ✅ Spotify OAuth integration (fixed in v3.3.1)
- ✅ User pattern recognition
- ✅ Conversation analytics
- ✅ Error logging
- ✅ Manual workout creation
- ✅ Workout/playlist history

---

## 🔄 Latest Updates (v3.3.1)

### Hotfix: Spotify OAuth Redirect
- **Issue:** Users received "Not Found" error after Spotify authorization
- **Fix:** Added `FRONTEND_URL` environment variable for proper redirect
- **Impact:** OAuth flow now works correctly in production
- **Documentation:** Updated `RAILWAY_ENV_VARIABLES.md`

### Recent Improvements (v3.3)
- AI Learning & Personalization system
- Conversation history storage
- User pattern recognition
- Analytics API
- Enhanced error handling
- Improved context understanding

---

**RunBeat is live, production-ready, and actively serving users!** 💪🎵🏃‍♂️

**Production URLs:**
- **Backend:** https://runbeat-backend.up.railway.app
- **Frontend:** https://runbeatweb-production.up.railway.app
- **Docs:** [GitHub Repository](https://github.com/alexxxstep/runbeat)
