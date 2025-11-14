# RunBeat AI Architecture 🏗️

## Поточна архітектура (Before)

```
┌─────────────┐
│   User      │
│  "хочу      │
│ пробігти"   │
└──────┬──────┘
       │
       v
┌──────────────────┐
│   FastAPI        │
│   /chat/message  │
└──────┬───────────┘
       │
       v
┌──────────────────────────┐
│   LLMService             │
│                          │
│  Basic prompt:           │
│  "You are JSON assistant"│
│                          │
│  Manual JSON parsing     │
│  ❌ No expertise         │
│  ❌ No validation        │
│  ❌ Single-turn only     │
└──────┬───────────────────┘
       │
       v
┌──────────────────┐
│  OpenAI GPT-4    │
└──────────────────┘
```

## Нова архітектура (After)

```
┌─────────────────────────────────────────────────┐
│                    User                          │
│  "хочу пробігти 40 хв з інтервалами"           │
└────────────────────┬────────────────────────────┘
                     │
                     v
┌────────────────────────────────────────────────┐
│              FastAPI Endpoint                   │
│           /api/v1/chat/message                  │
└────────────────────┬───────────────────────────┘
                     │
                     v
┌────────────────────────────────────────────────────────┐
│           ConversationManager (Agent 4)                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  State Machine:                                  │  │
│  │  NEW → PARSING → CLARIFICATION → GENERATING      │  │
│  │                          ↓                       │  │
│  │                      COMPLETE                    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  • Multi-turn context management                       │
│  • Intelligent follow-up questions                     │
│  • Conversation history storage                        │
└────────────────────┬───────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         v                       v
┌────────────────┐      ┌────────────────┐
│  LLMService    │      │   Database     │
│  (Updated)     │      │   (Supabase)   │
└────────┬───────┘      └────────────────┘
         │                  • conversations
         │                  • messages
         │                  • user_preferences
         v
┌─────────────────────────────────────────────┐
│           PromptBuilder (Agent 1)            │
│  ┌───────────────────────────────────────┐  │
│  │  Dynamic Prompt Construction:         │  │
│  │                                       │  │
│  │  • Workout Expert System              │  │
│  │  • Music Curator System               │  │
│  │  • User Context Injection             │  │
│  │  • Conversation History               │  │
│  └───────────────────────────────────────┘  │
└────────┬────────────────────────────────────┘
         │
         v
┌─────────────────────────────────────────────────┐
│        Expert System Prompts                     │
│                                                  │
│  ┌────────────────────┐  ┌────────────────────┐ │
│  │ workout_expert.py  │  │ music_curator.py   │ │
│  │  (Agent 1)         │  │  (Agent 3)         │ │
│  │                    │  │                    │ │
│  │ • Zone 1-5 HR/BPM  │  │ • BPM Progression  │ │
│  │ • Interval types   │  │ • Genre Selection  │ │
│  │ • Workout science  │  │ • Energy Curves    │ │
│  │ • Duration parsing │  │ • Track Selection  │ │
│  │ • Confidence calc  │  │ • Warm-up/Cool-down│ │
│  └────────────────────┘  └────────────────────┘ │
└─────────────────────────────────────────────────┘
         │
         v
┌─────────────────────────────────────────────────┐
│           OpenAI API                             │
│  ┌───────────────────────────────────────────┐  │
│  │  Structured Outputs (Agent 2)             │  │
│  │                                           │  │
│  │  response_format=WorkoutIntent            │  │
│  │  response_format=PlaylistResponse         │  │
│  │                                           │  │
│  │  ✓ Type-safe Pydantic models              │  │
│  │  ✓ Automatic validation                   │  │
│  │  ✓ No manual JSON parsing                 │  │
│  └───────────────────────────────────────────┘  │
└────────┬────────────────────────────────────────┘
         │
         v
┌─────────────────────────────────────────────────┐
│         Pydantic Models (Agent 2)                │
│  ┌───────────────────────────────────────────┐  │
│  │  class WorkoutIntent(BaseModel):          │  │
│  │      workout_type: Literal[...]           │  │
│  │      duration_minutes: int                │  │
│  │      target_bpm_min: int                  │  │
│  │      target_bpm_max: int                  │  │
│  │      intervals: List[IntervalPhase]       │  │
│  │      confidence: float                    │  │
│  │      needs_clarification: bool            │  │
│  │                                           │  │
│  │  class PlaylistResponse(BaseModel):       │  │
│  │      tracks: List[PlaylistTrack]          │  │
│  │      bpm_progression: str                 │  │
│  │      energy_curve: str                    │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Data Flow Example

### Приклад 1: Complete Intent (Single Turn)

```
User: "Хочу темповий біг 30 хв"
                │
                v
    ┌───────────────────────┐
    │ ConversationManager   │
    │  state: NEW           │
    └───────────┬───────────┘
                v
    ┌───────────────────────┐
    │ PromptBuilder         │
    │  + workout_expert     │
    └───────────┬───────────┘
                v
    ┌───────────────────────┐
    │ OpenAI GPT-4          │
    │  Structured Output    │
    └───────────┬───────────┘
                v
    ┌───────────────────────────────┐
    │ WorkoutIntent                 │
    │  type: "tempo"                │
    │  duration: 30                 │
    │  bpm: 145-160                 │
    │  confidence: 0.95             │
    │  needs_clarification: False   │
    └───────────┬───────────────────┘
                v
    ┌───────────────────────┐
    │ ConversationManager   │
    │  state: READY         │
    └───────────┬───────────┘
                v
    ┌───────────────────────┐
    │ LLMService            │
    │  generate_playlist()  │
    └───────────┬───────────┘
                v
    ┌───────────────────────┐
    │ PromptBuilder         │
    │  + music_curator      │
    └───────────┬───────────┘
                v
    ┌───────────────────────┐
    │ OpenAI GPT-4          │
    │  Structured Output    │
    └───────────┬───────────┘
                v
    ┌───────────────────────────┐
    │ PlaylistResponse          │
    │  12 tracks, 31 min        │
    │  BPM: steady 145-160      │
    │  Energy curve: ━━━━━━━    │
    └───────────┬───────────────┘
                v
    ┌───────────────────────┐
    │ User: "Open Spotify"  │
    └───────────────────────┘
