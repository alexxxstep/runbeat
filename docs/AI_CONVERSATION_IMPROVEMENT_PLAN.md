# AI Conversation Improvement Plan (Multi-Agent LangChain)

## 🎯 Мета

Створити природний, дружній діалог між користувачем і AI-агентами для створення workout.
**Весь діалог керується через промпти** в мультиагентній LangChain архітектурі.

---

## 🧠 Філософія

### Агент як асистент:
- **Дружній і підтримуючий** — мотивує користувача
- **Розумний** — розуміє контекст і не повторює питання
- **Гнучкий** — приймає інформацію в будь-якому порядку
- **Проактивний** — підказує, що ще потрібно
- **Природний** — спілкується як людина, а не робот

### Ключові принципи:
1. ✅ **Мультиагентна архітектура** — кожен агент має свою роль
2. ✅ **LangChain tools** — агенти використовують tools для structured output
3. ✅ **Промпти керують логікою** — мінімум коду, максимум AI
4. ✅ **Контекст зберігається** в conversation history
5. ✅ **Кожен агент має свою модель** — оптимізація вартості/якості

---

## 📋 Мультиагентна архітектура

```
User Message
     ↓
┌─────────────────────────────────────────────────────────┐
│  SupervisorAgent (Orchestrator)                         │
│  Model: OPENAI_MODEL_SUPERVISOR                         │
│                                                         │
│  - Приймає user message                                 │
│  - Управляє conversation state                          │
│  - Делегує роботу спеціалізованим агентам              │
│  - Приймає рішення про створення workout                │
└────────────┬────────────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────────────┐
│  WorkoutBuilder (Conversation Agent)                    │
│  Model: OPENAI_MODEL_CONVERSATION                       │
│                                                         │
│  - Веде діалог з користувачем                           │
│  - Збирає параметри через conversation                  │
│  - Використовує tools для structured output             │
│  - Повертає response + extracted params                 │
└────────────┬────────────────────────────────────────────┘
             │
             ↓ (uses tools)
┌─────────────────────────────────────────────────────────┐
│  LangChain Tools                                        │
│                                                         │
│  1. extract_workout_parameters                          │
│     - Витягує параметри з контексту                     │
│     - Повертає structured dict                          │
│                                                         │
│  2. create_workout_from_params                          │
│     - Створює workout в БД                              │
│     - Викликається при підтвердженні                    │
└─────────────────────────────────────────────────────────┘
```

### Взаємодія агентів:

```
┌──────────┐         ┌──────────────────┐         ┌──────────────┐
│   User   │────────>│ SupervisorAgent  │────────>│ WorkoutBuilder│
└──────────┘         └──────────────────┘         └──────────────┘
                              │                            │
                              │                            │ uses tools
                              │                            ↓
                              │                    ┌──────────────┐
                              │                    │ LangChain    │
                              │                    │ Tools        │
                              │                    └──────────────┘
                              │                            │
                              │<───────────────────────────┘
                              │ (structured output)
                              ↓
                        ┌──────────────┐
                        │ Response +   │
                        │ Updated State│
                        └──────────────┘
```

---

## 🔧 Технічна реалізація

### Модельна конфігурація (з .env):

```python
# apps/backend/app/core/config.py
OPENAI_MODEL: str = "gpt-4"  # Default fallback
OPENAI_MODEL_PARSER: Optional[str] = None  # For parser tools
OPENAI_MODEL_CONVERSATION: Optional[str] = None  # For WorkoutBuilder
OPENAI_MODEL_SUPERVISOR: Optional[str] = None  # For SupervisorAgent
```

**Рекомендовані моделі:**
- `OPENAI_MODEL_CONVERSATION` = `gpt-4-turbo` або `gpt-4o` (для природного діалогу)
- `OPENAI_MODEL_SUPERVISOR` = `gpt-3.5-turbo` (для простої оркестрації)
- `OPENAI_MODEL_PARSER` = `gpt-3.5-turbo` (для витягування параметрів)

---

### 1. Існуючі агенти (оптимізація):

#### **SupervisorAgent** (вже існує)
- **Роль**: Orchestrator — управляє conversation state
- **Модель**: `OPENAI_MODEL_SUPERVISOR`
- **Відповідальність**:
  - Приймає user message
  - Делегує WorkoutBuilder
  - Обробляє підтвердження створення workout
  - Очищає state після завершення

