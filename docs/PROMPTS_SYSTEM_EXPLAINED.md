# Система Prompts - Детальне Пояснення

**Дата:** 2025-11-14

---

## 📋 Огляд

Система prompts в RunBeat - це модульна архітектура для побудови промптів для OpenAI GPT-4. Вона складається з кількох компонентів, які комбінуються для створення ефективних промптів.

---

## 🏗️ Архітектура

```
┌─────────────────────────────────────────────────────────────┐
│                    Prompt System                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐      ┌──────────────────┐           │
│  │  PromptBuilder   │──────│  LLMService      │           │
│  │  (Orchestrator)  │      │  (OpenAI Client) │           │
│  └──────────────────┘      └──────────────────┘           │
│         │                                                    │
│         ├───► WorkoutExpert (workout_expert.py)            │
│         │     - Heart rate zones                            │
│         │     - Interval training                           │
│         │     - Workout types                               │
│         │                                                    │
│         ├───► MusicCurator (music_curator.py)              │
│         │     - BPM science                                 │
│         │     - Genre selection                             │
│         │     - Playlist validation                         │
│         │                                                    │
│         └───► SystemPrompts (system_prompts.py)            │
│               - Base system prompt                          │
│               - Version info                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Структура файлів

### 1. `__init__.py` - Експорт модулів

**Призначення:** Експортує всі необхідні класи та функції для використання в інших частинах системи.

**Що експортує:**

- `PromptBuilder` - основний клас для побудови промптів
- `PromptConfig` - конфігурація промптів
- `UserContext` - контекст користувача
- `ConversationState` - стан розмови
- `WORKOUT_EXPERT_SYSTEM` - системний промпт для експерта з тренувань
- `MUSIC_CURATOR_SYSTEM` - системний промпт для куратора музики
- Функції валідації та побудови промптів

---

### 2. `workout_expert.py` - Експерт з тренувань

**Призначення:** Містить знання про тренування, зони пульсу, інтервали.

**Що містить:**

- `WORKOUT_EXPERT_SYSTEM` - великий системний промпт з:
  - Heart rate zones (Zone 1-5)
  - BPM mapping для кожної зони
  - Interval training principles
  - Workout types (steady, progressive, intervals, fartlek)
  - Warm-up/cool-down структури
  - Приклади інтерпретації

**Приклад використання:**

```python
from app.services.prompts.workout_expert import WORKOUT_EXPERT_SYSTEM

# Використовується в PromptBuilder для додавання знань про тренування
```

---

### 3. `music_curator.py` - Куратор музики

**Призначення:** Містить знання про музику, BPM, жанри, валідацію плейлистів.

**Що містить:**

- `MUSIC_CURATOR_SYSTEM` - системний промпт з:

  - BPM science для бігу
  - Cadence synchronization
  - Zone-specific BPM recommendations
  - Genre selection principles
  - Playlist structure (warm-up, main, cool-down)

- Функції валідації:

  - `validate_bpm_progression()` - перевірка прогресу BPM
  - `validate_genre_coherence()` - перевірка узгодженості жанрів
  - `validate_playlist()` - загальна валідація плейлисту

- Функції побудови промптів:
  - `build_first_time_user_prompt()` - для нових користувачів
  - `build_returning_user_prompt()` - для постійних користувачів
  - `build_genre_specific_prompt()` - для конкретних жанрів
  - `build_mood_based_prompt()` - на основі настрою

**Приклад використання:**

```python
from app.services.prompts.music_curator import (
    MUSIC_CURATOR_SYSTEM,
    validate_playlist,
    build_first_time_user_prompt
)
```

---

### 4. `prompt_builder.py` - Основний оркестратор

**Призначення:** Комбінує всі компоненти для створення фінальних промптів.

**Основні класи:**

#### `PromptBuilder`

Головний клас для побудови промптів.

**Методи:**

1. **`build_system_prompt()`** - будує системний промпт

   - Комбінує BASE_SYSTEM_PROMPT
   - Додає WORKOUT_EXPERT_SYSTEM (якщо `include_workout_expert=True`)
   - Додає MUSIC_CURATOR_SYSTEM (якщо `include_music_curator=True`)
   - Додає user context

2. **`build_workout_parsing_prompt()`** - будує промпт для парсингу тренування

   - Додає conversation history
   - Додає user message
   - Додає формат виводу (JSON)
   - Додає приклади

3. **`build_playlist_generation_prompt()`** - будує промпт для генерації плейлисту

   - Використовує music curator system prompt
   - Додає workout intent
   - Додає user preferences
   - Додає previous playlists для навчання

4. **`build_messages()`** - будує повний список повідомлень для OpenAI API
   - Створює system message
   - Створює user message
   - Повертає список у форматі OpenAI

---

## 🔄 Flow використання

### Сценарій 1: Парсинг тренування (Parse Workout)

```
User: "Хочу пробігти 30 хв"
    ↓
