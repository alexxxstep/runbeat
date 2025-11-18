# AI Conversation Architecture Documentation

## 📚 Огляд

Система AI-driven діалогу для створення workout в RunBeat. Використовує мультиагентну LangChain архітектуру з акцентом на природний діалог і context awareness.

**Дата створення**: 2025-11-18
**Версія**: 2.0
**Статус**: ✅ Production Ready

---

## 🏗️ Архітектура

### Компоненти системи:

```
┌──────────────────────────────────────────────────────────────┐
│                        User Input                            │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────────┐
│                   SupervisorAgent                            │
│  • Управляє conversation state                               │
│  • Делегує WorkoutBuilder                                    │
│  • Обробляє створення workout                                │
│  Model: OPENAI_MODEL_SUPERVISOR (gpt-3.5-turbo)             │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────────┐
│                   WorkoutBuilder                             │
│  • Веде діалог з користувачем                                │
│  • Використовує LangChain tools                              │
│  • Повертає ConversationUpdate                               │
│  Model: OPENAI_MODEL_CONVERSATION (gpt-4-turbo/gpt-4o)      │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────────┐
│                   LangChain Tools                            │
│                                                              │
│  1. extract_workout_parameters                               │
│     • Витягує параметри з контексту                          │
│     • Повертає structured JSON                               │
│                                                              │
│  2. create_workout_from_params                               │
│     • Створює workout в БД                                   │
│     • Викликається при підтвердженні                         │
└──────────────────────────────────────────────────────────────┘
```

---

## 📦 Структура файлів

```
apps/backend/app/
├── agents/
│   ├── base.py                          # BaseAgent (існує)
│   ├── supervisor.py                    # SupervisorAgent
│   ├── prompts/
│   │   └── conversation_prompts.py      # CONVERSATION_AGENT_SYSTEM_PROMPT
│   └── tools/
│       ├── workout_tools.py             # create_workout_from_params
│       └── parameter_extraction_tools.py # extract_workout_parameters (НОВИЙ)
├── services/
│   ├── workout_builder.py               # WorkoutBuilder (оптимізований)
│   └── conversation_service.py          # Збереження в БД
├── schemas/
│   └── conversation.py                  # ConversationState, ConversationUpdate
└── api/routes/
    └── chat.py                          # /chat/message endpoint
```

---

## 🔧 Ключові компоненти

### 1. SupervisorAgent

**Файл**: `apps/backend/app/agents/supervisor.py`

**Відповідальність**:
- Управління conversation state для кожного користувача
- Делегування WorkoutBuilder для обробки повідомлень
- Обробка підтвердження та створення workout
- Збереження conversation в БД

**Методи**:
- `handle_message(user_id, message)` — головний entry point
- `_get_or_create_state(user_id)` — отримання/створення стану
- `clear_state(user_id)` — очищення після створення workout

---

### 2. WorkoutBuilder

**Файл**: `apps/backend/app/services/workout_builder.py`

**Відповідальність**:
- Ведення природного діалогу з користувачем
- Використання LangChain tools для витягування параметрів
- Генерація відповідей українською мовою
- Управління conversation flow

**Ключові зміни (v2.0)**:
- ✅ Додано `extract_workout_parameters` tool
- ✅ Видалено rule-based parsing (~400 рядків коду)
- ✅ Спрощено `_build_conversation_context()`
- ✅ Підвищено temperature до 0.8
- ✅ Зменшено max_iterations до 5

**Методи**:
- `process_message(state, user_message)` — обробка повідомлення
- `_build_conversation_context(state, user_message)` — побудова контексту
- `_get_fallback_response(state, user_message)` — fallback при помилках
- `_determine_question_type_from_response(response, state)` — визначення типу питання

---

### 3. extract_workout_parameters Tool

**Файл**: `apps/backend/app/agents/tools/parameter_extraction_tools.py`

**Призначення**: AI-driven витягування параметрів з контексту розмови

**Параметри**:
- `user_message` — поточне повідомлення користувача
- `conversation_history` — JSON історії розмови
- `current_params` — JSON поточних параметрів

**Повертає**:
```json
{
  "duration_minutes": int | null,
  "intensity": "low" | "moderate" | "high" | null,
  "workout_type": "steady" | "intervals" | "fartlek" | null,
  "genres": ["genre1", "genre2"],
  "all_collected": boolean
}
```

**Особливості**:
- ✅ Параметри **акумулюються** (не перезаписуються)
- ✅ Genres **нормалізуються** до англійських назв
- ✅ Підтримка української та англійської мов
- ✅ Robust error handling

---

### 4. CONVERSATION_AGENT_SYSTEM_PROMPT

**Файл**: `apps/backend/app/agents/prompts/conversation_prompts.py`

**Особливості**:
- 📝 Промпт на **англійській мові** (для кращої роботи GPT)
- 🇺🇦 Агент відповідає **українською**
- 🧠 Чіткі інструкції для **context awareness**
- 📚 Приклади діалогів (включно з проблемним сценарієм)
- 🚫 Правила для уникнення loops

**Структура**:
1. ROLE & PERSONALITY
2. MISSION & GOALS
3. CRITICAL: CONTEXT AWARENESS
4. TOOLS USAGE
5. CONVERSATION FLOW
6. PARAMETER RECOGNITION GUIDE
7. EXAMPLES OF GOOD CONVERSATION
8. CRITICAL RULES TO AVOID LOOPS
9. LANGUAGE & TONE