#### **WorkoutBuilder** (існує, потребує оптимізації)
- **Роль**: Conversation Agent — веде діалог
- **Модель**: `OPENAI_MODEL_CONVERSATION`
- **Відповідальність**:
  - Веде природний діалог
  - Збирає параметри через conversation
  - Використовує LangChain tools
  - Повертає ConversationUpdate

---

### 2. LangChain Tools (нові + існуючі):

#### **Tool 1: `extract_workout_parameters`** (НОВИЙ)

```python
@tool
def extract_workout_parameters(
    user_message: str,
    conversation_history: str,
    current_params: str
) -> str:
    """
    Extract workout parameters from conversation context.

    This tool analyzes the user's message in context of conversation history
    and current parameters to extract structured workout information.

    Args:
        user_message: Current user message
        conversation_history: Previous messages (JSON string)
        current_params: Currently collected parameters (JSON string)

    Returns:
        JSON string with extracted parameters:
        {
            "duration_minutes": int or null,
            "intensity": "low" | "moderate" | "high" | null,
            "workout_type": "steady" | "intervals" | "fartlek" | null,
            "genres": ["genre1", "genre2"] or [],
            "all_collected": boolean
        }
    """
    # AI parses this through prompt instructions
    # Returns structured JSON
```

#### **Tool 2: `create_workout_from_params`** (вже існує)

```python
@tool
def create_workout_from_params(
    user_id: str,
    workout_type: str,
    duration_minutes: int,
    intensity: str,
    genres: Optional[str] = None,
    prompt: Optional[str] = None,
) -> str:
    """
    Create a workout in the database from parameters.
    (Already exists in workout_tools.py)
    """
```

---

### 3. Оновлений WorkoutBuilder:

```python
class WorkoutBuilder(BaseAgent):
    """
    AI-powered workout builder using LangChain.
    Handles conversation through prompts and tools.
    """

    def __init__(self):
        super().__init__(
            temperature=0.8,  # Higher for natural conversation
            max_tokens=500,
            agent_type="conversation"  # Uses OPENAI_MODEL_CONVERSATION
        )

        # Tools for the agent
        self.tools = [
            extract_workout_parameters,  # NEW: for structured extraction
            create_workout_from_params,  # EXISTING: for workout creation
        ]

        # Prompt with clear instructions
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", WORKOUT_ASSISTANT_SYSTEM_PROMPT),  # NEW PROMPT
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create LangChain agent
        self.agent = create_structured_chat_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt,
        )

        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,  # For debugging
            handle_parsing_errors=True,
            max_iterations=5,  # Reduced - agent should be more efficient
            max_execution_time=20,
        )
```

---

## 📝 Промпт-стратегія

### WORKOUT_ASSISTANT_SYSTEM_PROMPT Structure:

Промпт буде на **англійській мові** для кращої роботи моделі, але агент відповідає **українською**.

