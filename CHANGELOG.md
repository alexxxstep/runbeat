# RunBeat Changelog

## Version 3.3 - AI Learning & Personalization (November 2025)

### ✨ Major Features

#### AI Learning System
- 🧠 **User Pattern Recognition** - AI analyzes conversation history to learn user preferences
- 📊 **Analytics API** - New endpoints for conversation insights and user patterns
- 💾 **Conversation Persistence** - All chats saved to database for learning
- 🎯 **Personalized Responses** - AI incorporates user's favorite genres and typical workout parameters

#### Enhanced User Interface
- 📋 **7-Step User Flow Guide** - Comprehensive in-app instructions
  1. Describe workout via AI chat (natural language)
  2. AI clarification questions (if needed)
  3. Workout creation & dual playlist generation
  4. OR Create custom workout manually via right panel
  5. Track selection & exclusion
  6. History panel navigation (right sidebar)
  7. Regenerate playlists for saved workouts
- 🔄 **Auto-Refresh History** - Workout/playlist panels update automatically
- ⚡ **Instant Workout Activation** - Click workout in history to make it active
- ⚙️ **Manual Workout Creation** - Create workouts via right panel without AI chat

#### Backend Improvements
- 🔧 **Fixed AI Agent Context** - Agent now properly understands conversation history
- 📈 **Increased Processing Limits** - `max_iterations=8`, `max_execution_time=25s`
- 🔄 **Enhanced Fallback Logic** - Better parameter extraction from history
- 🎵 **Genre Normalization** - Automatic translation to English (електро → electronic)

### 🗄️ Database

#### Unified Migration
- ✅ **Single Migration File** - `DATABASE_MIGRATION_COMPLETE_v2.sql`
- 📊 **All Tables Included**
  - Users, Workouts, Playlists
  - Conversations (chat history)
  - Error logs
- 🔒 **RLS Policies** - Security policies for all tables
- 📈 **Performance Indexes** - Optimized queries

#### Removed Files
- 🗑️ Deleted 9 outdated SQL migration files
- 🗑️ Deleted 13 obsolete documentation files
  - Old migration plans
  - Legacy documentation
  - Duplicate files

### 🐛 Bug Fixes

#### Critical Fixes (v3.2)
- ✅ Fixed `BaseTool.__call__()` error - Separated internal function from LangChain tool
- ✅ Fixed genre recognition - Added fuzzy matching for variations
- ✅ Fixed genre accumulation - Genres now properly merge instead of replace
- ✅ Fixed workout type parsing - "фартлек" now correctly recognized
- ✅ Fixed iteration timeout - Optimized limits to prevent agent failures

#### Context Understanding (v3.3)
- ✅ Fixed empty `collected_parameters` - Enhanced fallback logic
- ✅ Fixed repeated questions - AI now checks chat history
- ✅ Fixed parameter loss - Agent properly merges new info with existing
- ✅ Fixed timeout before processing - Increased iteration/time limits

### 📚 Documentation Updates

#### README Files
- 📄 **Root README.md** - Updated with v3.3 features and status
- 🔌 **Backend README.md** - Added database setup, features, API endpoints
- 🌐 **Web README.md** - Added 6-step flow, technical features, tech stack
- 📱 **Mobile README.md** - Added mobile-specific features and tech stack

#### Structure
- 📋 Reorganized documentation links
- ✅ Added feature status checklist
- 🗄️ Updated migration instructions
- 🎯 Clarified MVP completion

### 🔧 Technical Changes

#### AI Agent System
- 🤖 **Prompt Optimization** - Added "WORK FAST & EFFICIENT" instructions
- 🎯 **Context Builder** - Explicit step indicators and instructions
- 📝 **Self-Parsing** - AI agent handles all parameter extraction via prompt
- 🔄 **Minimal Fallback** - Code-based parsing only for critical failures

#### API Changes
- 📊 **New Analytics Endpoints**
  - `GET /analytics/conversation-insights` - Aggregated conversation data
  - `GET /analytics/user-patterns/{user_id}` - User preference analysis
  - `GET /analytics/recommendations` - AI-driven recommendations
- 💬 **Enhanced Chat Endpoint**
  - Returns created workout object
  - Includes completion status

#### Frontend Changes
- 🔄 **Automatic History Update** - `refreshTrigger` state for manual refresh
- ⚡ **Workout Activation** - `activeWorkout` and `activeWorkoutId` state
- 🎵 **Playlist Question Flow** - `showPlaylistQuestion` for better UX

---

## Version 3.2 - Agent Fixes & Optimization (November 2025)

### 🐛 Critical Bug Fixes
- Fixed tool invocation error in `SupervisorAgent`
- Fixed genre recognition (electric → electronic)
- Fixed workout type parsing (фартлек)
- Fixed agent iteration/time limits

### ⚡ Performance Optimizations
- Reduced max_iterations from 10 to 5
- Reduced max_execution_time from 30s to 15s
- Added fuzzy genre matching
- Improved fallback response logic

---

## Version 3.1 - Core Features (November 2025)

### ✨ Features
- AI chat interface with natural language processing
- Dual playlist variant generation
- Spotify integration (OAuth + playlist saving)
- Workout and playlist history
- BPM matching to workout intensity
- Genre-based track selection

---

## Version 3.0 - Multi-Agent Architecture (October 2025)

### 🏗️ Architecture
- LangChain-based multi-agent system
- SupervisorAgent orchestration
- WorkoutBuilder, WorkoutManager, MusicCurator agents
- Conversation state management

---

## Version 2.0 - MVP Foundation (September 2025)

### 🎯 Initial MVP
- Basic FastAPI backend
- React web frontend
- Spotify API integration
- PostgreSQL database (Supabase)
- Simple playlist generation

---

**Current Version:** 3.3
**Status:** ✅ MVP Complete, actively developing new features
**Next Focus:** Mobile app completion, advanced analytics