---

## 🔄 Conversation Flow

### Типовий діалог:

```
1. User: "інтервальна"
   ↓
   AI calls: extract_workout_parameters
   ↓
   AI: "Чудово! Інтервальна тренування — це дуже ефективно!
        Скільки часу плануєш бігти і яка буде інтенсивність?"

2. User: "44 хвилин"
   ↓
   AI calls: extract_workout_parameters
   ↓
   AI: "Супер! 44 хвилини інтервалів. Яка буде інтенсивність?"

3. User: "класика джаз"
   ↓
   AI calls: extract_workout_parameters
   ↓
   AI: "Бачу ти обрав музику (classical і jazz — чудовий вибір!),
        але мені ще потрібно знати інтенсивність."

4. User: "середня"
   ↓
   AI calls: extract_workout_parameters
   ↓
   AI: "Відмінно! Отже, середня інтервальна тренування на 44 хвилини
        під classical і jazz. Створюємо воркаут?"

5. User: "так"
   ↓
   AI calls: create_workout_from_params
   ↓
   AI: "✅ Чудово! Створюю твій workout..."
   ↓
   Supervisor: Очищує state, зберігає workout
```

---

## 🧪 Тестування

### Unit тести (29):
- `test_parameter_extraction_tools.py`
  - Витягування duration (3 тести)
  - Витягування intensity (3 тести)
  - Витягування workout type (3 тести)
  - Витягування genres (3 тести)
  - Merge parameters (6 тестів)
  - Check all collected (5 тестів)
  - Tool integration (4 тести)

### Integration тести (12):
- `test_workout_builder_integration.py`
  - Проблемний сценарій (1 тест)
  - All info at once (1 тест)
  - Context building (1 тест)
  - Fallback responses (4 тести)
  - Question type determination (3 тести)
  - Error handling (1 тест)
  - History management (1 тест)

**Загальне покриття**: 41 тест ✅

---

## 🚀 Deployment

### Environment Variables:

```bash
# OpenAI API
OPENAI_API_KEY=sk-...

# Models (optional, defaults to OPENAI_MODEL)
OPENAI_MODEL=gpt-4
OPENAI_MODEL_CONVERSATION=gpt-4-turbo  # Для природного діалогу
OPENAI_MODEL_SUPERVISOR=gpt-3.5-turbo  # Для оркестрації
OPENAI_MODEL_PARSER=gpt-3.5-turbo      # Для tools

# LangChain (optional)
USE_LANGCHAIN_SUPERVISOR=true
USE_LANGCHAIN_PARSER=true
```

### Запуск:

```bash
# Development
cd apps/backend
python -m uvicorn app.main:app --reload --port 8000

# Production
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 📊 Метрики та моніторинг

### Ключові метрики:

1. **Conversation completion rate** — % діалогів що завершилися створенням workout
2. **Average messages per conversation** — середня кількість повідомлень
3. **Parameter extraction accuracy** — точність витягування параметрів
4. **Response time** — час відповіді агента

### Логування:

```python
# Всі важливі події логуються через loguru
logger.info("WorkoutBuilder initialized with 2 tools")
logger.debug(f"Extracted parameters: {params}")
logger.error(f"Error in process_message: {e}")
```

---

## 🐛 Troubleshooting

### Проблема: Агент повторює питання

**Причина**: Параметри не витягуються або не зберігаються

**Рішення**:
1. Перевірити що `extract_workout_parameters` викликається
2. Перевірити що `collected_parameters` оновлюються
3. Перевірити логи: `logger.debug(f"Updated collected_parameters: {collected}")`

### Проблема: Агент не створює workout

**Причина**: Не всі параметри зібрані або user не підтвердив

**Рішення**:
1. Перевірити `all_collected` в response від `extract_workout_parameters`
2. Перевірити що user сказав "так"/"yes"/"ok"
3. Перевірити `state.last_question == "final_confirmation"`

### Проблема: 500 Error в API

**Причина**: Workout model validation error

**Рішення**:
1. Перевірити що `created_workout` має всі required поля
2. Додати валідацію перед створенням `Workout(**created_workout)`
3. Перевірити логи backend

---

## 🔮 Майбутні покращення

### Phase 1 (Short-term):
- [ ] Streaming responses для швидшої відповіді
- [ ] Персоналізація на основі user patterns
- [ ] A/B тестування різних промптів

### Phase 2 (Mid-term):
- [ ] Мультимовність (English, Polish, etc.)
- [ ] Голосовий ввід (speech-to-text)
- [ ] Рекомендації на основі історії

### Phase 3 (Long-term):
- [ ] Adaptive learning (покращення на основі feedback)
- [ ] Інтеграція з wearables (Garmin, Apple Watch)
- [ ] Predictive workout suggestions

---

## 📞 Контакти та підтримка

**Документація**: `docs/AI_CONVERSATION_IMPROVEMENT_PLAN.md`
**Тести**: `apps/backend/tests/test_*`
**Issues**: GitHub Issues

---

**Версія документації**: 1.0
**Останнє оновлення**: 2025-11-18
**Автор**: AI Assistant

