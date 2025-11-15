# 📊 RunBeat - Детальний звіт по архітектурі проекту

**Дата:** 2025-11-15
**Версія:** 3.0
**Статус:** Production Ready
**Останнє оновлення:** 2025-11-15 (Перехід на розмовну AI-архітектуру)

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

- 🤖 **Розмовний AI-асистент** для покрокового створення тренувань.
- 🎵 Генерація плейлистів на основі параметрів тренування.
- 🏃 Підтримка різних типів тренувань (стабільна, інтервальна, фартлек).
- 📱 Адаптивний веб-інтерфейс з оптимізованою швидкістю завантаження.
- 🔗 Інтеграція з Spotify API.
- 💾 Збереження історії тренувань та плейлистів.

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
│  • React.lazy & Suspense для швидкого завантаження              │
│  • Адаптивні компоненти чату, історії та налаштувань              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ REST API (/api/v1/chat/message)
                             │
                             v
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              API Routes (/api/v1/chat)                   │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                          │
│                       v                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               SupervisorAgent (Оркестратор)              │   │
│  │  • Керує станом розмови для кожного користувача          │   │
│  │  • Делегує завдання спеціалізованим агентам              │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                          │
│         ┌─────────────┴─────────────┐                           │
│         │                           │                           │
│         v                           v                           │
│  ┌──────────────┐          ┌──────────────┐                    │
│  │ WorkoutBuilder │          │ WorkoutManager │                    │
│  │ Agent        │          │ Agent        │                    │
│  │              │          │              │                    │
│  │ • Веде діалог│          │ • Створює    │                    │
│  │ • Збирає     │          │   воркаут в БД│                   │
│  │   параметри  │          │              │                    │
│  └──────────────┘          └───────┬──────┘                    │
│                                    │                           │
│                                    v                           │
│                             ┌──────────────┐                   │
│                             │ MusicCurator │                   │
│                             │ Agent        │                   │
│                             │              │                   │
│                             │ • Генерує    │                   │
│                             │   плейлист   │                   │
│                             └──────────────┘                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                v            v            v
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   Supabase   │ │   OpenAI     │ │   Spotify    │
    │  PostgreSQL  │ │   GPT-4      │ │     API      │
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
│       ├── chat.py            # Новий, спрощений Chat endpoint
│       └── ...                # Інші роути (workouts, playlists)
├── services/
│   ├── spotify_service.py     # Spotify API client (рефакторений)
│   ├── spotify_modules/       # Модулі для spotify_service
│   ├── supabase_service.py    # Database client
│   ├── workout_builder.py     # WorkoutBuilder - LangChain AI-агент
│   └── ...                    # Інші сервіси
├── agents/                        # Multi-agent система
│   ├── __init__.py
│   ├── base.py                    # Base agent class
│   ├── supervisor.py              # SupervisorAgent (Оркестратор)
│   ├── manager.py                 # WorkoutManagerAgent (робота з БД)
│   ├── curator.py                 # MusicCuratorAgent (генерація плейлистів)
│   ├── tools/                     # Інструменти для агентів
│   │   ├── parser_tools.py        # rule_based_parse, validate_intent
│   │   └── workout_tools.py       # create_workout_from_params
│   └── prompts/                   # Промпти для агентів
│       └── conversation_prompts.py # CONVERSATION_AGENT_SYSTEM_PROMPT
├── schemas/
│   ├── chat.py                    # Chat request/response
│   ├── workout.py                 # Workout schemas
│   ├── playlist.py                # Playlist schemas
│   └── conversation.py            # Схеми для стану розмови
└── ...
```

---

## 🤖 Multi-Agent система (Нова архітектура)

Попередня система, що базувалася на парсингу одного повідомлення, була повністю замінена на проактивну розмовну модель, де AI-асистент веде користувача покроково.

### Архітектура агентів

```
┌─────────────────────────────────────────────────────────────────┐
│                        SupervisorAgent                           │
│                  (Керує станом та делегує)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ 1. User message
                             v
┌─────────────────────────────────────────────────────────────────┐
│                     WorkoutBuilder                                │
│        (LangChain AI-агент для збору параметрів воркаута)         │
│                                                                   │
│  • Використовує детальний промпт (CONVERSATION_AGENT_SYSTEM_PROMPT)│
│  • Tools: rule_based_parse, validate_intent, create_workout      │
│  • max_iterations=10, max_execution_time=30 секунд              │
│  • Fallback-логіка для iteration limits та коротких повідомлень │
│  • State: last_question = "none" -> "goal_clarification" ...      │
│                                                                   │
│  Коли всі параметри зібрані:                                     │
│  • last_question = "final_confirmation"                           │
│  • Запитує: "Створюємо воркаут?" з кнопками Да/Ні на frontend    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ 2. User confirms ("Так")
                             v