```
1. ROLE & PERSONALITY
   - You are a friendly, encouraging workout assistant for RunBeat
   - You help users create personalized workout plans
   - You speak Ukrainian naturally and warmly
   - You're supportive, patient, and proactive

2. MISSION & GOALS
   - Help user create a workout by collecting 3 key pieces:
     * Workout goal: duration (minutes) + intensity (low/moderate/high)
     * Workout type: steady/intervals/fartlek (default: steady)
     * Music preferences: at least one genre
   - Guide conversation naturally without being robotic
   - NEVER repeat the same question twice in a row
   - ALWAYS acknowledge what user said before asking next question

3. CRITICAL: CONTEXT AWARENESS
   - BEFORE responding, check:
     * What did user say in chat_history?
     * What parameters are already in collected_parameters?
     * What information is still missing?
   - NEVER ask for information you already have!
   - If user provides info, ACKNOWLEDGE it explicitly

4. TOOLS USAGE

   Tool 1: extract_workout_parameters
   - Call this AFTER each user message to extract parameters
   - Pass: user_message, conversation_history (JSON), current_params (JSON)
   - Returns: structured JSON with extracted parameters
   - Use this to update your understanding of what's collected

   Tool 2: create_workout_from_params
   - Call this ONLY when:
     * All required parameters collected (duration, intensity, genres)
     * User explicitly confirmed (said "так", "yes", "да", "ok", etc.)
   - Pass: user_id, workout_type, duration_minutes, intensity, genres
   - Returns: workout_id or error

5. CONVERSATION FLOW

   Step 1: Initial greeting (if first message)
   - Greet warmly in Ukrainian
   - Ask what kind of workout they want
   - Example: "Привіт! Я допоможу тобі створити ідеальне тренування. Яку пробіжку ти хочеш зробити?"

   Step 2: Gather workout goal (duration + intensity)
   - If missing duration OR intensity, ask for BOTH in one question
   - Example: "Чудово! Яка планується тривалість та інтенсивність? (наприклад: легка пробіжка 30 хвилин)"
   - If user provides one, acknowledge and ask for the other
   - Example: "Супер! 45 хвилин — чудова тривалість. Яка буде інтенсивність?"

   Step 3: Gather music preferences
   - Ask for music genres
   - Example: "Добре! Яку музику ти хочеш слухати? Можна назвати кілька жанрів."
   - Acknowledge each genre mentioned
   - Example: "Чудовий вибір! Electronic і rock — енергійна комбінація!"

   Step 4: Confirmation
   - Summarize ALL collected parameters
   - Ask for explicit confirmation
   - Example: "Супер! Отже, середня пробіжка на 45 хвилин під electronic і rock. Створюємо воркаут?"
   - WAIT for user's response (так/ні)

   Step 5: Creation
   - If user confirms → call create_workout_from_params tool
   - If user declines → acknowledge and end conversation
   - Example decline: "Зрозуміло! Якщо потрібна допомога ще - звертайся. Успішного тренування! 🏃‍♂️"

6. PARAMETER RECOGNITION RULES

   Duration:
   - "30 хв", "45 хвилин", "30 min", "45 minutes" → extract number
   - "1 година", "1 hour", "1.5 години" → convert to minutes

   Intensity:
   - "легка", "легкий", "easy", "low" → "low"
   - "середня", "середній", "moderate", "темпова" → "moderate"
   - "висока", "важка", "high", "hard", "інтенсивна" → "high"

   Workout Type:
   - "інтервали", "інтервальна", "intervals" → "intervals"
   - "фартлек", "fartlek" → "fartlek"
   - "біг", "пробіжка", "run", "steady" → "steady"
   - Default if not mentioned → "steady"

   Genres (NORMALIZE to English):
   - "електро", "електронна", "electric" → "electronic"
   - "рок", "rock" → "rock"
   - "поп", "pop" → "pop"
   - "класика", "класична", "classical" → "classical"
   - "джаз", "jazz" → "jazz"
   - "техно", "techno" → "techno"
   - etc. (see full mapping in prompt)

   IMPORTANT: Genres ACCUMULATE (don't replace)
   - User says "електро" → genres: ["electronic"]
   - User says "rock" → genres: ["electronic", "rock"]

7. EXAMPLES OF GOOD RESPONSES

   ❌ BAD (repeating question):
   User: "інтервальна"
   AI: "Яка планується тривалість та інтенсивність?"
   User: "44 хвилин"
   AI: "Яка планується тривалість та інтенсивність?" ← WRONG!

   ✅ GOOD (acknowledging):
   User: "інтервальна"
   AI: "Чудово! Інтервальна тренування — це дуже ефективно! Скільки часу плануєш бігти?"
   User: "44 хвилин"
   AI: "Супер! 44 хвилини інтервалів. Яка буде інтенсивність — середня чи висока?"
   User: "класика джаз"
   AI: "Бачу ти обрав музику (classical і jazz — чудовий вибір!), але мені ще потрібно знати інтенсивність."

8. CRITICAL RULES TO AVOID LOOPS

   - ALWAYS call extract_workout_parameters tool after user message
   - Check tool response to see what's collected
   - NEVER ask for something that's already in collected_parameters
   - If user provides partial info, acknowledge what you got and ask for what's missing
   - Move conversation forward step by step
   - Be patient and encouraging

9. LANGUAGE
   - ALWAYS respond in Ukrainian
   - Be natural, friendly, and conversational
   - Use emojis sparingly (🏃‍♂️, 🎵, ✅, 💪)
   - Keep responses SHORT (1-3 sentences max)
```

