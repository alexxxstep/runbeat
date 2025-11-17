# RunBeat 🎵🏃‍♂️

**AI-powered music assistant for runners** that generates personalized workout playlists through natural chat conversation.

[![Production Status](https://img.shields.io/badge/status-production-brightgreen)](https://github.com/yourusername/runbeat)
[![Version](https://img.shields.io/badge/version-3.3-blue)](./CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18-blue)](https://reactjs.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

---

## 🎯 Project Overview

**RunBeat** - це інтелектуальна система генерації музичних плейлистів для бігу, що використовує передові технології штучного інтелекту для створення персоналізованих тренувальних програм.

### Що робить RunBeat унікальним?

- 🧠 **AI-агенти на базі LangChain** - складна багатоагентна система для розуміння природної мови
- 🎯 **Персоналізація через навчання** - система аналізує історію розмов і вчиться на ваших уподобаннях
- ⚡ **Швидка генерація** - плейлисти створюються менш ніж за 10 секунд
- 🎵 **Dual Variants** - AI генерує 2 варіанти плейлиста, ви обираєте кращий
- 📊 **Аналітика та інсайти** - система відстежує patterns користувачів та оптимізує розмови

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

### AI-Powered Conversation

- 🤖 **Smart AI Chat** - Natural language workout planning with LangChain multi-agent system
- 🧠 **AI Learning** - System learns from your conversation history
- 🎯 **Personalized Suggestions** - AI recommends based on your favorite genres and typical workout parameters
- 💬 **Context-Aware** - AI remembers conversation context and previous interactions

### Workout Creation

- ⚙️ **Manual Workout Builder** - Configure workouts via right panel settings
- 🏃 **Multiple Workout Types** - Steady, Progressive, Intervals, Fartlek
- ⚡ **Instant Activation** - Click any workout in history to make it active
- 📊 **Complete History** - All workouts and playlists saved and accessible

### Playlist Generation

- 🎵 **Dual Playlist Variants** - AI generates 2 options, you choose the best fit
- ⚡ **Fast Generation** - Playlists ready in under 10 seconds
- 🎯 **BPM Matching** - Music perfectly synced to workout intensity
- 🎼 **Genre Flexibility** - Support for 15+ music genres with fuzzy matching
- 🔄 **Regeneration** - Create new playlists for any saved workout

### Analytics & Insights

- 📈 **Conversation Analytics** - Track completion rates and user patterns
- 🔍 **User Pattern Recognition** - Identify favorite genres, typical duration, preferred workout types
- 📊 **Error Logging** - Comprehensive error tracking and statistics

## 🏗️ Tech Stack

### Backend

- **Framework:** FastAPI + Python 3.11
- **AI/LLM:** OpenAI GPT-4 + LangChain 0.1.0
- **Architecture:** Multi-agent system (Supervisor, WorkoutBuilder, MusicCurator, WorkoutManager)
- **Database:** Supabase PostgreSQL
- **Music API:** Spotify API (spotipy)
- **Logging:** Loguru + Database error logging

### Frontend

- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite 5
- **Styling:** Tailwind CSS
- **State Management:** Zustand
- **Routing:** React Router v6
- **HTTP Client:** Axios

### Infrastructure

- **Deployment:** Railway (Backend + Web)
- **Database:** Supabase (PostgreSQL + Auth)
- **CI/CD:** Automatic deployment on push to main

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
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Web Setup

```bash
cd apps/web
npm install
cp .env.example .env
# Fill in .env with backend URL
npm run dev
```

### Database Setup

1. Create a Supabase project
2. Run the migration: `apps/backend/DATABASE_MIGRATION_COMPLETE_v2.sql`
3. Copy your Supabase URL and keys to `.env` files

See [DEPLOYMENT.md](./docs/DEPLOYMENT.md) for detailed deployment instructions.

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

### ✅ Completed (v3.3 - Production Ready)

#### Core Features

- ✅ Natural language AI chat interface with LangChain
- ✅ Multi-agent architecture (Supervisor, WorkoutBuilder, MusicCurator, WorkoutManager)
- ✅ Workout intent parsing (95%+ accuracy with context awareness)
- ✅ Dual playlist variant generation (<10s)
- ✅ BPM & genre matching with fuzzy recognition
- ✅ Spotify OAuth integration & playlist creation
- ✅ Manual workout creation via settings panel

#### AI Learning & Personalization (v3.3)

- ✅ Conversation history storage in database
- ✅ User pattern recognition (favorite genres, typical duration, preferred type)
- ✅ Personalized AI suggestions based on history
- ✅ Conversation analytics API (completion rate, abandonment rate, insights)
- ✅ Context-aware conversation flow

#### User Interface

- ✅ Responsive web interface (desktop + mobile)
- ✅ Workout history with instant activation
- ✅ Playlist history with regeneration capability
- ✅ Real-time chat with typing indicators
- ✅ Error handling with user-friendly messages
- ✅ Auto-refresh history panels

#### Backend Infrastructure

- ✅ Comprehensive error logging to database
- ✅ Analytics endpoints for monitoring
- ✅ Production deployment on Railway
- ✅ Database migration scripts
- ✅ Comprehensive test suite

### 🚧 In Progress

- 🚧 Advanced analytics dashboard UI
- 🚧 Performance optimizations (caching, Redis)
- 🚧 LangSmith integration for AI observability

### 📋 Planned (Future Versions)

- 📋 Mobile app (React Native + Expo)
- 📋 Voice commands for hands-free operation
- 📋 Offline mode with local caching
- 📋 Apple Music integration
- 📋 Social sharing features
- 📋 Collaborative playlists
- 📋 Workout challenges and achievements

## 🔧 Development

### Architecture

RunBeat використовує **multi-agent architecture** на базі LangChain:

- **SupervisorAgent** - оркеструє всі агенти та керує станом розмови
- **WorkoutBuilder** - AI-агент для покрокового збору параметрів тренування
- **WorkoutManager** - створює та активує тренування в базі даних
- **MusicCurator** - генерує плейлисти з інтеграцією Spotify
- **ConversationService** - зберігає розмови та аналізує user patterns

Детальна документація: [ARCHITECTURE_REPORT.md](./docs/ARCHITECTURE_REPORT.md)

### Testing

```bash
# Backend tests
cd apps/backend
pytest tests/ -v

# Run specific test
pytest tests/test_chat.py -v

# With coverage
pytest --cov=app tests/
```

### Code Quality

```bash
# Backend linting
cd apps/backend
ruff check app/
black app/ --check

# Frontend linting
cd apps/web
npm run lint
```

---

## 🌟 Key Achievements

- ✅ **95%+ accuracy** в парсингу workout intent
- ✅ **<10 секунд** генерація плейлиста
- ✅ **Multi-agent AI** система з LangChain
- ✅ **AI Learning** - персоналізація через аналіз історії
- ✅ **Production Ready** - задеплоєно на Railway
- ✅ **Comprehensive Testing** - повний набір тестів

---

## 📊 Project Stats

- **Lines of Code:** ~15,000+
- **Backend Endpoints:** 25+
- **AI Agents:** 4 (Supervisor, Builder, Manager, Curator)
- **Database Tables:** 6 (users, workouts, playlists, conversations, error_logs, playlist_tracks)
- **Supported Genres:** 15+
- **Test Coverage:** 70%+

---

## 🤝 Contributing

Ми вітаємо внески в проект! Будь ласка, ознайомтеся з [CONTRIBUTING.md](./CONTRIBUTING.md) для детальної інформації.

### Quick Contribution Guide

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'feat: add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

## 👥 Team

- **Developer:** Alex
- **AI Assistant:** Cursor AI with GPT-4
- **Architecture:** Multi-agent LangChain system

---

## 🙏 Acknowledgments

- [OpenAI](https://openai.com/) - GPT-4 API
- [LangChain](https://langchain.com/) - Multi-agent framework
- [Spotify](https://developer.spotify.com/) - Music API
- [Supabase](https://supabase.com/) - Database and Auth
- [Railway](https://railway.app/) - Deployment platform

---

## 📞 Support

- 📧 Email: support@runbeat.app
- 🐛 Issues: [GitHub Issues](https://github.com/alexxxstep/runbeat/issues)
- 📖 Docs: [Documentation](./docs/)

---

**Status:** ✅ **Production Ready** - MVP Complete, actively adding features
**Version:** 3.3 (AI Learning & Personalization)
**Last Updated:** November 2025
**Deployment:** [Railway](https://railway.app/)

---

<p align="center">
  Made with ❤️ for runners who love music
</p>
