# PromptBuilder - Детальне Пояснення

**Файл:** `apps/backend/app/services/prompts/prompt_builder.py`

---

## 🎯 Призначення

`PromptBuilder` - це оркестратор, який комбінує різні компоненти для створення промптів для OpenAI GPT-4. Він забезпечує модульність та гнучкість у побудові промптів.

---

## 📦 Структура класів

### 1. `UserContext` - Контекст користувача

```python
class UserContext(BaseModel):
    user_id: Optional[str]                    # ID користувача
    workout_history: Optional[List[Dict]]     # Історія тренувань
    music_preferences: Optional[List[str]]    # Улюблені жанри
    fitness_level: Optional[str]              # Рівень фітнесу
    language: Optional[str] = "en"            # Мова
```

**Приклад використання:**
```python
user_ctx = UserContext(
    user_id="123",
    music_preferences=["pop", "rock"],
    fitness_level="intermediate"
)
```

---

### 2. `ConversationState` - Стан розмови

```python
class ConversationState(BaseModel):
    messages: List[Dict[str, str]]           # Попередні повідомлення
    current_intent: Optional[str]            # Поточний intent
    clarification_needed: bool = False       # Чи потрібне уточнення
```

**Приклад використання:**
```python
conv_state = ConversationState(
    messages=[
        {"role": "user", "content": "Хочу пробігти"},
        {"role": "assistant", "content": "Скільки часу?"}
    ]
)
```

---

### 3. `PromptConfig` - Конфігурація

```python
class PromptConfig(BaseModel):
    include_workout_expert: bool = True      # Додати знання про тренування
    include_music_curator: bool = False      # Додати знання про музику
    response_format: str = "json"            # Формат відповіді
    temperature: float = 0.3                 # Температура LLM
    max_tokens: int = 500                    # Максимум токенів
```

**Приклад використання:**
```python
config = PromptConfig(
    include_workout_expert=True,
    include_music_curator=False,  # Для парсингу не потрібно
    temperature=0.3
)
pb = PromptBuilder(config=config)
```

---

## 🔧 Основні методи

### 1. `build_system_prompt()` - Побудова системного промпту

**Що робить:**
Комбінує базовий системний промпт з експертними знаннями.

**Алгоритм:**
```
1. Додати BASE_SYSTEM_PROMPT
2. Якщо include_workout_expert=True → додати WORKOUT_EXPERT_SYSTEM
3. Якщо include_music_curator=True → додати MUSIC_CURATOR_SYSTEM
4. Якщо є user_context → додати інформацію про користувача
```

**Приклад:**
```python
pb = PromptBuilder()
user_ctx = UserContext(music_preferences=["pop", "rock"])

system_prompt = pb.build_system_prompt(user_context=user_ctx)
# Результат:
# "You are RunBeat AI..."
# + "\n\n## Workout Expertise\n"
# + [весь WORKOUT_EXPERT_SYSTEM]
# + "\n\n## User Context\n"
# + "Preferred genres: pop, rock"
```

---

### 2. `build_workout_parsing_prompt()` - Промпт для парсингу тренування

**Що робить:**
Створює промпт для парсингу повідомлення користувача в структурований WorkoutIntent.

**Алгоритм:**
```
1. Додати conversation history (останні 3 повідомлення)
2. Додати Task instruction
3. Додати Output format (JSON структура)
4. Додати Examples (приклади парсингу)
5. Додати Instructions (правила парсингу)
```

**Приклад результату:**
```
## Conversation History
User: Хочу пробігти
Assistant: Скільки часу?

## Task
Parse the user's workout request into structured JSON format.
IMPORTANT: If the user provides duration AND intensity/pace information,
the intent is COMPLETE...

User message: "37 хв в легкому темпі"

## Output Format
{
  "type": "steady|progressive|intervals|fartlek",
  "duration_minutes": <number>,
  ...
}

## Examples
"37 хв в легкому темпі" → {...}

## Instructions
1. Use your workout expertise...
2. Map intensity keywords...
...
```

**Використання:**
```python
prompt = pb.build_workout_parsing_prompt(
    user_message="37 хв в легкому темпі",
    conversation_state=conv_state
)
```

---

### 3. `build_playlist_generation_prompt()` - Промпт для генерації плейлисту

**Що робить:**
Створює список повідомлень для OpenAI API для генерації плейлисту.