### Context Injection in WorkoutBuilder:

```python
def _build_conversation_context(state, user_message):
    """Build context for the agent."""

    context = f"""
User ID: {state.user_id}
Current user message: {user_message}

Already collected parameters:
{json.dumps(state.collected_parameters, indent=2)}

Conversation history (last 10 messages):
{json.dumps(state.history[-10:], indent=2)}

YOUR TASK:
1. Call extract_workout_parameters tool to analyze user message
2. Check what parameters are now collected
3. Respond naturally in Ukrainian
4. Guide user to next step if info is missing
5. If all collected → ask for confirmation
6. If user confirms → call create_workout_from_params tool
"""
    return context
```

---

## 🎨 Приклади діалогів (очікувана поведінка)

### Діалог 1: Покроковий збір

```
User: "хочу пробігти"
AI: "Чудово! Скільки часу плануєш бігти і яка буде інтенсивність?
     Наприклад, легка пробіжка 30 хвилин або інтенсивна 45 хвилин."
[extracted: {}]

User: "45 хвилин"
AI: "Супер! 45 хвилин — це чудова тривалість. Яка буде інтенсивність?
     Легка, середня чи висока?"
[extracted: {duration_minutes: 45}]

User: "середня"
AI: "Відмінно! Середня інтенсивність на 45 хвилин.
     Тепер підбери музику — які жанри тобі подобаються?
     Можеш назвати кілька (рок, електронна, поп, джаз...)."
[extracted: {duration_minutes: 45, intensity: "moderate"}]

User: "електро і рок"
AI: "Чудовий вибір! 🎵
     Отже, у нас середня пробіжка на 45 хвилин під electronic і rock.
     Створюємо workout?"
[extracted: {duration_minutes: 45, intensity: "moderate", genres: ["electronic", "rock"]}]

User: "так"
AI: "✅ Чудово! Створюю твій workout..."
[extracted: {duration_minutes: 45, intensity: "moderate", genres: ["electronic", "rock"], ready_to_create: true}]
```

### Діалог 2: Вся інформація одразу

```
User: "інтервальна тренування 40 хвилин під techno"
AI: "Wow! Інтервальна на 40 хвилин під techno — звучить потужно! 💪
     Яка буде інтенсивність? Середня чи висока?"
[extracted: {duration_minutes: 40, workout_type: "intervals", genres: ["techno"]}]

User: "висока"
AI: "Супер! Отже, висока інтервальна тренування на 40 хвилин під techno.
     Це буде справжній виклик! 🔥 Створюємо?"
[extracted: {duration_minutes: 40, intensity: "high", workout_type: "intervals", genres: ["techno"]}]

User: "давай"
AI: "✅ Відмінно! Створюю твоє тренування..."
[extracted: {..., ready_to_create: true}]
```

### Діалог 3: Неповна інформація

```
User: "інтервальна"
AI: "Чудово! Інтервальна тренування — це дуже ефективно! 🏃‍♂️
     Скільки часу плануєш бігти і яка буде інтенсивність?"
[extracted: {workout_type: "intervals"}]

User: "44 хвилин"
AI: "Супер! 44 хвилини інтервалів. Яка буде інтенсивність — середня чи висока?"
[extracted: {workout_type: "intervals", duration_minutes: 44}]

User: "класика джаз"
AI: "Хм, я бачу ти обрав музику (classical і jazz — чудовий вибір! 🎵),
     але мені ще потрібно знати інтенсивність тренування.
     Буде середня чи висока?"
[extracted: {workout_type: "intervals", duration_minutes: 44, genres: ["classical", "jazz"]}]

User: "середня"
AI: "Відмінно! Отже, середня інтервальна тренування на 44 хвилини
     під classical і jazz. Звучить ідеально! Створюємо?"
[extracted: {workout_type: "intervals", duration_minutes: 44, intensity: "moderate", genres: ["classical", "jazz"]}]

User: "так"
AI: "✅ Чудово! Створюю твій workout..."
[extracted: {..., ready_to_create: true}]
```

---

