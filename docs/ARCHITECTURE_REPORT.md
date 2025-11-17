# 📊 RunBeat - Детальний звіт по архітектурі проекту

**Дата:** Листопад 2025
**Версія:** 3.3
**Статус:** Production Ready
**Останнє оновлення:** Листопад 2025 (AI Learning & Personalization)

---

## 📋 Зміст

1. [Загальний огляд](#загальний-огляд)
2. [Архітектура системи](#архітектура-системи)
3. [Backend архітектура](#backend-архітектура)
4. [Frontend архітектура (Web)](#frontend-архітектура)
5. [Mobile App архітектура (Planned)](#mobile-app-архітектура-planned)
6. [База даних](#база-даних)
7. [Потоки даних](#потоки-даних)
8. [Multi-Agent система](#multi-agent-система)
9. [API Endpoints](#api-endpoints)
10. [Технологічний стек](#технологічний-стек)
11. [Deployment архітектура](#deployment-архітектура)

---

## 🎯 Загальний огляд

RunBeat - це AI-powered система для генерації персоналізованих плейлистів для бігу через природну розмову з користувачем.

### Основні можливості:

- 🤖 **Розмовний AI-асистент** для покрокового створення тренувань.
- 🧠 **AI Learning & Personalization** - система вчиться на розмовах користувача.
- 🎯 **Персоналізовані рекомендації** на основі історії користувача.
- 🎵 Генерація плейлистів на основі параметрів тренування.
- 🏃 Підтримка різних типів тренувань (стабільна, інтервальна, фартлек).
- 📱 Адаптивний веб-інтерфейс з оптимізованою швидкістю завантаження.
- 🔗 Інтеграція з Spotify API.
- 💾 Збереження історії тренувань та плейлистів.
- 📊 Analytics API для моніторингу та оптимізації розмов.

---

## 🏗️ Архітектура системи

### Високорівнева схема

```
┌─────────────────────────────────────────────────────────────────┐
│                         Користувач                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                v
┌───────────────────────────┐
│   Web App (React + Vite)  │
│  • Tailwind CSS           │
│  • React Router           │
│  • Lazy Loading           │
│  • Responsive Design      │
└────────────┬──────────────┘
             │
             │ REST API (/api/v1/*)
             │ HTTPS
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
│  │ • Fuzzy      │          │              │                    │
│  │   розпізнаван│          │              │                    │
│  │   ня жанрів  │          │              │                    │
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
│       ├── analytics.py       # Analytics API для conversation insights
│       └── ...                # Інші роути (workouts, playlists)
├── services/
│   ├── spotify_service.py     # Spotify API client (рефакторений)
│   ├── spotify_modules/       # Модулі для spotify_service
│   ├── supabase_service.py    # Database client
│   ├── workout_builder.py     # WorkoutBuilder - LangChain AI-агент
│   ├── conversation_service.py # ConversationService - збереження та аналіз розмов
│   └── ...                    # Інші сервіси
├── agents/                        # Multi-agent система
│   ├── __init__.py
│   ├── base.py                    # Base agent class
│   ├── supervisor.py              # SupervisorAgent (Оркестратор)
│   ├── manager.py                 # WorkoutManagerAgent (робота з БД)
│   ├── curator.py                 # MusicCuratorAgent (генерація плейлистів)
│   ├── tools/                     # Інструменти для агентів
│   │   ├── parser_tools.py        # rule_based_parse, validate_intent
│   │   └── workout_tools.py       # create_workout_from_params (tool)
│   │                              # _create_workout_from_params_internal (internal)
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
│  • AI сам витягує параметри через промпт (без tools для парсингу)│
│  • max_iterations=8, max_execution_time=25 секунд (оптимізовано)│
│  • Fuzzy matching для розпізнавання жанрів (electric→electronic) │
│  • Акумуляція жанрів замість заміни (rock + pop → [rock, pop])  │
│  • Персоналізація через user patterns з БД                       │
│  • Витягує з БД: улюблені жанри, типову тривалість, preferred type│
│  • Fallback-логіка для iteration limits та коротких повідомлень │
│  • Явні індикатори кроків у контексті (Step 1, 2, 3)            │
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
│    створює його через fallback                                  │
│    (_create_workout_from_params_internal)                       │
│  • Виправлено: тепер використовує внутрішню функцію, а не tool │
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

### 🧠 AI Learning & Personalization

```
┌─────────────────────────────────────────────────────────────────┐
│                   ConversationService                            │
│           (Збереження та аналіз розмов)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📝 save_conversation()                                          │
│     • Зберігає кожну розмову в БД після кожного повідомлення    │
│     • Таблиця: conversations (messages JSONB, workout_intent)   │
│     • State: active, completed, abandoned                       │
│                                                                   │
│  🔍 get_user_patterns()                                          │
│     • Аналізує останні 20 розмов користувача                    │
│     • Favorite genres (top 3)                                   │
│     • Typical duration (середнє)                                │
│     • Preferred workout type (найпопулярніший)                  │
│     • Common intensity (найчастіший)                            │
│                                                                   │
│  📊 get_conversation_insights()                                  │
│     • Аналізує всі розмови за N днів                            │
│     • Completion rate (% успішних)                              │
│     • Abandonment rate (% покинутих)                            │
│     • Most common genres                                        │
│     • Average messages per conversation                         │
│                                                                   │
│  🎯 Використання в AI:                                           │
│     WorkoutBuilder витягує patterns → додає в context →         │
│     AI бачить історію → дає кращі підказки!                     │
└─────────────────────────────────────────────────────────────────┘

Потік персоналізації:
┌──────────┐
│   User   │ "хочу пробіжку"
└────┬─────┘
     │
     v
┌─────────────────────────────────────┐
│ WorkoutBuilder.process_message()    │
│  ↓                                   │
│ conversation_service.get_user_patterns(user_id)
│  ↓                                   │
│ Витягує з БД:                        │
│  - favorite_genres: ["electronic", "rock"]
│  - typical_duration: 45 min         │
│  - preferred_type: "fartlek"        │
│  ↓                                   │
│ Додає в context:                    │
│ "USER PREFERENCES (from history):   │
│  - Favorite genres: electronic, rock"│
│  ↓                                   │
│ AI отримує context → генерує відповідь:
│ "Чудово! Може фартлек на 45 хв     │
│  під electronic?"                   │
└─────────────────────────────────────┘
     │
     v
  User отримує персоналізовану підказку! 🎯
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

✅ **SupervisorAgent** - Координує всіх агентів та керує станом розмови. Має fallback для створення воркаутів. Зберігає розмови в БД після кожного повідомлення.
✅ **WorkoutBuilder** - LangChain AI-агент з детальними промптами для природної розмови з користувачем. AI сам витягує параметри через промпт. Використовує user patterns для персоналізації.
✅ **ConversationService** - Зберігає розмови в БД, аналізує user patterns, надає insights для оптимізації.
✅ **WorkoutManagerAgent** - Створює та активує воркаути в базі даних.
✅ **MusicCuratorAgent** - Генерує плейлисти з інтеграцією Spotify.
✅ **ErrorLoggingService** - Зберігає помилки в базі даних.
✅ **Analytics API** - Endpoints для моніторингу conversation insights та user patterns.

### Виправлені проблеми (v3.2)

🐛 **Критичні помилки**:

- ❌ `BaseTool.__call__() got an unexpected keyword argument 'user_id'` → ✅ Виправлено через внутрішню функцію
- ❌ Агент зациклювався на одному питанні → ✅ Виправлено через акумуляцію параметрів
- ❌ Жанри не розпізнавалися ("electric" не працював) → ✅ Додано fuzzy matching
- ❌ Агент досягав iteration limit (10 ітерацій) → ✅ Оптимізовано до 5 ітерацій з кращим fallback

### Реалізовано (v3.3) ✅

✅ **AI Learning & Personalization** - AI вчиться на розмовах користувача
✅ **User Patterns Analysis** - аналіз улюблених жанрів, тривалості, типу
✅ **Conversation Storage** - збереження всіх розмов в БД
✅ **Analytics API** - insights для оптимізації промптів
✅ **Персоналізовані підказки** - AI бачить історію користувача

### Майбутні покращення

🔮 **LangSmith integration** - детальний моніторинг AI агентів
🔮 **Redis для кешування** - швидший доступ до user patterns
🔮 **A/B тестування різних промптів/питань**
🔮 **Streaming responses** для кращого UX
🔮 **Автоматична оптимізація промптів** на основі analytics
🔮 **Error analytics dashboard** (візуалізація помилок)

---

---

## 🔧 Технічні деталі виправлень (v3.2)

### Виправлення помилки з викликом tool

**Проблема**: SupervisorAgent намагався викликати LangChain `@tool` як звичайну функцію, що викликало помилку:

```
BaseTool.__call__() got an unexpected keyword argument 'user_id'
```

**Рішення**:

```python
# workout_tools.py

# Створено внутрішню функцію (не tool)
def _create_workout_from_params_internal(
    user_id: str,
    workout_type: str,
    duration_minutes: int,
    intensity: str,
    genres: Optional[str] = None,
    prompt: Optional[str] = None,
) -> str:
    # ... реалізація створення воркаута ...
    pass

# Tool тепер викликає внутрішню функцію
@tool
def create_workout_from_params(...) -> str:
    return _create_workout_from_params_internal(...)

# supervisor.py
from app.agents.tools.workout_tools import _create_workout_from_params_internal

# Тепер можна викликати напряму
result = _create_workout_from_params_internal(
    user_id=user_id,
    workout_type=workout_type,
    ...
)
```

### Fuzzy matching для жанрів

**Проблема**: Користувач писав "electric", але система не розпізнавала це як "electronic".

**Рішення**:

```python
# workout_builder.py
genre_mapping = {
    "electronic": ["electronic", "electric", "electro", "електро", "електронн"],
    "rock": ["rock", "рок"],
    "pop": ["pop", "поп"],
    # ... 20+ жанрів з варіаціями
}

found_genres = []
for genre, variations in genre_mapping.items():
    if any(var in message_lower for var in variations):
        found_genres.append(genre)
```

### Акумуляція жанрів

**Проблема**: При введенні "electric", потім "rock", зберігався лише "rock".

**Рішення**:

```python
# workout_builder.py
if "genres" in parsed_params:
    existing_genres = collected.get("genres", [])
    new_genres = parsed_params["genres"]
    if isinstance(existing_genres, list):
        # Злиття без дублікатів
        all_genres = list(set(existing_genres + new_genres))
        parsed_params["genres"] = all_genres
```

### Оптимізація лімітів

**Було**:

```python
max_iterations=10
max_execution_time=30  # секунд
```

**Стало (v3.2)**:

```python
max_iterations=5  # Достатньо для більшості випадків
max_execution_time=15  # Швидший відгук
```

**Оновлено (v3.3)**:

```python
max_iterations=8  # Збільшено для повної обробки контексту
max_execution_time=25  # Достатньо для витягування параметрів
```

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

## 🎨 Frontend архітектура

### Технологічний стек

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: Zustand (authStore)
- **Routing**: React Router v6
- **HTTP Client**: Axios (api service)

### Структура проекту

```
apps/web/
├── src/
│   ├── App.tsx                 # Main app component with routing
│   ├── main.tsx                # Entry point
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── InputBar.tsx              # Message input component
│   │   │   ├── MessageBubble.tsx         # Chat message bubble
│   │   │   ├── PlaylistHistorySidebar.tsx # Workout & playlist history
│   │   │   ├── SettingsSidebar.tsx       # Workout settings panel
│   │   │   └── TypingIndicator.tsx       # Loading indicator
│   │   ├── Player/
│   │   │   └── TrackCard.tsx             # Track display card
│   │   ├── Shared/
│   │   │   ├── Button.tsx
│   │   │   ├── ErrorDisplay.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   └── SpotifyConnectBanner.tsx
│   │   └── ProtectedRoute.tsx            # Auth guard component
│   ├── pages/
│   │   ├── ChatPage.tsx                  # Main chat interface
│   │   ├── HistoryPage.tsx               # Workout history
│   │   ├── PlayerPage.tsx                # Music player
│   │   ├── LoginPage.tsx                 # Spotify login
│   │   └── AuthCallbackPage.tsx          # OAuth callback handler
│   ├── hooks/
│   │   ├── useAuth.ts                    # Authentication hook
│   │   ├── useChat.ts                    # Chat logic hook
│   │   ├── usePlaylist.ts                # Playlist operations
│   │   ├── usePlaylistHistory.ts         # Playlist history
│   │   └── useWorkoutHistory.ts          # Workout history
│   ├── services/
│   │   ├── api.ts                        # API client (Axios)
│   │   ├── errorLogger.ts                # Error logging to backend
│   │   └── supabase.ts                   # Supabase client
│   ├── stores/
│   │   └── authStore.ts                  # Zustand auth state
│   └── types/
│       ├── index.ts                      # Shared types
│       └── settings.ts                   # Workout settings types
└── ...
```

### Component Hierarchy

```
App (React Router)
├── Routes
│   ├── / (ChatPage) [Protected]
│   │   ├── PlaylistHistorySidebar
│   │   │   ├── Workout history list
│   │   │   └── Playlist history list
│   │   │
│   │   ├── Chat Area
│   │   │   ├── MessageBubble (×N)        # User + Assistant messages
│   │   │   ├── TypingIndicator           # Loading state
│   │   │   └── ErrorDisplay              # Error messages
│   │   │
│   │   ├── InputBar                      # Message input + Send button
│   │   │
│   │   └── SettingsSidebar
│   │       ├── WorkoutTypeSelector       # steady/intervals/fartlek
│   │       ├── DurationSlider            # Duration control
│   │       ├── IntensitySelector         # low/moderate/high
│   │       ├── GenreSelector             # Music genres
│   │       └── PromptInput               # Additional prompt
│   │
│   ├── /login (LoginPage)                # Spotify authentication
│   ├── /auth/callback (AuthCallbackPage) # OAuth callback
│   ├── /history (HistoryPage) [Protected]
│   │   └── Workout & Playlist lists
│   │
│   └── /player/:playlistId? (PlayerPage) [Protected]
│       ├── TrackCard (×N)                # Track list
│       └── Player controls
│
└── Components used across pages:
    ├── ProtectedRoute               # Auth guard wrapper
    ├── LoadingSpinner               # Loading state
    ├── ErrorDisplay                 # Error messages
    ├── SpotifyConnectBanner         # Spotify connection prompt
    └── Button                       # Reusable button component
```

### Key Features

- **Lazy Loading**: Pages загружаються за допомогою React.lazy для швидшого початкового завантаження
- **Protected Routes**: ProtectedRoute перевіряє автентифікацію та підключення Spotify
- **Responsive Design**: Адаптивний UI для mobile та desktop (sidebars collapse на mobile)
- **Real-time Chat**: Conversational interface для створення workouts
- **Error Handling**: Централізований error logging до backend API
- **Spotify Integration**: OAuth authentication та playlist generation

---

## 📱 Mobile App архітектура (Planned)

> **Статус:** 📋 Заплановано (не реалізовано)

Mobile додаток для RunBeat запланований для майбутньої розробки. Web додаток вже має адаптивний дизайн і працює на мобільних пристроях через браузер.

### Плановий Mobile технологічний стек

- **Framework**: React Native 0.73+
- **Platform**: Expo ~50.0+
- **Language**: TypeScript
- **State Management**: Zustand (спільний з web)
- **Navigation**: React Navigation v6 (Stack + Bottom Tabs)
- **HTTP Client**: Axios
- **Backend**: Supabase client

### Планові можливості

- 📋 **Cross-platform**: iOS, Android через Expo
- 📋 **Native Navigation**: React Navigation для smooth transitions
- 📋 **Spotify Integration**: Native SDK для програвання
- 📋 **Offline Support**: Можливість роботи офлайн
- 📋 **Push Notifications**: Сповіщення про нові плейлисти
- 📋 **Shared Codebase**: Спільна логіка з web app (hooks, types, services)

### Поточна альтернатива

Web додаток повністю адаптивний і працює на мобільних пристроях:

- ✅ Responsive design з Tailwind CSS
- ✅ Mobile-оптимізовані sidebar та навігація
- ✅ Touch-friendly інтерфейс
- ✅ PWA support (може бути додано)

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

### Analytics API (NEW! 🎯)

```
GET    /api/v1/analytics/conversation-insights?days=30
Response:
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

GET    /api/v1/analytics/user-patterns/{user_id}
Response:
{
  "success": true,
  "user_id": "uuid",
  "patterns": {
    "has_history": true,
    "total_conversations": 25,
    "favorite_genres": ["electronic", "rock", "pop"],
    "typical_duration": 45,
    "preferred_type": "fartlek",
    "common_intensity": "moderate"
  }
}

GET    /api/v1/analytics/recommendations?days=30
Response:
{
  "success": true,
  "insights": { ... },
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
│    • AI САМ витягує параметри через промпт (без tools!)     │
│    • Tools: тільки create_workout_from_params               │
│    • max_iterations=8, max_execution_time=25 секунд        │
│      (збільшено для повної обробки контексту)               │
│    • Fuzzy matching жанрів в промпті: 20+ жанрів + варіації │
│    • Акумуляція жанрів при збиранні параметрів              │
│    • 🧠 Персоналізація через user patterns з БД             │
│    • Витягує з БД: favorite genres, typical duration, etc.  │
│    • Fallback-логіка для iteration limits                  │
│    • Явні індикатори кроків (Step 1, 2, 3) у контексті     │
│                                                               │
│ 2. SupervisorAgent (Оркестратор)                            │
│    • Керує станом розмови для кожного користувача           │
│    • Делегує завдання до WorkoutBuilder                     │
│    • Має fallback для створення воркаутів через             │
│      _create_workout_from_params_internal() (внутрішня)    │
│    • Виправлено критичну помилку з викликом tools           │
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
│                                                               │
│ 5. ConversationService (NEW! 🧠)                            │
│    • Зберігає розмови в БД (conversations table)            │
│    • Аналізує user patterns (genres, duration, type)        │
│    • Надає insights для оптимізації (completion rate, etc.) │
│    • Інтегрований з WorkoutBuilder для персоналізації       │
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
│     • 🧠 User patterns з БД (витягує ConversationService):  │
│       - favorite_genres, typical_duration, preferred_type   │
│     • AI бачить preferences → дає кращі підказки!           │
│                                                               │
│  3. Виклик LangChain AI-агента:                              │
│     • Використовує CONVERSATION_AGENT_SYSTEM_PROMPT         │
│     • AI САМ витягує параметри через промпт                 │
│     • Tools: тільки create_workout_from_params              │
│     • max_iterations=8, max_execution_time=25               │
│       (оптимізовано для повної обробки контексту)           │
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
│  • 💾 Зберігає розмову в БД:                                │
│    conversation_service.save_conversation(user_id, state)   │
│    (таблиця conversations: messages, workout_intent)        │
│  • Якщо user підтвердив ("Да"/"так") і last_question ==      │
│    "final_confirmation":                                     │
│    - Перевіряє, чи створив агент воркаут                    │
│    - Якщо ні → створює через fallback                       │
│      (_create_workout_from_params_internal)                 │
│  • Виправлено: використовує внутрішню функцію, а не tool    │
│  • ✅ Позначає розмову як completed в БД                     │
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

**Дата створення:** 2024-11-15
**Останнє оновлення:** 2025-11-17
**Версія документа:** 3.3
**Статус:** Актуальний - AI Learning & Personalization ✅

### Останні зміни (v3.3) - 2024-11-15

🔧 **Виправлення розуміння контексту розмови:**

- **Збільшено ліміти для повної обробки**:

  - `max_iterations`: 5 → 8 (достатньо для витягування параметрів з контексту)
  - `max_execution_time`: 15 → 25 секунд (агент встигає обробити історію)

- **Покращено fallback-логіку**:

  - Fallback тепер **витягує параметри** з поточного повідомлення
  - Fallback **аналізує історію розмови** (останні 3 повідомлення)
  - Fallback **оновлює collected_parameters** перед генерацією відповіді
  - Агент більше НЕ втрачає контекст при досягненні iteration limit

- **Оновлено інструкції в промпті**:

  - Видалено посилання на неіснуючий `rule_based_parse` tool
  - Додано явні інструкції для витягування параметрів
  - Додано нагадування перевіряти chat_history
  - Підкреслено важливість SHORT відповідей (1-2 речення)

- **Покращено context builder**:
  - Чіткіші інструкції "ANALYZE the user message"
  - Явне нагадування "Look at chat_history"
  - Instruction to UPDATE (не overwrite) параметри

🧠 **AI Learning & Personalization System:**

- **ConversationService** - новий сервіс для збереження та аналізу розмов:

  - `save_conversation()` - зберігає кожну розмову в БД після кожного повідомлення
  - `get_user_patterns()` - аналізує останні 20 розмов користувача та визначає:
    - Улюблені музичні жанри (top 3)
    - Типову тривалість тренувань (середнє значення)
    - Preferred workout type (найпопулярніший тип)
    - Common intensity (найчастіша інтенсивність)
  - `get_conversation_insights()` - аналізує всі розмови за N днів для оптимізації:
    - Completion rate (% успішних розмов)
    - Abandonment rate (% покинутих розмов)
    - Most common genres (найпопулярніші жанри)
    - Average messages per conversation
  - `mark_conversation_completed()` - позначає розмову як завершену після створення воркаута

- **Analytics API** - три нових endpoints для моніторингу:

  - `GET /api/v1/analytics/conversation-insights?days=30` - insights для оптимізації
  - `GET /api/v1/analytics/user-patterns/{user_id}` - персоналізовані patterns користувача
  - `GET /api/v1/analytics/recommendations?days=30` - рекомендації для покращення промптів

- **Персоналізація AI-агента**:

  - WorkoutBuilder тепер витягує user patterns з БД перед кожною розмовою
  - Додає patterns у context промпту: "USER PREFERENCES (from history): ..."
  - AI бачить історію користувача та дає кращі, персоналізовані підказки
  - Приклад: якщо користувач зазвичай обирає фартлек 45 хв під electronic, AI запропонує це

- **Інтеграція з SupervisorAgent**:

  - Автоматичне збереження розмови після кожного повідомлення
  - Позначення розмови як "completed" після успішного створення воркаута
  - Історія зберігається в таблиці `conversations` (messages JSONB, workout_intent JSONB)

- **Періодичний аналіз для оптимізації**:
  - Адміністратори можуть переглядати insights через Analytics API
  - Рекомендації для покращення conversation flow
  - Виявлення проблемних місць (низький completion rate, високий abandonment rate)

### Останні зміни (v3.2) - 2024-11-15

🔧 **Виправлення критичних помилок AI-агента:**

- **Виправлено критичну помилку**: `BaseTool.__call__() got an unexpected keyword argument 'user_id'`

  - Створено внутрішню функцію `_create_workout_from_params_internal()` для використання supervisor
  - Tool `create_workout_from_params` тепер викликає цю внутрішню функцію
  - SupervisorAgent використовує внутрішню функцію для fallback створення воркаутів

- **Покращено розпізнавання жанрів**:

  - Додано fuzzy matching для жанрів: "electric" → "electronic", "electro" → "electronic"
  - Підтримка 20+ жанрів з різними варіаціями написання (українською та англійською)
  - Приклади: rock/рок, pop/поп, electronic/electric/електронн, classical/класик

- **Виправлено зациклення розмови**:

  - Жанри тепер акумулюються замість заміни: "rock" + "pop" → ["rock", "pop"]
  - Покращено логіку fallback для відстеження стану розмови

- **Оптимізовано продуктивність**:

  - Зменшено `max_iterations` з 10 до 5 для швидшого відгуку
  - Зменшено `max_execution_time` з 30 до 15 секунд
  - Покращено fallback логіку для обробки iteration limits

- **Покращено контекст для агента**:
  - Додано явні індикатори кроків: "Step 1: Get duration and intensity", "Step 2: Get music genres", "Step 3: Confirm and create workout"
  - Детальніші інструкції в контексті для запобігання повторенню питань
  - Чіткий user_id у контексті для правильного виклику tools

### Останні зміни (v3.1)

✅ **Покращення розмовної AI-архітектури:**

- **WorkoutBuilder** тепер є повноцінним LangChain AI-агентом з детальними промптами для управління розмовою
- Вся логіка розмови закодована в промптах (`CONVERSATION_AGENT_SYSTEM_PROMPT`), що спрощує підтримку та налаштування
- Додана обробка підтвердження/відмови з кнопками Да/Ні на frontend
- Реалізована fallback-логіка для обробки iteration limits та коротких повідомлень
- SupervisorAgent має fallback для створення воркаутів, якщо агент досягає ліміту ітерацій
- Покращена обробка помилок та повторних спроб через `OpenAIErrorHandler`

### Останні зміни (v3.0)

✅ **Перехід на розмовну AI-архітектуру:**

- Заміна парсингу одного повідомлення на проактивну розмовну модель, де AI-асистент веде користувача покроково
- Багаторазова взаємодія через природну розмову з покроковим збором параметрів