ConversationManager.process_message()
    ↓
LLMService.parse_workout()
    ↓
PromptBuilder.build_messages(task="parse_workout")
    ↓
    ├── build_system_prompt()
    │   ├── BASE_SYSTEM_PROMPT
    │   └── WORKOUT_EXPERT_SYSTEM (include_workout_expert=True)
    │
    └── build_workout_parsing_prompt()
        ├── Conversation history
        ├── User message
        ├── Output format (JSON)
        └── Examples
    ↓
OpenAI API → WorkoutIntent
```

**Код:**

```python
# В ConversationManager
intent = await self.llm_service.parse_workout(
    user_message=message,
    user_context=user_context,
    conversation_state=conversation_state,
)

# В LLMService
messages = self.prompt_builder.build_messages(
    user_message=user_message,
    user_context=user_context,
    conversation_state=conversation_state,
    task="parse_workout",
)

# В PromptBuilder
def build_messages(self, task="parse_workout", ...):
    system_prompt = self.build_system_prompt(user_context)
    user_prompt = self.build_workout_parsing_prompt(...)
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
```

---

### Сценарій 2: Генерація плейлисту (Generate Playlist)

```
WorkoutIntent готовий
    ↓
ConversationManager._decide_next_action()
    ↓
LLMService.generate_playlist()
    ↓
PromptBuilder.build_playlist_generation_prompt()
    ↓
    ├── _build_music_curator_system_prompt()
    │   ├── MUSIC_CURATOR_SYSTEM
    │   ├── MUSIC_CURATOR_EXAMPLES
    │   ├── User preferences
    │   └── Learning from previous playlists
    │
    └── _build_playlist_request_prompt()
        ├── Workout type
        ├── Duration
        ├── BPM range
        ├── Energy profile
        └── Intervals (якщо є)
    ↓
OpenAI API → PlaylistResponse
```

**Код:**

```python
# В ConversationManager
playlist = await self.llm_service.generate_playlist(
    workout_intent=workout_intent,
    user_preferences=user_preferences,
)

# В LLMService
messages = self.prompt_builder.build_playlist_generation_prompt(
    workout_intent=workout_intent.model_dump(),
    user_preferences=user_preferences,
    previous_playlists=previous_playlists,
)

# В PromptBuilder
def build_playlist_generation_prompt(self, ...):
    system_prompt = self._build_music_curator_system_prompt(...)
    user_prompt = self._build_playlist_request_prompt(...)
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
```

---

## 🔍 Детальний розбір компонентів

### PromptBuilder.build_system_prompt()

**Що робить:**

1. Починає з BASE_SYSTEM_PROMPT
2. Додає WORKOUT_EXPERT_SYSTEM (якщо `include_workout_expert=True`)
3. Додає MUSIC_CURATOR_SYSTEM (якщо `include_music_curator=True`)
4. Додає user context (якщо надано)

**Приклад результату:**

```
You are RunBeat AI, an expert assistant for runners...

## Workout Expertise

You are an expert running coach...
[весь WORKOUT_EXPERT_SYSTEM]

## User Context
User ID: 123
Favorite genres: pop, rock
```

---

### PromptBuilder.build_workout_parsing_prompt()

**Що робить:**

1. Додає conversation history (останні 3 повідомлення)
2. Додає user message
3. Додає формат виводу (JSON структура)
4. Додає приклади парсингу
5. Додає інструкції

**Приклад результату:**

```
## Conversation History
User: Хочу пробігти
Assistant: Який тип тренування?

## Task
Parse the user's workout request into structured JSON format.

User message: "30 хв легкий біг"

## Output Format
{
  "type": "steady|progressive|intervals|fartlek",
  "duration_minutes": <number>,
  ...
}

## Examples
"Хочу пробігти 40 хв з інтервалами" → {...}
```

---

### PromptBuilder.build_playlist_generation_prompt()

**Що робить:**

1. Будує music curator system prompt:
   - Базовий MUSIC_CURATOR_SYSTEM
   - Приклади
   - User preferences
   - Learning from history
2. Будує user prompt:
   - Workout parameters
   - BPM range
   - Energy profile
   - Intervals (якщо є)

**Приклад результату:**

```
System:
You are an expert music curator...
[весь MUSIC_CURATOR_SYSTEM]