┌─────────────────────────────────────────────────────────────────┐
│                        SupervisorAgent                           │
│  • Отримує підтвердження ("Да"/"так"/"yes")                      │
│  • Якщо агент не створив воркаут (iteration limit),             │
│    створює його через fallback (create_workout_from_params)     │
│  • Очищує стан розмови після успішного створення                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ 3. (Після створення воркаута, опціонально)
                             v
┌─────────────────────────────────────────────────────────────────┐
│                      MusicCuratorAgent                           │
│                  (Генерує плейлист для воркаута)                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Потоки даних

### Потік 1: Створення воркаута через діалог (Новий потік)

```
┌─────────┐
│  User   │
│ "хочу   │
│ пробігти"│
└────┬────┘
     │ POST /chat/message
     v
┌─────────────────────────────────────────────────────────────┐
│  Backend: SupervisorAgent.handle_message()                   │
│  • Створює новий ConversationState для user_id               │
│  • Делегує до WorkoutBuilder (LangChain AI-агент)            │
└────┬─────────────────────────────────────────────────────────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  WorkoutBuilder.process_message()                             │
│  • Використовує LangChain AI-агент з промптом                  │
│  • Обробляє короткі повідомлення через fallback               │
│  • Генерує природну відповідь на основі промпту              │
└────┬─────────────────────────────────────────────────────────┘
     │
     │ Response: "Чудово! ... Оберіть тип тренування: ..."
     v
┌─────────────────────────────────────────────────────────────┐
│  Frontend: ChatPage                                          │
│  • Показує питання від AI                                    │
└────┬─────────────────────────────────────────────────────────┘
     │
┌─────────┐
│  User   │
│ "Стабільна"│
└────┬────┘
     │ POST /chat/message
     v
┌─────────────────────────────────────────────────────────────┐
│  Backend: SupervisorAgent -> WorkoutBuilder                   │
│  • AI-агент аналізує повідомлення через промпт                 │
│  • Використовує tools для витягнення параметрів                │
│  • Зберігає параметри в state.collected_parameters            │
│  • Генерує наступне питання на основі відсутньої інформації   │
└────┬─────────────────────────────────────────────────────────┘
     │
     │ Response: "Добре, зрозуміло. Яка буде тривалість ...?"
     v
... (діалог продовжується, доки всі параметри не зібрано) ...
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  WorkoutBuilder                                               │
│  • AI-агент визначає, що всі параметри зібрані                │
│  • Генерує: "Створюємо воркаут?"                              │
│  • Frontend показує кнопки Да/Ні                             │
└────┬─────────────────────────────────────────────────────────┘
     │
     │ Response: "Ми зібрали всю інформацію! ... Зберегти його?"
     v
┌─────────┐
│  User   │
│  "Так"  │
└────┬────┘
     │ POST /chat/message
     v
┌─────────────────────────────────────────────────────────────┐
│  SupervisorAgent                                             │
│  • Визнає підтвердження користувача ("Да"/"так")              │
│  • Якщо агент створив воркаут → очищає стан                   │
│  • Якщо агент не створив (iteration limit) →                  │
│    створює через create_workout_from_params fallback         │
│  • Очищує стан розмови після успішного створення             │
└────┬─────────────────────────────────────────────────────────┘
     │
     │ Response: "✅ Воркаут успішно створено!"
     v
┌─────────────────────────────────────────────────────────────┐
│  Frontend: ChatPage                                          │
│  • Показує повідомлення про успіх                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Висновки

### Поточна архітектура (Розмовний AI)

1. **✅ Розмовний підхід**: AI-асистент проактивно веде діалог, покроково збираючи параметри.
2. **✅ Чітка архітектура агентів**: Supervisor (оркестратор), Builder (діалог), Manager (БД), Curator (музика).
3. **✅ Модульність**: Кожен агент має чітку, єдину відповідальність.
4. **✅ Гнучкість**: Систему легко розширювати новими питаннями або логікою.
5. **✅ Покращений UX**: Взаємодія стала більш природною та інтуїтивною для користувача.

### Активні компоненти

✅ **SupervisorAgent** - Координує всіх агентів та керує станом розмови. Має fallback для створення воркаутів, якщо агент досягає iteration limit.
✅ **WorkoutBuilder** - LangChain AI-агент з детальними промптами для природної розмови з користувачем. Веде діалог для збору параметрів воркаута з fallback-логікою для обробки помилок.
✅ **WorkoutManagerAgent** - Створює та активує воркаути в базі даних.
✅ **MusicCuratorAgent** - Генерує плейлисти з інтеграцією Spotify.
✅ **ErrorLoggingService** - Зберігає помилки в базі даних.

### Майбутні покращення

🔮 **Додавання моніторингу та логування** (LangSmith integration)
🔮 **Кешування для оптимізації** (Redis для станів розмов)
🔮 **A/B тестування різних промптів/питань**
🔮 **Streaming responses** для кращого UX
🔮 **Agent memory persistence** для довготривалих розмов
🔮 **Error analytics dashboard** (візуалізація помилок)

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

### Error Logs API

```
POST   /api/v1/error-logs/
Request:
{
  "level": "ERROR",
  "message": "Failed to generate playlist",
  "error_type": "ValueError",
  "error_details": { ... },
  "stack_trace": "...",
  "user_id": "uuid" (optional),
  "request_path": "/api/v1/playlists/generate",
  "request_method": "POST",
  "request_body": { ... } (optional),
  "response_status": 500 (optional)
}

