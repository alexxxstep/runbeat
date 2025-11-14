# 📊 RunBeat - Детальний звіт по архітектурі проекту

**Дата:** 2025-11-14
**Версія:** 2.0
**Статус:** Production Ready

---

## 📋 Зміст

1. [Загальний огляд](#загальний-огляд)
2. [Архітектура системи](#архітектура-системи)
3. [Backend архітектура](#backend-архітектура)
4. [Frontend архітектура](#frontend-архітектура)
5. [База даних](#база-даних)
6. [Потоки даних](#потоки-даних)
7. [Multi-Agent система](#multi-agent-система)
8. [Технологічний стек](#технологічний-стек)
9. [Deployment архітектура](#deployment-архітектура)

---

## 🎯 Загальний огляд

RunBeat - це AI-powered система для генерації персоналізованих плейлистів для бігу через природну розмову з користувачем.

### Основні можливості:

- 🤖 AI-асистент для розмови з користувачем
- 🎵 Генерація плейлистів на основі параметрів тренування
- 🏃 Підтримка різних типів тренувань (стабільна, інтервальна, фартлек)
- 📱 Адаптивний веб-інтерфейс
- 🔗 Інтеграція з Spotify API
- 💾 Збереження історії тренувань та плейлистів

---

## 🏗️ Архітектура системи

### Високорівнева схема

```
┌─────────────────────────────────────────────────────────────────┐
│                         Користувач                               │
│                    (Web Browser / Mobile)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS
                             │
                             v
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (React)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  ChatPage    │  │  HistoryPage │  │  PlayerPage  │          │
│  │              │  │              │  │              │          │
│  │ • useChat    │  │ • useHistory │  │ • usePlayer  │          │
│  │ • Messages   │  │ • Workouts   │  │ • Spotify    │          │
│  │ • Input      │  │ • Playlists  │  │   Player     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ REST API
                             │
                             v
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              API Routes                                  │   │
│  │  /api/v1/chat/message                                    │   │
│  │  /api/v1/workouts                                        │   │
│  │  /api/v1/playlists                                       │   │
│  │  /api/v1/auth/spotify                                    │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                          │
│                       v                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         ConversationManager                              │   │
│  │  • State Machine                                         │   │
│  │  • Context Management                                    │   │
│  │  • Multi-turn Conversations                              │   │
│  │  • ConversationOrchestrator (Supervisor) Integration     │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                          │
│                       v                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │     ConversationOrchestrator (Supervisor)                │   │
│  │  • Routes messages to appropriate agents                 │   │
│  │  • Coordinates multi-agent workflow                      │   │
│  │  • Manages conversation state                            │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                          │
│         ┌─────────────┴─────────────┐                           │
│         │                           │                           │
│         v                           v                           │
│  ┌──────────────┐          ┌──────────────┐                    │
│  │ LangChain    │          │ Fallback     │                    │
│  │ Agents       │          │ (if needed)  │                    │
│  │              │          │              │                    │
│  │ • Parser     │          │ • Legacy     │                    │
│  │ • Curator    │          │   Parser     │                    │
│  │ • Manager    │          │ • LLMService │                    │
│  │ • Conversation│         │              │                    │
│  └──────────────┘          └──────────────┘                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                v            v            v
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   Supabase   │ │   OpenAI     │ │   Spotify    │
    │  PostgreSQL  │ │   GPT-4      │ │     API      │
    │              │ │              │ │              │
    │ • users      │ │ • Parsing    │ │ • Search     │
    │ • workouts   │ │ • Generation │ │ • Playlists  │
    │ • playlists  │ │              │ │ • Tracks     │
    │ • convos     │ │              │ │              │
    └──────────────┘ └──────────────┘ └──────────────┘
```

---

## 🔧 Backend архітектура

### Структура директорій

```
apps/backend/app/
├── main.py                    # FastAPI application entry point
├── core/
│   └── config.py              # Configuration & settings
├── api/
│   └── routes/
│       ├── chat.py            # Chat endpoints
│       ├── workouts.py        # Workout CRUD
│       ├── playlists.py       # Playlist management
│       ├── auth.py            # Authentication
│       └── users.py           # User management
├── services/
│   ├── conversation_manager.py    # Main conversation orchestrator
│   ├── llm_service.py             # OpenAI integration
│   ├── spotify_service.py         # Spotify API client
│   ├── supabase_service.py        # Database client
│   ├── workout_parser_agent.py    # Legacy parser agent
│   ├── playlist_generator.py      # Playlist generation logic
│   └── parsers/
│       └── rule_based_parser.py   # Rule-based parsing
├── agents/                        # LangChain multi-agent system
│   ├── base.py                    # Base agent class
│   ├── parser.py                  # WorkoutParserAgent
│   ├── curator.py                 # MusicCuratorAgent
│   ├── conversation.py            # ConversationAgent
│   ├── manager.py                 # WorkoutManagerAgent
│   ├── supervisor.py              # ConversationOrchestrator
│   ├── tools/                     # Agent tools
│   │   ├── parser_tools.py
│   │   ├── spotify_tools.py
│   │   ├── database_tools.py
│   │   └── workout_tools.py
│   └── prompts/                   # Agent prompts
│       ├── parser_prompts.py
│       ├── curator_prompts.py
│       ├── conversation_prompts.py
│       └── manager_prompts.py
├── schemas/
│   ├── chat.py                    # Chat request/response
│   ├── llm_responses.py           # Pydantic models for LLM
│   ├── workout.py                 # Workout schemas
│   └── playlist.py                # Playlist schemas
└── models/
    ├── workout.py                 # Workout domain model
    └── playlist.py                # Playlist domain model
```

### Детальна схема Backend компонентів

```
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                         │
│                         (main.py)                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             v
┌─────────────────────────────────────────────────────────────────┐
│                      API Routes Layer                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  /api/v1/chat/message                                    │   │
│  │  ├── POST /message          → ChatRequest                │   │
│  │  ├── GET  /conversation/:id → Get conversation           │   │
│  │  └── DELETE /conversation/:id → Delete conversation      │   │
│  │                                                           │   │
│  │  /api/v1/workouts                                        │   │
│  │  ├── GET    /              → List workouts               │   │
│  │  ├── POST   /              → Create workout              │   │
│  │  ├── GET    /:id           → Get workout                 │   │
│  │  ├── PUT    /:id           → Update workout              │   │
│  │  └── DELETE /:id           → Delete workout              │   │
│  │                                                           │   │
│  │  /api/v1/playlists                                       │   │
│  │  ├── GET    /              → List playlists              │   │
│  │  ├── POST   /generate      → Generate playlist           │   │
│  │  └── GET    /:id           → Get playlist                │   │
│  │                                                           │   │
│  │  /api/v1/auth/spotify                                    │   │
│  │  ├── GET  /login          → Initiate OAuth               │   │
│  │  └── GET  /callback       → OAuth callback               │   │
│  └───────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             v
┌─────────────────────────────────────────────────────────────────┐
│                  ConversationManager                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  State Machine:                                          │   │
│  │                                                           │   │
│  │  NEW ──→ PARSING_INTENT ──→ NEEDS_CLARIFICATION         │   │
│  │   │                              │                        │   │
│  │   │                              │                        │   │
│  │   └──────────────────────────────┘                        │   │
│  │                              │                            │   │
│  │                              v                            │   │
│  │  ASK_WORKOUT_CONFIRMATION ──→ COMPLETE                   │   │
│  │                              │                            │   │
│  │                              v                            │   │
│  │  GENERATING_PLAYLIST ───────→ COMPLETE                   │   │
│  │                                                           │   │
│  │  Features:                                                │   │
│  │  • Multi-turn context preservation                        │   │
│  │  • Intelligent follow-up questions                        │   │
│  │  • Conversation history storage                           │   │
│  │  • Workout confirmation flow                              │   │
│  └────────────────────┬──────────────────────────────────────┘   │
│                       │                                          │
│         ┌─────────────┴─────────────┐                           │
│         │                           │                           │
│         v                           v                           │
│  ┌──────────────┐          ┌──────────────┐                    │
│  │ LangChain    │          │ Legacy       │                    │
│  │ System       │          │ System       │                    │
│  │              │          │              │                    │
│  │ (Feature     │          │ (Default)    │                    │
│  │  Flags)      │          │              │                    │
│  └──────────────┘          └──────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### ConversationManager - Детальна схема

```
┌─────────────────────────────────────────────────────────────────┐
│                    ConversationManager                           │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  process_message(user_id, message, conversation_id)      │   │
│  │                                                           │   │
│  │  1. Get/Create conversation                              │   │
│  │  2. Add user message to history                          │   │
│  │  3. Check if Supervisor enabled                          │   │
│  │     ├── Yes → Use ConversationOrchestrator               │   │
│  │     │   └──→ Routes to appropriate agent                 │   │
│  │     └── No  → Direct agent integration                   │   │
│  │  4. Check for greetings/general questions                │   │
│  │     └──→ Use ConversationAgent                           │   │
│  │  5. Parse intent (WorkoutParserAgent)                    │   │
│  │  6. Decide next action                                   │   │
│  │     ├── Intent complete?                                 │   │
│  │     │   ├── Yes → Ask for confirmation                   │   │
│  │     │   └── No  → Ask clarification                      │   │
│  │     └── User confirmed?                                  │   │
│  │         └──→ WorkoutManagerAgent → Create workout        │   │
│  │         └──→ MusicCuratorAgent → Generate playlist       │   │
│  │  7. Save conversation                                    │   │
│  │  8. Return response                                      │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Agent Integration:                                       │   │
│  │                                                           │   │
│  │  • ConversationOrchestrator (Supervisor)                  │   │
│  │    └──→ Coordinates all agents                            │   │
│  │                                                           │   │
│  │  • ConversationAgent                                      │   │
│  │    └──→ Handles greetings & general questions             │   │
│  │                                                           │   │
│  │  • WorkoutParserAgent (LangChain)                         │   │
│  │    └──→ Hybrid parsing (rule-based + AI)                  │   │
│  │                                                           │   │
│  │  • WorkoutManagerAgent (LangChain)                        │   │
│  │    └──→ Creates & activates workouts                      │   │
│  │                                                           │   │
│  │  • MusicCuratorAgent (LangChain)                          │   │
│  │    └──→ Generates playlists with Spotify tools            │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Multi-Agent система

### Архітектура LangChain агентів

```
┌─────────────────────────────────────────────────────────────────┐
│              ConversationOrchestrator (Supervisor)               │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  process_message()                                       │   │
│  │                                                           │   │
│  │  Routes based on state:                                  │   │
│  │                                                           │   │
│  │  • new / needs_clarification                             │   │
│  │    └──→ ConversationAgent                                │   │
│  │        • Handles greetings ("привіт", "ти хто")         │   │
│  │        • Asks clarifying questions                       │   │
│  │        • Maintains conversation context                  │   │
│  │                                                           │   │
│  │  • intent_ready                                          │   │
│  │    └──→ WorkoutParserAgent                               │   │
│  │        • Hybrid parsing (rule-based + AI)                │   │
│  │        • Extracts workout parameters                     │   │
│  │        • Validates intent completeness                   │   │
│  │                                                           │   │
│  │  • workout_confirmation                                  │   │
│  │    └──→ WorkoutManagerAgent                              │   │
│  │        • Creates workout in database                     │   │
│  │        • Activates workout                               │   │
│  │        • Returns workout_id                              │   │
│  │                                                           │   │
│  │  • workout_created                                       │   │
│  │    └──→ MusicCuratorAgent                                │   │
│  │        • Generates playlist with Spotify tools           │   │
│  │        • Matches BPM to workout                          │   │
│  │        • Creates playlist in Spotify                     │   │
│  └───────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        v                    v                    v
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Conversation │    │   Parser     │    │   Curator    │
│    Agent     │    │    Agent     │    │    Agent     │
│              │    │              │    │              │
│ • Natural    │    │ • Hybrid     │    │ • Playlist   │
│   language   │    │   parsing    │    │   generation │
│ • Questions  │    │ • Rule-based │    │ • BPM        │
│ • Context    │    │   + AI       │    │   matching   │
│ • Greetings  │    │ • Validation │    │ • Spotify    │
│              │    │ • Tools      │    │ • Tools      │
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                             v
                    ┌──────────────┐
                    │   Manager    │
                    │    Agent     │
                    │              │
                    │ • Create     │
                    │   workout    │
                    │ • Activate   │
                    │ • Database   │
                    │ • Tools      │
                    └──────────────┘
```

### WorkoutParserAgent - Детальна схема

```
┌─────────────────────────────────────────────────────────────────┐
│                    WorkoutParserAgent                            │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  parse(message, conversation_history)                    │   │
│  │                                                           │   │
│  │  1. Try Rule-Based Parser first                          │   │
│  │     └──→ RuleBasedParser.parse()                         │   │
│  │         ├── Extract duration (regex)                     │   │
│  │         ├── Extract intensity (keywords)                 │   │
│  │         ├── Extract workout_type (keywords)              │   │
│  │         ├── Extract music_genres (keywords)              │   │
│  │         └── Extract music_prompt (text)                  │   │
│  │                                                           │   │
│  │  2. If rule-based fails or incomplete:                   │   │
│  │     └──→ AI Parsing (LangChain Agent)                    │   │
│  │         ├── Use structured chat agent                    │   │
│  │         ├── Tools: rule_based_parse, validate_intent     │   │
│  │         └── Output: WorkoutIntent (Pydantic)             │   │
│  │                                                           │   │
│  │  3. Merge results                                        │   │
│  │  4. Return WorkoutIntent                                 │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Tools:                                                           │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ rule_based_parse │  │ validate_intent  │                     │
│  │                  │  │                  │                     │
│  │ • Fast           │  │ • Check required │                     │
│  │ • Regex-based    │  │   fields         │                     │
│  │ • Low cost       │  │ • Validate BPM   │                     │
│  └──────────────────┘  └──────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

### MusicCuratorAgent - Детальна схема

```
┌─────────────────────────────────────────────────────────────────┐
│                    MusicCuratorAgent                             │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  generate_playlist(workout_intent, user_id, preferences) │   │
│  │                                                           │   │
│  │  1. Analyze workout requirements                         │   │
│  │     ├── Duration                                         │   │
│  │     ├── BPM range                                        │   │
│  │     ├── Workout type                                     │   │
│  │     └── Music preferences (genres, prompt)               │   │
│  │                                                           │   │
│  │  2. Use LangChain Agent with tools:                      │   │
│  │     ├── search_spotify_tracks()                          │   │
│  │     ├── get_spotify_recommendations()                    │   │
│  │     ├── calculate_bpm_progression()                      │   │
│  │     ├── get_user_preferences()                           │   │
│  │     └── get_user_music_history()                         │   │
│  │                                                           │   │
│  │  3. Generate playlist structure:                         │   │
│  │     ├── Warm-up phase (lower BPM)                        │   │
│  │     ├── Main workout (target BPM)                        │   │
│  │     └── Cool-down phase (lower BPM)                      │   │
│  │                                                           │   │
│  │  4. Output: PlaylistResponse (Pydantic)                  │   │
│  │     ├── tracks: List[PlaylistTrack]                      │   │
│  │     ├── bpm_range: [min, max]                            │   │
│  │     ├── total_tracks: int                                │   │
│  │     ├── total_duration_minutes: float                    │   │
│  │     └── curation_notes: str                              │   │
│  │                                                           │   │
│  │  5. Fallback: Use legacy LLMService if agent fails       │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💻 Frontend архітектура

### Структура Frontend

```
apps/web/src/
├── main.tsx                    # Entry point
├── App.tsx                     # Root component with routing
├── pages/
│   ├── ChatPage.tsx            # Main chat interface
│   ├── HistoryPage.tsx         # Workout & playlist history
│   ├── PlayerPage.tsx          # Spotify player
│   └── LoginPage.tsx           # Authentication
├── components/
│   ├── Chat/
│   │   ├── MessageBubble.tsx   # Message display
│   │   ├── InputBar.tsx        # Message input
│   │   ├── TypingIndicator.tsx # Loading indicator
│   │   ├── PlaylistHistorySidebar.tsx  # History sidebar
│   │   └── SettingsSidebar.tsx # Workout settings
│   ├── Player/
│   │   └── TrackCard.tsx       # Track display
│   └── Shared/
│       ├── Button.tsx
│       ├── LoadingSpinner.tsx
│       └── ErrorDisplay.tsx
├── hooks/
│   ├── useChat.ts              # Chat logic & state
│   ├── useAuth.ts              # Authentication
│   ├── usePlaylist.ts          # Playlist management
│   ├── usePlaylistHistory.ts   # History management
│   └── useWorkoutHistory.ts    # Workout history
├── services/
│   ├── api.ts                  # API client
│   └── supabase.ts             # Supabase client
└── types/
    ├── index.ts                # TypeScript types
    └── settings.ts             # Settings types
```

### Frontend потік даних

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ChatPage                                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │  History     │  │    Chat      │  │  Settings    │   │   │
│  │  │  Sidebar     │  │    Area      │  │  Sidebar     │   │   │
│  │  │              │  │              │  │              │   │   │
│  │  │ • Workouts   │  │ • Messages   │  │ • Workout    │   │   │
│  │  │ • Playlists  │  │ • Input      │  │   config     │   │   │
│  │  │              │  │ • Variants   │  │ • Genres     │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  └───────────────────────────────────────────────────────────┘   │
│                       │                                           │
│                       v                                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  useChat Hook                                            │   │
│  │  • sendMessage()                                         │   │
│  │  • generatePlaylist()                                    │   │
│  │  • clearMessages()                                       │   │
│  │  • State: messages, isLoading, error                     │   │
│  └────────────────────┬──────────────────────────────────────┘   │
│                       │                                           │
│                       v                                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API Client (api.ts)                                     │   │
│  │  • POST /api/v1/chat/message                             │   │
│  │  • POST /api/v1/playlists/generate                       │   │
│  │  • GET  /api/v1/workouts                                 │   │
│  │  • GET  /api/v1/playlists                                │   │
│  └────────────────────┬──────────────────────────────────────┘   │
│                       │                                           │
│                       v                                           │
│              ┌────────────────┐                                  │
│              │  Backend API   │                                  │
│              └────────────────┘                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Адаптивний дизайн

```
Desktop (≥768px)                    Mobile (<768px)
┌─────────────────────┐            ┌──────────────┐
│ ┌───┐ ┌──────┐ ┌──┐│            │ [☰]  [⚙]    │
│ │ H │ │ Chat │ │S ││            │              │
│ │ i │ │      │ │e ││            │              │
│ │ s │ │      │ │t ││            │   Chat       │
│ │ t │ │      │ │t ││            │   Area       │
│ │   │ │      │ │i ││            │              │
│ │ W │ │      │ │n ││            │              │
│ │ o │ │      │ │g ││            │              │
│ │ r │ │      │ │s ││            │              │
│ │ k │ │      │ │  ││            │              │
│ │   │ │      │ │  ││            │              │
│ │ P │ │      │ │  ││            │              │
│ │ l │ │      │ │  ││            │              │
│ │ a │ │      │ │  ││            │              │
│ │ y │ │      │ │  ││            │              │
│ └───┘ └──────┘ └──┘│            │              │
└─────────────────────┘            └──────────────┘

• Sidebars always visible          • Sidebars hidden by default
• Full layout                      • Overlay sidebars on click
• Table view for variants          • List view for variants
```

---

## 🗄️ База даних

### Схема бази даних (Supabase PostgreSQL)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Database Schema                           │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  users                                                    │   │
│  │  ┌─────────────┬──────────────┬──────────────────────┐   │   │
│  │  │ id (PK)     │ email        │ preferences (JSONB)  │   │   │
│  │  │ spotify_*   │ created_at   │ spotify_user_id      │   │   │
│  │  └─────────────┴──────────────┴──────────────────────┘   │   │
│  └───────────────────────────────────────────────────────────┘   │
│                              │                                    │
│                              │ 1:N                                │
│                              │                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  workouts                                                 │   │
│  │  ┌─────────────┬──────────────┬──────────────────────┐   │   │
│  │  │ id (PK)     │ user_id (FK) │ type                 │   │   │
│  │  │ duration_*  │ intensity    │ hr_zones (int[])     │   │   │
│  │  │ genres      │ prompt       │ interval_stages      │   │   │
│  │  │ is_active   │ created_at   │ (JSONB)              │   │   │
│  │  └─────────────┴──────────────┴──────────────────────┘   │   │
│  └───────────────────────────────────────────────────────────┘   │
│                              │                                    │
│                              │ 1:N                                │
│                              │                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  playlists                                                │   │
│  │  ┌─────────────┬──────────────┬──────────────────────┐   │   │
│  │  │ id (PK)     │ user_id (FK) │ workout_id (FK)      │   │   │
│  │  │ spotify_*   │ total_tracks │ total_duration_*     │   │   │
│  │  │ created_at  │ tracks (JSONB)│ spotify_url         │   │   │
│  │  └─────────────┴──────────────┴──────────────────────┘   │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  conversations                                            │   │
│  │  ┌─────────────┬──────────────┬──────────────────────┐   │   │
│  │  │ id (PK)     │ user_id (FK) │ state                │   │   │
│  │  │ messages    │ workout_*    │ playlist (JSONB)     │   │   │
│  │  │ created_at  │ updated_at   │                      │   │   │
│  │  └─────────────┴──────────────┴──────────────────────┘   │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Таблиці детально

#### users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    spotify_access_token TEXT,
    spotify_refresh_token TEXT,
    spotify_user_id TEXT,
    spotify_token_expires_at TIMESTAMPTZ,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### workouts

```sql
CREATE TABLE workouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type TEXT NOT NULL,  -- 'steady', 'intervals', 'fartlek', 'progressive'
    duration_minutes INTEGER NOT NULL,
    intensity TEXT NOT NULL,  -- 'low', 'moderate', 'high'
    hr_zones INTEGER[] NOT NULL,  -- [min, max]
    interval_stages JSONB,  -- Array of interval stages
    genres TEXT[],  -- Music genres
    prompt TEXT,  -- Music search prompt
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### playlists

```sql
CREATE TABLE playlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    workout_id UUID REFERENCES workouts(id) ON DELETE SET NULL,
    spotify_playlist_id TEXT,
    spotify_url TEXT,
    total_tracks INTEGER,
    total_duration_seconds INTEGER,
    tracks JSONB,  -- Array of track objects
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### conversations

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    state TEXT NOT NULL,
    messages JSONB DEFAULT '[]',
    workout_intent JSONB,
    playlist JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🔄 Потоки даних

### Потік 1: Створення воркауту через чат

```
┌─────────┐
│  User   │
│ "хочу   │
│ пробігти│
│ 30 хв"  │
└────┬────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  Frontend: ChatPage                                          │
│  • User types message                                        │
│  • useChat.sendMessage()                                     │
└────┬─────────────────────────────────────────────────────────┘
     │
     │ POST /api/v1/chat/message
     │ { message: "хочу пробігти 30 хв", user_id: "..." }
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  Backend: /api/v1/chat/message                               │
│  • Validate request                                          │
│  • Get user preferences from DB                              │
│  • Call ConversationManager.process_message()                │
└────┬─────────────────────────────────────────────────────────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  ConversationManager                                         │
│  • Get/Create conversation                                   │
│  • Add message to history                                    │
│  • Check if Supervisor enabled → YES                         │
│  • Use ConversationOrchestrator                              │
└────┬─────────────────────────────────────────────────────────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  ConversationOrchestrator (Supervisor)                       │
│  • State: NEW                                                │
│  • Route to: ConversationAgent                               │
└────┬─────────────────────────────────────────────────────────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  ConversationAgent (LangChain)                               │
│  • Analyze message                                           │
│  • Detect: workout intent present                            │
│  • Route to: WorkoutParserAgent                              │
└────┬─────────────────────────────────────────────────────────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  WorkoutParserAgent (Hybrid)                                 │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  1. RuleBasedParser.parse()                           │   │
│  │     ├── Extract: duration = 30                        │   │
│  │     ├── Extract: workout_type = "continuous"          │   │
│  │     └── Extract: intensity = "moderate" (inferred)    │   │
│  │                                                         │   │
│  │  2. If incomplete → AI Parsing                         │   │
│  │     └──→ LangChain Agent                               │   │
│  │         └──→ OpenAI GPT-4                              │   │
│  │             └──→ WorkoutIntent (Pydantic)              │   │
│  └───────────────────────────────────────────────────────┘   │
└────┬─────────────────────────────────────────────────────────┘
     │
     │ WorkoutIntent {
     │   workout_type: "continuous",
     │   duration_minutes: 30,
     │   target_bpm_min: 130,
     │   target_bpm_max: 150,
     │   confidence: 0.9,
     │   needs_clarification: false
     │ }
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  ConversationOrchestrator                                    │
│  • Intent complete → State: workout_confirmation            │
│  • Format workout summary                                    │
│  • Return: "Створити воркаут? (Да/Ні)"                      │
└────┬─────────────────────────────────────────────────────────┘
     │
     │ Response {
     │   message: "Ось що я зрозумів: ... Створити воркаут?",
     │   workout: WorkoutIntent,
     │   state: "ask_workout_confirmation",
     │   is_complete: false
     │ }
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  Frontend: ChatPage                                          │
│  • Display AI message                                        │
│  • Show buttons: "Так" / "Ні"                                │
└─────────────────────────────────────────────────────────────┘
```

### Потік 2: Підтвердження та створення воркауту

```
┌─────────┐
│  User   │
│ Clicks  │
│ "Так"   │
└────┬────┘
     │
     │ POST /api/v1/chat/message
     │ { message: "Так", conversation_id: "..." }
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  ConversationManager                                         │
│  • State: ASK_WORKOUT_CONFIRMATION                           │
│  • Use ConversationOrchestrator                              │
└────┬─────────────────────────────────────────────────────────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  ConversationOrchestrator                                    │
│  • State: workout_confirmation                               │
│  • Route to: WorkoutManagerAgent                             │
└────┬─────────────────────────────────────────────────────────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  WorkoutManagerAgent (LangChain)                             │
│  • Parse: "Так" → is_positive = true                        │
│  • Use tools: create_workout, activate_workout              │
│  • Create workout in database                                │
│  • Activate workout                                          │
│  • Return workout_id                                         │
└────┬─────────────────────────────────────────────────────────┘
     │
     │ workout_id = "abc-123"
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  ConversationManager                                         │
│  • Update conversation state: COMPLETE                       │
│  • Return response with workout_id                           │
└────┬─────────────────────────────────────────────────────────┘
     │
     │ Response {
     │   message: "✅ Воркаут успішно створено!",
     │   workout: { id: "abc-123", ... },
     │   state: "complete",
     │   is_complete: true
     │ }
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  Frontend: ChatPage                                          │
│  • Display success message                                   │
│  • Show button: "Так, згенерувати плейлист"                 │
└─────────────────────────────────────────────────────────────┘
```

### Потік 3: Генерація плейлисту

```
┌─────────┐
│  User   │
│ Clicks  │
│ "Згенерувати│
│ плейлист"│
└────┬────┘
     │
     │ POST /api/v1/playlists/preview-variants
     │ { workout_id: "abc-123", ... }
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  Backend: /api/v1/playlists/preview-variants                 │
│  • Get workout from DB                                       │
│  • Call playlist generator                                   │
└────┬─────────────────────────────────────────────────────────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  ConversationOrchestrator                                    │
│  • State: workout_created                                    │
│  • Route to: MusicCuratorAgent                               │
└────┬─────────────────────────────────────────────────────────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  MusicCuratorAgent (LangChain)                               │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  1. Analyze workout requirements                     │   │
│  │  2. Use LangChain Agent with tools:                  │   │
│  │     ├── search_spotify_tracks()                       │   │
│  │     ├── get_spotify_recommendations()                 │   │
│  │     ├── calculate_bpm_progression()                   │   │
│  │     ├── get_user_preferences()                        │   │
│  │     └── get_user_music_history()                      │   │
│  │  3. Generate playlist structure                       │   │
│  │  4. Output: PlaylistResponse (Pydantic)               │   │
│  │  5. Create playlist in Spotify                        │   │
│  └───────────────────────────────────────────────────────┘   │
└────┬─────────────────────────────────────────────────────────┘
     │
     │ PlaylistResponse {
     │   tracks: [Track, ...],
     │   bpm_range: [130, 150],
     │   total_tracks: 15,
     │   total_duration_minutes: 45.5
     │ }
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  Frontend: ChatPage                                          │
│  • Display 2 variants                                        │
│  • User selects variant                                      │
│  • Call generatePlaylist()                                   │
└────┬─────────────────────────────────────────────────────────┘
     │
     │ POST /api/v1/playlists/generate
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  Backend: Generate & Create Spotify Playlist                 │
│  • Create playlist in Spotify                                │
│  • Add tracks                                                │
│  • Save to DB                                                │
│  • Return spotify_url                                        │
└────┬─────────────────────────────────────────────────────────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  Frontend: ChatPage                                          │
│  • Display playlist with "Open in Spotify" button            │
│  • User clicks → Opens Spotify app                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Технологічний стек

### Backend Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    Backend Technology Stack                   │
├─────────────────────────────────────────────────────────────┤
│ Framework:        FastAPI 0.104.1                            │
│ Language:         Python 3.11+                               │
│ ASGI Server:      Uvicorn                                    │
│                                                                 │
│ AI/LLM:                                                       │
│   • OpenAI GPT-4  (via openai==1.7.2)                        │
│   • LangChain     (via langchain, langchain-openai)          │
│                                                                 │
│ Database:                                                     │
│   • Supabase      (PostgreSQL via supabase==2.3.0)           │
│                                                                 │
│ External APIs:                                                │
│   • Spotify API   (via spotipy==2.23.0)                      │
│                                                                 │
│ Validation:                                                   │
│   • Pydantic v2   (Data validation & serialization)          │
│                                                                 │
│ Utilities:                                                    │
│   • loguru        (Logging)                                  │
│   • httpx         (HTTP client)                              │
│   • python-dotenv (Environment variables)                    │
│                                                                 │
│ Testing:                                                      │
│   • pytest        (Testing framework)                        │
│   • pytest-asyncio (Async testing)                           │
└─────────────────────────────────────────────────────────────┘
```

### Frontend Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Technology Stack                  │
├─────────────────────────────────────────────────────────────┤
│ Framework:        React 18.2.0                               │
│ Build Tool:       Vite                                       │
│ Language:         TypeScript                                 │
│                                                                 │
│ Routing:          React Router v6                            │
│                                                                 │
│ Styling:          Tailwind CSS                               │
│                                                                 │
│ State Management:                                             │
│   • React Hooks   (useState, useEffect, useCallback)         │
│   • Custom Hooks  (useChat, useAuth, usePlaylist)            │
│                                                                 │
│ HTTP Client:      Axios                                      │
│                                                                 │
│ Authentication:   Supabase Auth                              │
│                                                                 │
│ UI Components:    Custom components                          │
│   • MessageBubble                                             │
│   • InputBar                                                  │
│   • Sidebars                                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Deployment архітектура

### Railway Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                    Railway Platform                          │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  Backend Service (FastAPI)                            │   │
│  │  • Runtime: Python 3.11                               │   │
│  │  • Build: pip install -r requirements.txt             │   │
│  │  • Start: uvicorn app.main:app --host 0.0.0.0         │   │
│  │  • Port: $PORT (Railway assigned)                     │   │
│  │  • Environment: Production                             │   │
│  └───────────────────────────────────────────────────────┘   │
│                       │                                       │
│                       v                                       │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  Frontend Service (React)                             │   │
│  │  • Runtime: Node.js 18                                │   │
│  │  • Build: npm install && npm run build                │   │
│  │  • Start: npx serve -s dist -l $PORT                  │   │
│  │  • Static files served from dist/                     │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                               │
│  Environment Variables:                                       │
│  • SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY     │
│  • SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET                  │
│  • OPENAI_API_KEY                                            │
│  • USE_LANGCHAIN_PARSER, USE_LANGCHAIN_CURATOR               │
└─────────────────────────────────────────────────────────────┘
```

### External Services

```
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Supabase   │  │    OpenAI    │  │   Spotify    │      │
│  │              │  │              │  │              │      │
│  │ • PostgreSQL │  │ • GPT-4 API  │  │ • Web API    │      │
│  │ • Auth       │  │ • Structured │  │ • OAuth 2.0  │      │
│  │ • Storage    │  │   Outputs    │  │ • Playlists  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 Feature Flags

### Поточна конфігурація (Production)

```python
# apps/backend/app/core/config.py

USE_LANGCHAIN_PARSER: bool = True       # ✅ LangChain WorkoutParserAgent enabled
USE_LANGCHAIN_CURATOR: bool = True      # ✅ LangChain MusicCuratorAgent enabled
USE_LANGCHAIN_SUPERVISOR: bool = True   # ✅ ConversationOrchestrator (Supervisor) enabled
```

**Статус:** Повна міграція на LangChain multi-agent систему завершена ✅

### Можливі конфігурації

```
┌─────────────────────────────────────────────────────────────┐
│                    Feature Flag Combinations                 │
├─────────────────────────────────────────────────────────────┤
│ Configuration 1: Legacy (Fallback)                          │
│   • USE_LANGCHAIN_PARSER = False                            │
│   • USE_LANGCHAIN_CURATOR = False                           │
│   • USE_LANGCHAIN_SUPERVISOR = False                        │
│   → Uses: LegacyWorkoutParserAgent + LLMService             │
│                                                                 │
│ Configuration 2: Hybrid Parser                               │
│   • USE_LANGCHAIN_PARSER = True                             │
│   • USE_LANGCHAIN_CURATOR = False                           │
│   • USE_LANGCHAIN_SUPERVISOR = False                        │
│   → Uses: LangChainWorkoutParserAgent + LLMService          │
│                                                                 │
│ Configuration 3: Full LangChain Agents                       │
│   • USE_LANGCHAIN_PARSER = True                             │
│   • USE_LANGCHAIN_CURATOR = True                            │
│   • USE_LANGCHAIN_SUPERVISOR = False                        │
│   → Uses: LangChainWorkoutParserAgent + MusicCuratorAgent   │
│   → Direct agent integration in ConversationManager         │
│                                                                 │
│ Configuration 4: Full Multi-Agent System (CURRENT) ✅        │
│   • USE_LANGCHAIN_PARSER = True                             │
│   • USE_LANGCHAIN_CURATOR = True                            │
│   • USE_LANGCHAIN_SUPERVISOR = True                         │
│   → Uses: ConversationOrchestrator (Supervisor)             │
│   → Coordinates: ConversationAgent, WorkoutParserAgent,     │
│                  WorkoutManagerAgent, MusicCuratorAgent     │
│   → Full LangChain multi-agent orchestration                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Безпека

### Authentication Flow

```
┌─────────┐
│  User   │
└────┬────┘
     │
     │ 1. Click "Login with Spotify"
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  Frontend: LoginPage                                         │
│  • Redirect to: /api/v1/auth/spotify/login                  │
└────┬─────────────────────────────────────────────────────────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  Backend: /api/v1/auth/spotify/login                         │
│  • Generate OAuth state                                      │
│  • Redirect to Spotify OAuth                                 │
└────┬─────────────────────────────────────────────────────────┘
     │
     │ Redirect to Spotify
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  Spotify OAuth                                               │
│  • User authorizes                                           │
│  • Redirect to: /auth/callback?code=...                     │
└────┬─────────────────────────────────────────────────────────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  Backend: /api/v1/auth/spotify/callback                      │
│  • Exchange code for tokens                                  │
│  • Get user info from Spotify                                │
│  • Create/Update user in Supabase                            │
│  • Generate Supabase session                                 │
│  • Return session to frontend                                │
└────┬─────────────────────────────────────────────────────────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  Frontend: AuthCallbackPage                                  │
│  • Store session                                             │
│  • Redirect to ChatPage                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Метрики та моніторинг

### Ключові метрики

```
┌─────────────────────────────────────────────────────────────┐
│                    Performance Metrics                       │
├─────────────────────────────────────────────────────────────┤
│ Parsing:                                                     │
│   • Rule-based success rate:    ~70%                        │
│   • AI parsing fallback:        ~30%                        │
│   • Average parse time:         <500ms (rule) / <2s (AI)   │
│                                                                 │
│ Conversation:                                                │
│   • Average turns to complete:  2-3                         │
│   • Intent completion rate:     >90%                        │
│                                                                 │
│ Playlist Generation:                                         │
│   • Generation time:            <8s                         │
│   • Track match rate:           >85%                        │
│   • Spotify playlist creation:  <3s                         │
│                                                                 │
│ User Experience:                                             │
│   • Time to first playlist:     <15s                        │
│   • User satisfaction:          TBD                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Висновки

### Поточна архітектура (Повна міграція на LangChain)

1. **✅ Повна LangChain інтеграція**: Всі агенти використовують LangChain
2. **✅ Multi-Agent система**: ConversationOrchestrator (Supervisor) координує всіх агентів
3. **✅ ConversationAgent**: Обробка привітань та загальних питань
4. **✅ Гібридний парсинг**: Rule-based + AI для оптимальної швидкості та точності
5. **✅ Модульність**: Чітке розділення відповідальностей між агентами
6. **✅ Адаптивність**: Frontend працює на всіх пристроях
7. **✅ Надійність**: Fallback механізми на всіх рівнях

### Переваги поточної архітектури

✅ **Повна LangChain інтеграція**: Всі агенти використовують LangChain framework
✅ **Supervisor Pattern**: ConversationOrchestrator координує workflow
✅ **Спеціалізовані агенти**: Кожен агент має чітку роль та інструменти
✅ **Гібридний парсинг**: Rule-based для швидкості + AI для точності
✅ **Природна мова**: ConversationAgent обробляє привітання та питання
✅ **Масштабованість**: Легко додавати нові агенти та інструменти
✅ **Тестованість**: Кожен агент може тестуватися окремо
✅ **Fallback механізми**: Legacy система доступна як резерв

### Активні компоненти

✅ **ConversationOrchestrator (Supervisor)** - Координує всіх агентів
✅ **ConversationAgent** - Обробка привітань, питань, контексту
✅ **WorkoutParserAgent** - Гібридний парсинг workout intent
✅ **WorkoutManagerAgent** - Створення та активація воркаутів
✅ **MusicCuratorAgent** - Генерація плейлистів з Spotify інтеграцією

### Майбутні покращення

🔮 **Додавання моніторингу та логування** (LangSmith integration)
🔮 **Кешування для оптимізації** (Redis для агентів)
🔮 **Batch processing для плейлистів**
🔮 **A/B тестування різних агентів**
🔮 **Streaming responses** для кращого UX
🔮 **Agent memory persistence** для довготривалих розмов

---

---

## 📐 Детальні схеми взаємодії

### Схема взаємодії компонентів при парсингу

```
User Message: "хочу легку пробіжку 55 хвилин"
                    │
                    v
┌─────────────────────────────────────────────────────────────┐
│  ConversationManager._parse_user_intent()                   │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  WorkoutParserAgent.parse()                           │   │
│  │                                                         │   │
│  │  Step 1: RuleBasedParser.parse()                      │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │  _extract_duration("55 хвилин")                 │   │   │
│  │  │    → duration_minutes = 55                       │   │   │
│  │  │                                                    │   │   │
│  │  │  _extract_intensity("легку")                     │   │   │
│  │  │    → intensity = "low"                           │   │   │
│  │  │    → target_bpm_min = 110                        │   │   │
│  │  │    → target_bpm_max = 130                        │   │   │
│  │  │                                                    │   │   │
│  │  │  _extract_workout_type("пробіжку")               │   │   │
│  │  │    → workout_type = "continuous"                 │   │   │
│  │  │                                                    │   │   │
│  │  │  Result: Complete intent (confidence: 0.9)       │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │   │
│  │                                                         │   │   │
│  │  Step 2: If incomplete → AI Parsing                   │   │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │   │
│  │  │  LangChain Agent                                │   │   │   │
│  │  │    ├── Tools: rule_based_parse, validate_intent │   │   │   │
│  │  │    ├── Prompt: PARSER_AGENT_SYSTEM_PROMPT       │   │   │   │
│  │  │    └── Output Parser: WorkoutIntent (Pydantic)  │   │   │   │
│  │  │                                                    │   │   │   │
│  │  │  OpenAI GPT-4                                    │   │   │   │
│  │  │    └──→ Structured JSON output                   │   │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │   │
│  │                                                         │   │   │
│  │  Step 3: Merge & Validate                              │   │   │
│  │    └──→ Return WorkoutIntent                          │   │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                    │
                    v
        WorkoutIntent {
          workout_type: "continuous",
          duration_minutes: 55,
          target_bpm_min: 110,
          target_bpm_max: 130,
          confidence: 0.9,
          needs_clarification: false
        }
```

### Схема генерації плейлисту

```
WorkoutIntent (confirmed by user)
                    │
                    v
┌─────────────────────────────────────────────────────────────┐
│  MusicCuratorAgent.generate_playlist()                      │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  LangChain Agent with Tools                           │   │
│  │                                                         │   │
│  │  1. Analyze Requirements                               │   │
│  │     ├── Duration: 55 min                              │   │
│  │     ├── BPM: 110-130                                  │   │
│  │     ├── Type: continuous (steady state)               │   │
│  │     └── Genres: ["Pop", "Electronic"] (if provided)   │   │
│  │                                                         │   │
│  │  2. Use Tools:                                         │   │
│  │     ├── calculate_bpm_progression()                    │   │
│  │     │   └──→ Warm-up: 100-110 BPM                     │   │
│  │     │   └──→ Main: 110-130 BPM                        │   │
│  │     │   └──→ Cool-down: 100-110 BPM                   │   │
│  │     │                                                    │   │
│  │     ├── search_spotify_tracks()                        │   │
│  │     │   └──→ Search by genre + BPM                     │   │
│  │     │                                                    │   │
│  │     ├── get_spotify_recommendations()                  │   │
│  │     │   └──→ Get recommendations based on seeds        │   │
│  │     │                                                    │   │
│  │     └── get_user_preferences()                         │   │
│  │         └──→ Get user's favorite genres/artists        │   │
│  │                                                         │   │
│  │  3. Generate Playlist Structure                        │   │
│  │     ├── Warm-up: 5 tracks, ~10 min, 100-110 BPM       │   │
│  │     ├── Main: 20 tracks, ~40 min, 110-130 BPM         │   │
│  │     └── Cool-down: 3 tracks, ~5 min, 100-110 BPM      │   │
│  │                                                         │   │
│  │  4. Output: PlaylistResponse                           │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                    │
                    v
        PlaylistResponse {
          tracks: [
            { name: "...", artist: "...", bpm: 105, phase: "warm-up" },
            ...
            { name: "...", artist: "...", bpm: 125, phase: "main" },
            ...
            { name: "...", artist: "...", bpm: 105, phase: "cool-down" }
          ],
          bpm_range: [100, 130],
          total_tracks: 28,
          total_duration_minutes: 55.2
        }
```

---

## 🔄 State Machine - Детальна схема

```
┌─────────────────────────────────────────────────────────────┐
│              Conversation State Machine                      │
│                                                               │
│  ┌─────────┐                                                 │
│  │   NEW   │ ← Initial state                                 │
│  └────┬────┘                                                 │
│       │                                                       │
│       │ User sends message                                   │
│       │                                                       │
│       v                                                       │
│  ┌─────────────────────┐                                     │
│  │ PARSING_INTENT      │                                     │
│  │                     │                                     │
│  │ • Parse message     │                                     │
│  │ • Extract intent    │                                     │
│  └────┬────────────────┘                                     │
│       │                                                       │
│       ├─── Intent incomplete? ──→ ┌─────────────────────┐   │
│       │                            │ NEEDS_CLARIFICATION │   │
│       │                            │                     │   │
│       │                            │ • Ask question      │   │
│       │                            │ • Wait for answer   │   │
│       │                            └────┬────────────────┘   │
│       │                                 │                     │
│       │                                 │ User responds       │
│       │                                 │                     │
│       │                                 └───→ (back to NEW)  │
│       │                                                       │
│       └─── Intent complete? ──→ ┌─────────────────────────┐ │
│                                  │ ASK_WORKOUT_CONFIRMATION│ │
│                                  │                         │ │
│                                  │ • Show summary          │ │
│                                  │ • Ask "Да/Ні"          │ │
│                                  └────┬────────────────────┘ │
│                                       │                       │
│                                       ├─── "Ні" ──→ ┌──────┐ │
│                                       │             │COMPLETE│
│                                       │             └──────┘ │
│                                       │                       │
│                                       └─── "Да" ──→ ┌──────┐ │
│                                                     │CREATE │ │
│                                                     │WORKOUT│ │
│                                                     └────┬──┘ │
│                                                          │     │
│                                                          v     │
│                                                  ┌──────────┐ │
│                                                  │ COMPLETE │ │
│                                                  │          │ │
│                                                  │ • Workout│ │
│                                                  │   created│ │
│                                                  │ • Ready  │ │
│                                                  │   for    │ │
│                                                  │   playlist│ │
│                                                  └──────────┘ │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  GENERATING_PLAYLIST (optional)                       │   │
│  │  • User requests playlist generation                  │   │
│  │  • Generate playlist                                  │   │
│  │  • Create in Spotify                                  │   │
│  │  • Save to database                                   │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 Frontend Component Hierarchy

```
App
├── Routes
│   ├── / (ChatPage)
│   │   ├── PlaylistHistorySidebar
│   │   │   ├── WorkoutList
│   │   │   └── PlaylistList
│   │   │
│   │   ├── ChatArea
│   │   │   ├── MessageList
│   │   │   │   └── MessageBubble (×N)
│   │   │   ├── VariantSelector (if variants shown)
│   │   │   └── TypingIndicator
│   │   │
│   │   ├── InputBar
│   │   │   ├── TextInput
│   │   │   └── SendButton
│   │   │
│   │   └── SettingsSidebar
│   │       ├── WorkoutTypeSelector
│   │       ├── DurationSliders
│   │       ├── IntensitySelector
│   │       ├── HRZoneSliders
│   │       ├── GenreSelector
│   │       ├── PromptInput
│   │       └── SaveButton
│   │
│   ├── /history (HistoryPage)
│   ├── /player/:id (PlayerPage)
│   └── /login (LoginPage)
│
└── ProtectedRoute (Auth wrapper)
```

---

## 🔌 API Endpoints

### Chat API

```
POST /api/v1/chat/message
Request:
{
  "message": "хочу пробігти 30 хв",
  "user_id": "uuid",
  "conversation_id": "uuid" (optional)
}

Response:
{
  "message": "Ось що я зрозумів: ...",
  "workout": {
    "type": "continuous",
    "duration_minutes": 30,
    "intensity": "moderate",
    "hr_zones": [130, 150],
    "id": "uuid" (if created)
  },
  "playlist": { ... } (if generated),
  "needs_clarification": false,
  "conversation_id": "uuid",
  "is_complete": true
}
```

### Workouts API

```
GET    /api/v1/workouts?user_id=uuid
POST   /api/v1/workouts
GET    /api/v1/workouts/:id
PUT    /api/v1/workouts/:id
DELETE /api/v1/workouts/:id
```

### Playlists API

```
GET    /api/v1/playlists?user_id=uuid
POST   /api/v1/playlists/preview-variants
POST   /api/v1/playlists/generate
GET    /api/v1/playlists/:id
```

---

## 🧪 Тестування

### Backend Tests

```
apps/backend/tests/
├── test_conversation_manager.py
│   ├── test_new_conversation_creation
│   ├── test_multi_turn_conversation
│   └── test_workout_confirmation
│
├── test_rule_based_parser.py
│   ├── test_extract_duration
│   ├── test_extract_intensity
│   ├── test_extract_workout_type
│   └── test_extract_music_genres
│
├── test_workout_parser_agent.py
│   ├── test_rule_based_parsing_success
│   ├── test_ai_parsing_fallback
│   └── test_merge_results
│
└── test_langchain_parser_agent.py
    ├── test_rule_based_parsing
    ├── test_ai_parsing_fallback
    └── test_structured_output
```

---

## 📊 Data Models

### WorkoutIntent (Pydantic)

```python
class WorkoutIntent(BaseModel):
    workout_type: Literal["continuous", "intervals", "fartlek", "recovery"]
    duration_minutes: int
    target_bpm_min: int
    target_bpm_max: int
    intervals: Optional[List[IntervalPhase]] = None
    confidence: float  # 0.0 - 1.0
    needs_clarification: bool
    clarification_question: Optional[str] = None
    music_genres: Optional[List[str]] = None
    music_prompt: Optional[str] = None
```

### PlaylistResponse (Pydantic)

```python
class PlaylistResponse(BaseModel):
    tracks: List[PlaylistTrack]
    bpm_range: List[int]  # [min, max]
    total_tracks: int
    total_duration_minutes: float
    curation_notes: Optional[str] = None

class PlaylistTrack(BaseModel):
    id: str
    name: str
    artist: str
    duration_ms: int
    bpm: Optional[int] = None
    phase: Literal["warm-up", "main", "cool-down"] = "main"
```

---

## 🔐 Security & Authentication

### Authentication Flow

```
1. User clicks "Login with Spotify"
   ↓
2. Frontend redirects to /api/v1/auth/spotify/login
   ↓
3. Backend generates OAuth state & redirects to Spotify
   ↓
4. User authorizes on Spotify
   ↓
5. Spotify redirects to /api/v1/auth/spotify/callback?code=...
   ↓
6. Backend exchanges code for tokens
   ↓
7. Backend creates/updates user in Supabase
   ↓
8. Backend generates Supabase session
   ↓
9. Frontend stores session & redirects to ChatPage
```

### Authorization

- All API endpoints require `user_id` in request
- Backend verifies user ownership of resources
- Supabase RLS policies (if enabled)
- Service key used for backend operations

---

## 🚀 Performance Optimizations

### Caching Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    Caching Layers                           │
├─────────────────────────────────────────────────────────────┤
│ 1. In-Memory Cache (ConversationManager)                    │
│    • Active conversations                                    │
│    • TTL: Until conversation ends                           │
│                                                                 │
│ 2. Spotify Service Cache                                     │
│    • Track search results                                    │
│    • TTL: 1 hour                                             │
│                                                                 │
│ 3. Database Cache (Supabase)                                 │
│    • User preferences                                        │
│    • Workout history                                         │
│    • Playlist history                                        │
└─────────────────────────────────────────────────────────────┘
```

### Optimization Techniques

- **Rule-based parsing first**: Fast, low-cost parsing for common cases
- **AI parsing fallback**: Only when rule-based fails
- **Parallel requests**: Use `asyncio.gather()` for multiple API calls
- **Lazy loading**: Load conversation history only when needed
- **Debouncing**: Prevent rapid successive API calls

---

---

## 🔄 Поточний стан міграції

### Статус LangChain інтеграції

```
┌─────────────────────────────────────────────────────────────┐
│              LangChain Migration Status                      │
├─────────────────────────────────────────────────────────────┤
│ ✅ Phase 1: WorkoutParserAgent          [COMPLETED]         │
│ ✅ Phase 2: MusicCuratorAgent           [COMPLETED]         │
│ ✅ Phase 3: ConversationAgent           [COMPLETED]         │
│ ✅ Phase 4: WorkoutManagerAgent         [COMPLETED]         │
│ ✅ Phase 5: ConversationOrchestrator    [COMPLETED]         │
│ ✅ Phase 6: Full Integration            [COMPLETED]         │
│                                                               │
│ Status: 🟢 FULLY MIGRATED TO LANGCHAIN                      │
└─────────────────────────────────────────────────────────────┘
```

### Активні агенти

```
┌─────────────────────────────────────────────────────────────┐
│                    Active LangChain Agents                   │
├─────────────────────────────────────────────────────────────┤
│ 1. ConversationAgent                                        │
│    • Handles greetings & general questions                  │
│    • Maintains conversation context                         │
│    • Tools: get_user_preferences, get_conversation_history  │
│                                                               │
│ 2. WorkoutParserAgent                                       │
│    • Hybrid parsing (rule-based + AI)                       │
│    • Extracts workout parameters                            │
│    • Tools: rule_based_parse, validate_intent               │
│                                                               │
│ 3. WorkoutManagerAgent                                      │
│    • Creates & activates workouts                           │
│    • Database operations                                    │
│    • Tools: create_workout, activate_workout, get_active    │
│                                                               │
│ 4. MusicCuratorAgent                                        │
│    • Generates playlists                                    │
│    • Spotify integration                                    │
│    • Tools: search_spotify_tracks, get_recommendations,     │
│             calculate_bpm_progression                        │
│                                                               │
│ 5. ConversationOrchestrator (Supervisor)                    │
│    • Coordinates all agents                                 │
│    • Routes messages based on state                         │
│    • Manages conversation flow                              │
└─────────────────────────────────────────────────────────────┘
```

### Потік обробки повідомлення (з Supervisor)

```
User Message
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  ConversationManager.process_message()                      │
│  • Check: use_supervisor = True                             │
│  • Use: ConversationOrchestrator                            │
└────┬─────────────────────────────────────────────────────────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  ConversationOrchestrator.process_message()                 │
│  • Analyze current state                                    │
│  • Route to appropriate agent                               │
└────┬─────────────────────────────────────────────────────────┘
     │
     ├─── State: new / needs_clarification
     │    └──→ ConversationAgent
     │         • Respond to greetings/questions
     │         • Ask clarifying questions
     │         • Try to parse intent
     │
     ├─── State: intent_ready
     │    └──→ WorkoutParserAgent
     │         • Parse workout intent
     │         • Validate completeness
     │
     ├─── State: workout_confirmation
     │    └──→ WorkoutManagerAgent
     │         • Create workout if "Да"
     │         • Activate workout
     │
     └─── State: workout_created
          └──→ MusicCuratorAgent
               • Generate playlist
               • Create in Spotify
```

---

**Дата створення:** 2025-11-14
**Останнє оновлення:** 2025-11-14
**Версія документа:** 2.0
**Статус:** Актуальний - Повна міграція на LangChain завершена ✅