## User Music Profile
Favorite Genres: pop, rock
Energy Preference: high

User:
Generate a workout playlist with the following parameters:

**Workout Type:** intervals
**Duration:** 30 minutes
**Target BPM Range:** 140-170
**Energy Profile:** building
```

---

## 🧪 Перевірка роботи

### Тест 1: Створення PromptBuilder

```python
from app.services.prompts import PromptBuilder

# Створення з дефолтною конфігурацією
pb = PromptBuilder()
# ✅ Працює: include_workout_expert=True, include_music_curator=False
```

### Тест 2: Побудова системного промпту

```python
from app.services.prompts import PromptBuilder, UserContext

pb = PromptBuilder()
user_ctx = UserContext(
    user_id="123",
    music_preferences=["pop", "rock"]
)

system_prompt = pb.build_system_prompt(user_context=user_ctx)
# ✅ Містить BASE_SYSTEM_PROMPT
# ✅ Містить WORKOUT_EXPERT_SYSTEM
# ✅ Містить user context
```

### Тест 3: Побудова промпту для парсингу

```python
from app.services.prompts import PromptBuilder, ConversationState

pb = PromptBuilder()
conv_state = ConversationState(
    messages=[
        {"role": "user", "content": "Хочу пробігти"},
        {"role": "assistant", "content": "Який тип?"}
    ]
)

prompt = pb.build_workout_parsing_prompt(
    user_message="30 хв легкий біг",
    conversation_state=conv_state
)
# ✅ Містить conversation history
# ✅ Містить user message
# ✅ Містить формат виводу
```

### Тест 4: Побудова промпту для генерації плейлисту

```python
from app.services.prompts import PromptBuilder

pb = PromptBuilder()
workout_intent = {
    "workout_type": "intervals",
    "duration_minutes": 30,
    "target_bpm_min": 140,
    "target_bpm_max": 170,
    "energy_profile": "building"
}

messages = pb.build_playlist_generation_prompt(
    workout_intent=workout_intent,
    user_preferences={"top_genres": ["pop", "rock"]}
)
# ✅ Повертає список з 2 повідомлень
# ✅ System message містить MUSIC_CURATOR_SYSTEM
# ✅ User message містить workout parameters
```

---

## 📊 Конфігурація

### PromptConfig

```python
from app.services.prompts import PromptBuilder, PromptConfig

config = PromptConfig(
    include_workout_expert=True,    # Додати знання про тренування
    include_music_curator=False,    # Не додавати знання про музику (для парсингу)
    response_format="json",         # Формат відповіді
    temperature=0.3,                # Температура для LLM
    max_tokens=500                  # Максимум токенів
)

pb = PromptBuilder(config=config)
```

**Коли використовувати:**

- **Для парсингу тренування:** `include_workout_expert=True`, `include_music_curator=False`
- **Для генерації плейлисту:** `include_music_curator=True` (автоматично в `build_playlist_generation_prompt`)

---

## 🔗 Інтеграція з LLMService

### LLMService використовує PromptBuilder

```python
class LLMService:
    def __init__(self, prompt_config: Optional[PromptConfig] = None):
        self.prompt_builder = PromptBuilder(config=prompt_config)

    async def parse_workout(self, ...):
        messages = self.prompt_builder.build_messages(
            user_message=user_message,
            task="parse_workout",
            ...
        )
        # Відправка в OpenAI

    async def generate_playlist(self, ...):
        messages = self.prompt_builder.build_playlist_generation_prompt(
            workout_intent=workout_intent.model_dump(),
            ...
        )
        # Відправка в OpenAI
```

---

## ✅ Висновок

**Система prompts працює так:**

1. **PromptBuilder** - оркеструє всі компоненти
2. **WorkoutExpert** - надає знання про тренування
3. **MusicCurator** - надає знання про музику
4. **SystemPrompts** - базові системні промпти

**Flow:**

- Парсинг: `PromptBuilder` → `WorkoutExpert` → OpenAI
- Генерація: `PromptBuilder` → `MusicCurator` → OpenAI

**Переваги модульної архітектури:**

- ✅ Легко додавати нові компоненти
- ✅ Можна тестувати окремо
- ✅ Можна налаштовувати для різних задач
- ✅ Легко підтримувати

---

## 🧪 Тестування

Всі компоненти протестовані:

- ✅ `test_music_curator.py` - тести для music curator
- ✅ `test_conversation_manager.py` - інтеграційні тести
- ✅ PromptBuilder створюється успішно
- ✅ Всі методи працюють коректно

---

**Статус:** ✅ Система працює правильно та ефективно