**Алгоритм:**
```
1. Побудувати system prompt (_build_music_curator_system_prompt):
   - MUSIC_CURATOR_SYSTEM
   - MUSIC_CURATOR_EXAMPLES
   - User preferences
   - Learning from previous playlists

2. Побудувати user prompt (_build_playlist_request_prompt):
   - Workout type
   - Duration
   - BPM range
   - Energy profile
   - Intervals (якщо є)

3. Повернути список: [system_message, user_message]
```

**Приклад:**
```python
workout_intent = {
    "workout_type": "steady",
    "duration_minutes": 37,
    "target_bpm_min": 110,
    "target_bpm_max": 130,
    "energy_profile": "steady"
}

messages = pb.build_playlist_generation_prompt(
    workout_intent=workout_intent,
    user_preferences={"top_genres": ["pop", "rock"]}
)

# Результат:
# [
#   {
#     "role": "system",
#     "content": "You are an expert music curator...\n\n## User Music Profile\n**Favorite Genres:** pop, rock"
#   },
#   {
#     "role": "user",
#     "content": "Generate a workout playlist...\n**Workout Type:** steady\n**Duration:** 37 minutes..."
#   }
# ]
```

---

### 4. `build_messages()` - Побудова повного списку повідомлень

**Що робить:**
Створює готовий список повідомлень для OpenAI API.

**Алгоритм:**
```
1. Побудувати system prompt
2. Побудувати user prompt залежно від task:
   - "parse_workout" → build_workout_parsing_prompt()
   - "curate_music" → user_message напряму
   - інше → user_message напряму
3. Повернути [system_message, user_message]
```

**Приклад:**
```python
messages = pb.build_messages(
    user_message="37 хв в легкому темпі",
    user_context=user_ctx,
    conversation_state=conv_state,
    task="parse_workout"
)

# Використання в OpenAI API:
response = await client.beta.chat.completions.parse(
    model="gpt-4",
    messages=messages,
    response_format=WorkoutIntent
)
```

---

## 🔄 Повний Flow використання

### Сценарій 1: Парсинг тренування

```python
# 1. Створити PromptBuilder
pb = PromptBuilder()

# 2. Створити контекст
user_ctx = UserContext(language="uk")
conv_state = ConversationState(messages=[...])

# 3. Побудувати повідомлення
messages = pb.build_messages(
    user_message="37 хв в легкому темпі",
    user_context=user_ctx,
    conversation_state=conv_state,
    task="parse_workout"
)

# 4. Відправити в OpenAI
response = await client.beta.chat.completions.parse(
    model="gpt-4",
    messages=messages,
    response_format=WorkoutIntent
)

# 5. Отримати WorkoutIntent
intent = response.choices[0].message.parsed
```

**Що відбувається всередині:**

1. `build_messages()` викликає:
   - `build_system_prompt()` → додає WORKOUT_EXPERT_SYSTEM
   - `build_workout_parsing_prompt()` → створює user prompt з прикладами

2. Результат:
   ```python
   [
     {
       "role": "system",
       "content": "You are RunBeat AI...\n\n## Workout Expertise\n[весь WORKOUT_EXPERT_SYSTEM]"
     },
     {
       "role": "user",
       "content": "## Conversation History\n...\n## Task\n...\nUser message: \"37 хв в легкому темпі\"\n## Examples\n..."
     }
   ]
   ```

---

### Сценарій 2: Генерація плейлисту

```python
# 1. Створити PromptBuilder (з music_curator)
config = PromptConfig(include_music_curator=True)
pb = PromptBuilder(config=config)

# 2. Побудувати промпт
workout_intent = {
    "workout_type": "steady",
    "duration_minutes": 37,
    "target_bpm_min": 110,
    "target_bpm_max": 130
}

messages = pb.build_playlist_generation_prompt(
    workout_intent=workout_intent,
    user_preferences={"top_genres": ["pop"]}
)

# 3. Відправити в OpenAI
response = await client.beta.chat.completions.parse(
    model="gpt-4",
    messages=messages,
    response_format=PlaylistResponse
)
```

**Що відбувається всередині:**

1. `build_playlist_generation_prompt()` викликає:
   - `_build_music_curator_system_prompt()` → додає MUSIC_CURATOR_SYSTEM + user preferences
   - `_build_playlist_request_prompt()` → створює user prompt з workout parameters