GET    /api/v1/error-logs/?level=ERROR&limit=100&offset=0
GET    /api/v1/error-logs/statistics?days=7
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
│ 1. WorkoutBuilder (основний AI-агент)                       │
│    • LangChain AI-агент з детальними промптами               │
│    • Веде природну розмову для збору параметрів             │
│    • Tools: rule_based_parse, validate_intent,              │
│             create_workout_from_params                      │
│    • max_iterations=10, max_execution_time=30 секунд       │
│    • Fallback-логіка для iteration limits                  │
│                                                               │
│ 2. SupervisorAgent (Оркестратор)                            │
│    • Керує станом розмови для кожного користувача           │
│    • Делегує завдання до WorkoutBuilder                     │
│    • Має fallback для створення воркаутів                   │
│    • Очищує стан після успішного створення                  │
│                                                               │
│ 3. MusicCuratorAgent                                        │
│    • Generates playlists                                    │
│    • Spotify integration                                    │
│    • Tools: search_spotify_tracks, get_recommendations,     │
│             calculate_bpm_progression                        │
│                                                               │
│ 4. WorkoutManagerAgent                                      │
│    • Creates & activates workouts                           │
│    • Database operations                                    │
│    • Tools: create_workout, activate_workout, get_active    │
└─────────────────────────────────────────────────────────────┘
```

### Потік обробки повідомлення (поточна архітектура)

```
User Message
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  POST /api/v1/chat/message                                  │
│  Request: { message: "...", user_id: "..." }                │
└────┬─────────────────────────────────────────────────────────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  SupervisorAgent.handle_message()                           │
│  • Отримує або створює ConversationState для user_id        │
│  • Делегує до WorkoutBuilder                                │
└────┬─────────────────────────────────────────────────────────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  WorkoutBuilder.process_message()                           │
│                                                               │
│  1. Валідація повідомлення:                                  │
│     • Короткі повідомлення (≤2 символи) → fallback         │
│                                                               │
│  2. Побудова контексту:                                      │
│     • Зібрані параметри з state.collected_parameters        │
│     • Відсутні параметри                                     │
│     • Історія розмови (останні 20 повідомлень)              │
│                                                               │
│  3. Виклик LangChain AI-агента:                              │
│     • Використовує CONVERSATION_AGENT_SYSTEM_PROMPT         │
│     • Tools: rule_based_parse, validate_intent,             │
│              create_workout_from_params                     │
│     • max_iterations=10, max_execution_time=30              │
│                                                               │
│  4. Обробка відповіді:                                       │
│     • Перевірка на iteration/time limit                     │
│     • Якщо досягнуто ліміт → fallback response              │
│     • Оновлення state.collected_parameters                  │
│     • Визначення state.last_question                        │
└────┬─────────────────────────────────────────────────────────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  SupervisorAgent (продовження)                              │
│  • Якщо user підтвердив ("Да"/"так") і last_question ==      │
│    "final_confirmation":                                     │
│    - Перевіряє, чи створив агент воркаут                    │
│    - Якщо ні → створює через fallback                       │
│  • Очищує стан після успішного створення                    │
└────┬─────────────────────────────────────────────────────────┘
     │
     v
┌─────────────────────────────────────────────────────────────┐
│  Response: "✅ Воркаут успішно створено! ..."                │
│  Frontend: Показує повідомлення та кнопки для плейлиста      │
└─────────────────────────────────────────────────────────────┘
```

---

**Дата створення:** 2025-11-15
**Останнє оновлення:** 2025-11-15
**Версія документа:** 3.1
**Статус:** Актуальний - Повна міграція на LangChain завершена ✅

### Останні зміни (v3.1)

✅ **Покращення розмовної AI-архітектури:**

- **WorkoutBuilder** тепер є повноцінним LangChain AI-агентом з детальними промптами для управління розмовою
- Вся логіка розмови закодована в промптах (`CONVERSATION_AGENT_SYSTEM_PROMPT`), що спрощує підтримку та налаштування
- Додана обробка підтвердження/відмови з кнопками Да/Ні на frontend
- Реалізована fallback-логіка для обробки iteration limits та коротких повідомлень
- SupervisorAgent має fallback для створення воркаутів, якщо агент досягає ліміту ітерацій
- Збільшені ліміти агента: `max_iterations=10`, `max_execution_time=30` секунд
- Покращена обробка помилок та повторних спроб через `OpenAIErrorHandler`

### Останні зміни (v3.0)

✅ **Перехід на розмовну AI-архітектуру:**

- Заміна парсингу одного повідомлення на проактивну розмовну модель, де AI-асистент веде користувача покроково
- Багаторазова взаємодія через природну розмову з покроковим збором параметрів
