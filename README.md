# RunBeat 🎵🏃‍♂️

Mobile-first AI music assistant for runners that generates personalized workout playlists through natural chat conversation.

## 🎯 Project Overview

RunBeat uses AI to understand your workout needs and generates Spotify playlists tailored to your running session in under 10 seconds.

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

## 🏗️ Tech Stack

- **Backend:** FastAPI + Python 3.11
- **Mobile:** React Native + Expo
- **Web:** React + Vite
- **Database:** Supabase PostgreSQL
- **AI:** OpenAI GPT-4
- **Music:** Spotify API

## 📁 Project Structure

```
runbeat/
├── apps/
│   ├── backend/          # FastAPI Backend
│   ├── mobile/           # React Native (Expo)
│   └── web/              # React Web (Vite)
├── packages/
│   └── shared-types/     # TypeScript types
└── docs/                 # Documentation
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

### Mobile Setup

```bash
cd apps/mobile
npm install
cp .env.example .env
# Fill in .env
npx expo start
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

- [PRD](./PRD_CURSOR_AI.md) - Product Requirements Document
- [API Documentation](./docs/API.md) - Complete API reference
- [Deployment Guide](./docs/DEPLOYMENT.md) - Deployment instructions
- [Project Status](./PROJECT_STATUS.md) - Current project status
- [Backend README](./apps/backend/README.md) - Backend setup guide

## 🎯 MVP Goals

- [ ] User can chat with AI
- [ ] AI parses workout intent correctly (>90% accuracy)
- [ ] Playlist generates in < 10 seconds
- [ ] Playlist matches workout parameters (BPM, duration)
- [ ] "Open in Spotify" opens Spotify app
- [ ] User can view playlist history

## 📝 Development

See [PRD_CURSOR_AI.md](./PRD_CURSOR_AI.md) for detailed development plan and architecture.

**Status:** 🚧 In Development
**Target MVP:** 3 weeks
**Version:** 2.0