2. Результат:
   ```python
   [
     {
       "role": "system",
       "content": "[MUSIC_CURATOR_SYSTEM]\n\n## User Music Profile\n**Favorite Genres:** pop"
     },
     {
       "role": "user",
       "content": "Generate a workout playlist...\n**Workout Type:** steady\n**Duration:** 37 minutes..."
     }
   ]
   ```

---

## 🎨 Допоміжні методи

### `_build_music_curator_system_prompt()`

**Що робить:**
Побудова системного промпту для music curator з персоналізацією.

**Алгоритм:**
```
1. Додати MUSIC_CURATOR_SYSTEM
2. Додати MUSIC_CURATOR_EXAMPLES
3. Якщо є user_preferences → додати User Music Profile
4. Якщо є previous_playlists → додати Learning from User History
   - Аналізує skip rates по жанрах
   - Додає рекомендації на основі історії
```

**Приклад:**
```python
system_prompt = pb._build_music_curator_system_prompt(
    user_preferences={"top_genres": ["pop", "rock"]},
    previous_playlists=[...]
)

# Результат містить:
# - MUSIC_CURATOR_SYSTEM
# - "## User Music Profile\n**Favorite Genres:** pop, rock"
# - "## Learning from User History\n- ✓ pop: High engagement..."
```

---

### `_build_playlist_request_prompt()`

**Що робить:**
Створює user prompt з параметрами тренування.

**Алгоритм:**
```
1. Додати базові параметри:
   - Workout Type
   - Duration
   - Target BPM Range
   - Energy Profile

2. Якщо є intervals → додати деталі інтервалів
3. Якщо є mood → додати mood
4. Якщо є genre_preferences → додати жанри
5. Додати інструкції для генерації
```

**Приклад:**
```python
prompt = pb._build_playlist_request_prompt(
    workout_intent={
        "workout_type": "intervals",
        "duration_minutes": 30,
        "target_bpm_min": 140,
        "target_bpm_max": 170,
        "intervals": [...]
    }
)

# Результат:
# "Generate a workout playlist with the following parameters:
# **Workout Type:** intervals
# **Duration:** 30 minutes
# **Target BPM Range:** 140-170
# **Intervals:** 5 intervals
#   - Interval 1: work for 3 min at 150 BPM
# ..."
```

---

### `_analyze_previous_playlists()`

**Що робить:**
Аналізує історію плейлистів користувача для навчання.

**Алгоритм:**
```
1. Пройти по всіх плейлистах
2. Для кожного треку:
   - Визначити жанр
   - Перевірити чи був пропущений (skipped)
3. Порахувати skip rate для кожного жанру
4. Повернути статистику
```

**Приклад:**
```python
stats = pb._analyze_previous_playlists([
    {
        "tracks": [
            {"genre": "pop", "skipped": False},
            {"genre": "pop", "skipped": True},
            {"genre": "rock", "skipped": False}
        ]
    }
])

# Результат:
# {
#   "pop": {
#     "total_tracks": 2,
#     "skipped_tracks": 1,
#     "skip_rate": 0.5
#   },
#   "rock": {
#     "total_tracks": 1,
#     "skipped_tracks": 0,
#     "skip_rate": 0.0
#   }
# }
```

---

## 🔍 Детальний розбір `build_workout_parsing_prompt()`

Це найважливіший метод для парсингу. Розберемо його покроково:

### Крок 1: Conversation History

```python
if conversation_state and conversation_state.messages:
    prompt_parts.append("## Conversation History\n")
    for msg in conversation_state.messages[-3:]:  # Останні 3 повідомлення
        role = msg.get("role", "user")
        content = msg.get("content", "")
        prompt_parts.append(f"{role.capitalize()}: {content}")
```

**Результат:**
```
## Conversation History
User: Хочу пробігти
Assistant: Скільки часу?
```

---

### Крок 2: Task Instruction

```python
prompt_parts.append("\n## Task\n")
prompt_parts.append(
    "Parse the user's workout request into structured JSON format. "
    "IMPORTANT: If the user provides duration AND intensity/pace information, "
    "the intent is COMPLETE and you should set needs_clarification=false with high confidence (0.9+)."
)
```

**Важливо:** Це правило каже LLM, що якщо є тривалість + інтенсивність, intent повний!

---

### Крок 3: Output Format