```

### Приклад 2: Needs Clarification (Multi-Turn)

```
Turn 1:
User: "хочу інтервали"
        │
        v
    WorkoutIntent:
      type: "intervals"
      duration: 40 (guessed)
      intervals: None ❌
      confidence: 0.6
      needs_clarification: True
      question: "Який інтервал роботи/відпочинку?"
        │
        v
AI: "Який інтервал роботи/відпочинку? (наприклад 5-2)"

Turn 2:
User: "5-2-5-2"
        │
        v
    WorkoutIntent:
      type: "intervals"
      duration: 40
      intervals: [work:5, rest:2] × 4
      confidence: 0.95
      needs_clarification: False ✓
        │
        v
    → Generate Playlist
        │
        v
AI: "✓ Плейлист готовий! 🎵"
```

## Component Responsibilities

### Agent 1: Prompt System Architect
```
workout_expert.py
├── Heart rate zones (1-5)
├── BPM mapping per zone
├── Workout types knowledge
├── Duration parsing
├── Intensity keywords
└── Response format specs

prompt_builder.py
├── Combine system prompts
├── Inject user context
├── Build conversation history
└── Dynamic prompt construction
```

### Agent 2: Structured Outputs
```
llm_responses.py
├── WorkoutIntent model
│   ├── Field validations
│   ├── BPM range checks
│   └── Interval requirements
├── PlaylistResponse model
│   ├── Track list structure
│   ├── BPM progression
│   └── Energy visualization
└── IntervalPhase model
    ├── Work/rest validation
    └── BPM for phase type
```

### Agent 3: Music Curator
```
music_curator.py
├── BPM Science
│   ├── Cadence sync
│   ├── Zone-specific BPM
│   └── Performance effects
├── Genre Selection
│   ├── High-energy genres
│   ├── Moderate workouts
│   └── Recovery music
├── Playlist Structure
│   ├── Warm-up phase
│   ├── Main workout
│   └── Cool-down phase
└── Energy Curves
    ├── Steady state
    ├── Building
    ├── Wave (intervals)
    └── Pyramid
```

### Agent 4: Conversation Flow
```
conversation_manager.py
├── State Machine
│   ├── NEW
│   ├── PARSING_INTENT
│   ├── NEEDS_CLARIFICATION
│   ├── READY_TO_GENERATE
│   └── COMPLETE
├── Context Management
│   ├── Message history
│   ├── Parsed intents
│   └── User preferences
├── Decision Making
│   ├── Is intent complete?
│   ├── Generate follow-up
│   └── When to create playlist
└── Database Persistence
    ├── Save conversations
    ├── Store messages
    └── Track analytics
```

## Technology Stack

```
┌─────────────────────────────────────┐
│          Technology Stack            │
├─────────────────────────────────────┤
│ Backend:   FastAPI + Python 3.11    │
│ LLM:       OpenAI GPT-4 Sonnet       │
│ Validation: Pydantic v2              │
│ Database:  Supabase PostgreSQL       │
│ State:     In-memory + DB            │
│ Testing:   Pytest + AsyncMock        │
└─────────────────────────────────────┘
```

## Metrics & Monitoring

```
┌────────────────────────────────────┐
│         Key Metrics                │
├────────────────────────────────────┤
│ Parse Accuracy:     >95%           │
│ Conversation Turns: <3 avg         │
│ Generation Time:    <8s            │
│ Playlist Quality:   >4.5/5         │
│ Track Skip Rate:    <20%           │
└────────────────────────────────────┘
```

---

**Архітектура готова до імплементації!** 🚀

Кожен агент додає свій шар експертизи:
1. Sport science knowledge
2. Type-safe responses
3. Music curation expertise
4. Intelligent conversations

Результат: Professional AI system для підбору музики 🎵