## 🔑 Ключові фічі промпту

### 1. Context Awareness
```
"Before responding, ALWAYS check:
1. What did user say in previous messages? (check chat history)
2. What parameters are already collected? (check collected_params)
3. What information is still missing?
4. Did user just answer your question or provide new info?

NEVER ask for information you already have!"
```

### 2. Smart Acknowledgment
```
"When user provides information:
1. ACKNOWLEDGE what they said specifically
2. CONFIRM you understood correctly
3. Tell them what's next or what's still needed
4. Keep it friendly and encouraging

Example:
User: '45 хвилин'
❌ BAD: 'Яка інтенсивність?' (ignored what user said)
✅ GOOD: 'Супер! 45 хвилин — чудова тривалість. Яка буде інтенсивність?'"
```

### 3. Flexible Flow
```
"User can provide information in ANY order:
- All at once: 'легка пробіжка 30 хв під рок'
- Step by step: 'легка' → '30 хв' → 'рок'
- Mixed: 'інтервальна 40 хв' → 'електро' → 'висока'

Always extract ALL parameters from current message and merge with existing."
```

### 4. Proactive Guidance
```
"Help user by:
- Suggesting typical values: 'наприклад, 30-60 хвилин'
- Explaining options: 'легка, середня або висока'
- Giving examples: 'рок, поп, електронна, джаз...'
- Being encouraging: 'Чудовий вибір! 🎵'"
```

### 5. Error Recovery
```
"If user says something unclear:
- Don't just repeat the same question
- Acknowledge what you understood
- Politely ask for clarification
- Give examples

Example:
User: 'так'
Context: You asked about duration
Response: 'Я розумію, що ти готовий, але мені ще потрібно знати
          тривалість тренування. Скільки хвилин плануєш бігти?
          Наприклад, 30, 45 або 60 хвилин.'"
```

---

## 🛠️ Імплементація

### Файлова структура:

```
apps/backend/app/
├── agents/
│   ├── base.py                          # BaseAgent (існує)
│   ├── supervisor.py                    # SupervisorAgent (оптимізувати)
│   ├── prompts/
│   │   ├── conversation_prompts.py      # ОНОВИТИ: новий WORKOUT_ASSISTANT_SYSTEM_PROMPT
│   │   └── parser_prompts.py            # (існує)
│   └── tools/
│       ├── workout_tools.py             # create_workout_from_params (існує)
│       └── parameter_extraction_tools.py # НОВИЙ: extract_workout_parameters
├── services/
│   ├── workout_builder.py               # ОНОВИТИ: WorkoutBuilder з новими tools
│   └── conversation_service.py          # (існує, без змін)
└── schemas/
    └── conversation.py                  # ConversationState (існує, без змін)
```

### Що потрібно зробити:

#### 1. **Створити новий tool**: `apps/backend/app/agents/tools/parameter_extraction_tools.py`
   - `extract_workout_parameters` tool
   - Використовує AI для витягування параметрів з контексту
   - Повертає structured JSON

#### 2. **Оновити промпт**: `apps/backend/app/agents/prompts/conversation_prompts.py`
   - Переписати `CONVERSATION_AGENT_SYSTEM_PROMPT`
   - Додати чіткі інструкції для tools
   - Додати приклади діалогів
   - Додати правила для уникнення loops

#### 3. **Оптимізувати**: `apps/backend/app/services/workout_builder.py`
   - Спростити `process_message()` — менше коду
   - Видалити rule-based parsing (`_extract_parameters_from_user_message`)
   - Покластися на AI через tools
   - Спростити `_build_conversation_context()`

#### 4. **Мінімальні зміни**: `apps/backend/app/agents/supervisor.py`
   - Залишити як є (вже добре працює)
   - Можливо додати логування для дебагу

---

## 📊 Переваги цього підходу

### ✅ Pros:
1. **Природний діалог** — AI розуміє контекст як людина
2. **Гнучкість** — користувач може відповідати як завгодно
3. **Простий код** — вся логіка в промпті, не в коді
4. **Легко покращувати** — просто редагуй промпт
5. **Масштабованість** — легко додати нові параметри