```python
prompt_parts.append("## Output Format\n")
prompt_parts.append("""{
  "type": "steady|progressive|intervals|fartlek",
  "duration_minutes": <number>,
  "intensity": "low|moderate|high",
  "hr_zones": [<min>, <max>],
  "confidence": <0-1>,
  "needs_clarification": <bool>,
  "clarification_question": "<string if needed>"
}""")
```

Це структура, яку має повернути LLM.

---

### Крок 4: Examples

```python
prompt_parts.append('''"37 хв в легкому темпі" →
{
  "type": "steady",
  "duration_minutes": 37,
  "intensity": "low",
  "hr_zones": [110, 130],
  "confidence": 0.95,
  "needs_clarification": false
}''')
```

**Важливо:** Приклади показують LLM як правильно парсити українські фрази!

---

### Крок 5: Instructions

```python
prompt_parts.append("""1. Use your workout expertise to interpret the user's intent
2. Map intensity keywords to appropriate HR zones and BPM:
   - "легкий", "легкому", "easy" → low intensity → Zone 1-2 (110-130 BPM)
   - "темповий", "tempo" → moderate intensity → Zone 2-3 (130-160 BPM)
   - "швидкий", "інтервали" → high intensity → Zone 4-5 (160-180 BPM)
3. When user provides duration AND intensity/pace, consider the intent COMPLETE
...""")
```

**Важливо:** Чітке маппінг ключових слів на інтенсивність та BPM!

---

## 🎯 Ключові особливості

### 1. Модульність

Кожен компонент (WorkoutExpert, MusicCurator) може бути включений або виключений:

```python
# Для парсингу - тільки WorkoutExpert
config = PromptConfig(include_workout_expert=True, include_music_curator=False)

# Для генерації - тільки MusicCurator
config = PromptConfig(include_workout_expert=False, include_music_curator=True)
```

---

### 2. Персоналізація

User context додається динамічно:

```python
user_ctx = UserContext(
    music_preferences=["pop", "rock"],
    fitness_level="intermediate"
)

# В system prompt додасться:
# "## User Context
# Preferred genres: pop, rock
# User fitness level: intermediate"
```

---

### 3. Контекст розмови

Conversation history додається для багаторазової розмови:

```python
conv_state = ConversationState(
    messages=[
        {"role": "user", "content": "Хочу пробігти"},
        {"role": "assistant", "content": "Скільки часу?"}
    ]
)

# В prompt додасться:
# "## Conversation History
# User: Хочу пробігти
# Assistant: Скільки часу?"
```

---

### 4. Навчання з історії

Аналіз попередніх плейлистів для покращення рекомендацій:

```python
previous_playlists = [
    {"tracks": [{"genre": "pop", "skipped": False}, ...]}
]

# В system prompt додасться:
# "## Learning from User History
# - ✓ pop: High engagement (skip rate 0%)"
```

---

## 📊 Приклад повного промпту

### Для парсингу "37 хв в легкому темпі":

**System message:**
```
You are RunBeat AI, an expert assistant for runners...

## Workout Expertise

You are an expert running coach...
[весь WORKOUT_EXPERT_SYSTEM з зонами пульсу, інтервалами, тощо]
```

**User message:**
```
## Task
Parse the user's workout request into structured JSON format.
IMPORTANT: If the user provides duration AND intensity/pace information,
the intent is COMPLETE...

User message: "37 хв в легкому темпі"

## Output Format
{...}

## Examples
"37 хв в легкому темпі" →
{
  "type": "steady",
  "duration_minutes": 37,
  "intensity": "low",
  "hr_zones": [110, 130],
  "confidence": 0.95,
  "needs_clarification": false
}

## Instructions
1. Use your workout expertise...
2. Map intensity keywords:
   - "легкий", "легкому" → low intensity → Zone 1-2 (110-130 BPM)
...
```

---

## ✅ Висновок

**PromptBuilder працює як фабрика промптів:**

1. **Модульність** - компоненти можна комбінувати
2. **Персоналізація** - додає user context
3. **Контекст** - використовує conversation history
4. **Навчання** - аналізує історію для покращення
5. **Гнучкість** - різні конфігурації для різних задач

**Основні методи:**
- `build_system_prompt()` - системний промпт
- `build_workout_parsing_prompt()` - для парсингу
- `build_playlist_generation_prompt()` - для генерації
- `build_messages()` - готовий список для OpenAI API

---

**Статус:** ✅ Працює правильно та ефективно

