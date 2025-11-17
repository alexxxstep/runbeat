# RunBeat 🎵🏃‍♂️

AI-powered music assistant for runners that generates personalized workout playlists through natural chat conversation.

## 🎯 Project Overview

RunBeat uses advanced AI to understand your workout needs in natural language and generates perfectly timed Spotify playlists in under 10 seconds. The system learns from your preferences and adapts to your running style.

### Core User Flow

```
User: "Хочу інтервальну пробіжку 40 хв під електронну музику"
  ↓ AI parses intent & parameters (instant)
AI: Creates workout → Generates 2 playlist variants
  ↓ User selects best variant
AI: Saves to Spotify (3-5s)
  ↓ Playlist appears in sidebar history
User: Starts running with perfect music 🏃‍♂️🎵

Alternative:
User: Clicks "Create Workout" in right panel
  ↓ Manual configuration (duration, intensity, genres)
  ↓ AI generates 2 playlist variants
User: Selects & saves to Spotify 🎵
```

## ✨ Key Features

- 🤖 **Smart AI Conversation** - Natural language workout planning
- ⚙️ **Manual Workout Creation** - Configure workouts via right panel
- 🎵 **Dual Playlist Variants** - Choose the best fit every time
- 📊 **Workout History** - All workouts and playlists saved
- 🧠 **Personalization** - AI learns your favorite genres and preferences
- ⚡ **Fast Generation** - Playlists ready in seconds
- 🎯 **BPM Matching** - Music synced to workout intensity

## 🏗️ Tech Stack

- **Backend:** FastAPI + Python 3.11
- **Web:** React + Vite + TypeScript
- **Database:** Supabase PostgreSQL
- **AI:** OpenAI GPT-4 (LangChain multi-agent system)
- **Music:** Spotify API
- **Deployment:** Railway

## 📁 Project Structure

```
runbeat/
├── apps/
│   ├── backend/          # FastAPI Backend
│   │   ├── app/          # Application code
│   │   │   ├── agents/   # LangChain AI agents
│   │   │   ├── api/      # API routes
│   │   │   ├── services/ # Business logic
│   │   │   └── models/   # Data models
│   │   └── tests/        # Backend tests
│   └── web/              # React Web (Vite)
│       └── src/          # Frontend source code
├── docs/                 # Documentation
└── scripts/              # Utility scripts
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase account
- Spotify Developer account
- OpenAI API key

### Backend Setup

```bash
cd apps/backend
pip install -r requirements.txt
cp .env.example .env
# Fill in .env with your keys
uvicorn app.main:app --reload
```

### Web Setup

```bash
cd apps/web
npm install
cp .env.example .env
# Fill in .env
npm run dev
```

## 📚 Documentation

### Core Documentation
- 📋 [Architecture Report](./docs/ARCHITECTURE_REPORT.md) - Complete system architecture (v3.3)
- 📄 [PRD](./PRD_CURSOR_AI.md) - Product Requirements Document
- 📝 [Changelog](./CHANGELOG.md) - Version history and updates
- 🤝 [Contributing Guide](./CONTRIBUTING.md) - How to contribute

### Setup Guides
- 🔌 [Backend README](./apps/backend/README.md) - Backend setup & deployment
- 🌐 [Web README](./apps/web/README.md) - Web app setup

### Technical Guides
- 🗄️ [Database Migration](./apps/backend/DATABASE_MIGRATION_COMPLETE_v2.sql) - Complete DB schema
- 🤖 [OpenAI Models Usage](./apps/backend/OPENAI_MODELS_USAGE.md) - AI integration details
- ⚙️ [Environment Setup](./apps/backend/ENV_SETUP_GUIDE.md) - Configuration guide
- 🚂 [Railway Deployment](./apps/backend/RAILWAY_QUICK_START.md) - Deploy to Railway
- 📚 [API Documentation](./docs/API.md) - Complete API reference
- 🚀 [Deployment Guide](./docs/DEPLOYMENT.md) - Full deployment instructions

## 🎯 Feature Status

### ✅ Completed (MVP)
- ✅ Natural language AI chat interface
- ✅ Workout intent parsing (95%+ accuracy)
- ✅ Dual playlist variant generation (<10s)
- ✅ BPM & genre matching
- ✅ Spotify integration & saving
- ✅ Workout & playlist history
- ✅ User pattern recognition & learning
- ✅ Responsive web interface

### 🚧 In Progress
- 🚧 Advanced analytics dashboard
- 🚧 Social sharing features

### 📋 Planned
- 📋 Mobile app (React Native + Expo)
- 📋 Voice commands
- 📋 Offline mode
- 📋 Apple Music integration

## 📝 Development

See [ARCHITECTURE_REPORT.md](./docs/ARCHITECTURE_REPORT.md) for detailed system architecture and development guidelines.

**Status:** ✅ MVP Complete, actively adding features
**Version:** 3.3 (AI Learning & Personalization)
**Last Updated:** January 2025