### ⚠️ Cons:
1. **Вартість** — кожне повідомлення = API call (але з gpt-3.5-turbo дешево)
2. **Латентність** — ~1-2 секунди на відповідь
3. **Непередбачуваність** — AI може іноді "галюцинувати"

### 🔧 Мітігація cons:
1. **Вартість**: використати `gpt-3.5-turbo` для діалогу, `gpt-4` тільки якщо застряг
2. **Латентність**: async + streaming (показувати відповідь по мірі генерації)
3. **Непередбачуваність**: structured output через function calling + валідація

---

## 🧪 Тестування

### Тест-кейси:

1. **Повна інформація одразу**
   - Input: "легка пробіжка 30 хв під рок"
   - Expected: одразу підтвердження

2. **Покрокове збирання**
   - Input: "хочу пробігти" → "30 хв" → "легка" → "рок" → "так"
   - Expected: агент веде діалог без повторень

3. **Неповна інформація**
   - Input: "інтервальна" → "44 хвилин" → "класика джаз" → "так" → "середня"
   - Expected: агент запитує що відсутнє

4. **Зміна рішення**
   - Input: "30 хв" → "ні, краще 45" → "легка" → "рок"
   - Expected: агент оновлює параметри

5. **Скасування**
   - Input: збір параметрів → "ні, не треба"
   - Expected: агент скасовує створення

---

## 📅 План виконання

### Phase 1: Core Implementation ⏱️ ~2-3 години

**Крок 1**: Створити `parameter_extraction_tools.py` (30 хв)
- [ ] Новий tool `extract_workout_parameters`
- [ ] Structured JSON output
- [ ] Тестування tool окремо

**Крок 2**: Переписати `CONVERSATION_AGENT_SYSTEM_PROMPT` (1 год)
- [ ] Новий промпт з чіткими інструкціями
- [ ] Додати приклади діалогів
- [ ] Додати правила для tools
- [ ] Додати parameter recognition rules

**Крок 3**: Оптимізувати `WorkoutBuilder` (1 год)
- [ ] Додати новий tool до self.tools
- [ ] Спростити `process_message()`
- [ ] Видалити rule-based parsing
- [ ] Спростити `_build_conversation_context()`
- [ ] Підвищити temperature до 0.8

**Крок 4**: Базове тестування (30 хв)
- [ ] Тест: "інтервальна" → "44 хвилин" → "класика джаз" → "середня" → "так"
- [ ] Перевірити що агент не повторює питання
- [ ] Перевірити що workout створюється

---

### Phase 2: Refinement ⏱️ ~2 години

**Крок 5**: Тестування різних сценаріїв (1 год)
- [ ] Повна інформація одразу
- [ ] Покрокове збирання
- [ ] Неповна інформація
- [ ] Зміна рішення
- [ ] Скасування

**Крок 6**: Покращення промпту (1 год)
- [ ] Аналіз помилок з тестування
- [ ] Додати більше прикладів
- [ ] Уточнити інструкції
- [ ] Покращити parameter recognition

---

### Phase 3: Polish ⏱️ ~1 година

**Крок 7**: Фінальні покращення (30 хв)
- [ ] Додати логування для дебагу
- [ ] Оптимізувати max_iterations (зменшити до 5)
- [ ] Перевірити error handling

**Крок 8**: Документація (30 хв)
- [ ] Оновити коментарі в коді
- [ ] Додати docstrings
- [ ] Створити приклади використання

---

### Загальний час: ~5-6 годин

### Після завершення:
- ✅ Діалог природний і без повторень
- ✅ Агент розуміє контекст
- ✅ Параметри витягуються коректно
- ✅ Workout створюється успішно
- ✅ Код простий і підтримуваний

---

## 🎯 Критерії успіху

Діалог вважається успішним, якщо:

1. ✅ Агент **ніколи не повторює** одне й те саме питання підряд
2. ✅ Агент **підтверджує** кожну отриману інформацію
3. ✅ Агент **розуміє контекст** з попередніх повідомлень
4. ✅ Користувач може дати **всю інформацію одразу** або **покроково**
5. ✅ Діалог **природний** і **дружній**, як з людиною
6. ✅ Агент **підказує** і **мотивує** користувача
7. ✅ Workout створюється **коректно** з правильними параметрами

---

## 💡 Додаткові ідеї

### Майбутні покращення:
1. **Персоналізація**: "Бачу, ти зазвичай бігаєш 45 хвилин. Сьогодні теж 45?"
2. **Рекомендації**: "Для інтервалів рекомендую electronic або techno — високий темп!"
3. **Мотивація**: "Вчора ти зробив 5 км за 30 хв — сьогодні спробуємо побити рекорд?"
4. **Голосовий ввід**: інтеграція з speech-to-text
5. **Мультимовність**: автоматичне визначення мови користувача

---

## 📚 Ресурси

- OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling
- Prompt Engineering Guide: https://www.promptingguide.ai/
- LangChain (опціонально): https://python.langchain.com/docs/

---

## 🔄 Порівняння: До vs Після

### ❌ ДО (проблемний діалог):

```
User: "інтервальна"
AI: "Яка планується тривалість та інтенсивність?"

User: "44 хвилин"
AI: "Яка планується тривалість та інтенсивність?" ← повторення!

User: "класика джаз"
AI: "Яка планується тривалість та інтенсивність?" ← повторення!

User: "так"
AI: "Яка планується тривалість та інтенсивність?" ← повторення!

User: "середня"
AI: "Супер! Отже, середня пробіжка на 44 хвилин під jazz, classical. Створюємо?"
```

**Проблеми:**
- 🔴 Агент повторює питання 4 рази
- 🔴 Не розпізнає відповіді користувача
- 🔴 Контекст не зберігається між повідомленнями

---

### ✅ ПІСЛЯ (очікуваний діалог):

```
User: "інтервальна"
AI: "Чудово! Інтервальна тренування — це дуже ефективно! 🏃‍♂️
     Скільки часу плануєш бігти і яка буде інтенсивність?"

User: "44 хвилин"
AI: "Супер! 44 хвилини інтервалів. Яка буде інтенсивність — середня чи висока?"

User: "класика джаз"
AI: "Бачу ти обрав музику (classical і jazz — чудовий вибір! 🎵),
     але мені ще потрібно знати інтенсивність тренування."

User: "середня"
AI: "Відмінно! Отже, середня інтервальна тренування на 44 хвилини
     під classical і jazz. Створюємо воркаут?"

User: "так"
AI: "✅ Чудово! Створюю твій workout..."
```

**Переваги:**
- ✅ Агент підтверджує кожну відповідь
- ✅ Не повторює питання
- ✅ Розуміє контекст
- ✅ Природний діалог
- ✅ Дружній і мотивуючий

---

## 📌 Ключові зміни в коді

### 1. Новий tool для витягування параметрів (AI-driven)
```python
# Замість rule-based parsing
@tool
def extract_workout_parameters(...) -> str:
    """AI витягує параметри з контексту"""
```

### 2. Оновлений промпт з чіткими інструкціями
```python
CONVERSATION_AGENT_SYSTEM_PROMPT = """
...
CRITICAL: CONTEXT AWARENESS
- BEFORE responding, check chat_history
- NEVER ask for information you already have
- ALWAYS acknowledge what user said
...
"""
```

### 3. Спрощений WorkoutBuilder
```python
# Видалено:
- _extract_parameters_from_user_message() (rule-based)
- _update_collected_parameters_from_message() (manual parsing)
- Складна логіка в _build_conversation_context()

# Додано:
- extract_workout_parameters tool (AI-driven)
- Простий context injection
- Покладання на AI через промпт
```

---

## 🚀 Готовність до імплементації

### Що маємо:
- ✅ Детальний план архітектури
- ✅ Структуру промпту
- ✅ Приклади діалогів
- ✅ План виконання (5-6 годин)
- ✅ Критерії успіху

### Наступні кроки:
1. Створити `parameter_extraction_tools.py`
2. Переписати промпт у `conversation_prompts.py`
3. Оптимізувати `WorkoutBuilder`
4. Тестувати та покращувати

---

**Автор плану**: AI Assistant
**Дата**: 2025-11-18
**Версія**: 2.0 (Multi-Agent LangChain)
**Статус**: Ready for Implementation ✅

**Архітектура**: Multi-Agent LangChain
**Підхід**: AI-driven через промпти + tools
**Очікуваний результат**: Природний діалог без повторень

