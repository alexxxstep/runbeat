# LangChain Multi-Agent System - Quick Start

**Дата:** 2025-11-14

---

## 🚀 Швидкий старт

### 1. Встановити залежності

```bash
cd apps/backend
pip install -r requirements.txt
```

### 2. Увімкнути LangChain WorkoutParserAgent

**В `.env` файлі:**
```env
USE_LANGCHAIN_PARSER=true
```

**Або через environment variable:**
```bash
export USE_LANGCHAIN_PARSER=true
```

### 3. Запустити сервер

```bash
uvicorn app.main:app --reload
```

### 4. Перевірити логи

У логах має з'явитися:
```
LangChain WorkoutParserAgent imported successfully
Using LangChain WorkoutParserAgent
```

---

## 📁 Структура проекту

```
apps/backend/app/
├── agents/                    # LangChain агенти
│   ├── __init__.py
│   ├── base.py               # Базовий клас
│   ├── parser.py             # WorkoutParserAgent ✅
│   ├── tools/                # Інструменти для агентів
│   │   ├── __init__.py
│   │   └── parser_tools.py   # Parser tools ✅
│   └── prompts/              # Промпти для агентів
│       ├── __init__.py
│       └── parser_prompts.py # Parser prompts ✅
│
└── services/
    ├── conversation_manager.py  # Інтегровано з LangChain ✅
    └── workout_parser_agent.py  # Legacy parser (backward compat)
```

---

## 🧪 Тестування

### Запустити тести для LangChain агентів:

```bash
cd apps/backend
pytest tests/test_langchain_parser_agent.py -v
```

### Запустити всі тести:

```bash
pytest tests/ -v
```

---

## 🔄 Як працює WorkoutParserAgent

### Flow:

```
User Message
    ↓
WorkoutParserAgent.parse()
    ├─ Step 1: Rule-based parsing (швидко, безкоштовно)
    │   └─ RuleBasedParser.parse()
    │       └─ Якщо успішно (confidence >= 0.9) → повертає WorkoutIntent
    │
    ├─ Step 2: AI parsing (якщо rule-based не спрацював)
    │   └─ LangChain Agent
    │       ├─ Tools: rule_based_parse, validate_intent
    │       ├─ Memory: ConversationBufferMemory
    │       └─ Output: WorkoutIntent (Pydantic)
    │
    └─ Step 3: Error handling
        └─ Fallback до rule-based або мінімальний intent
```

---

## 📝 Приклад використання

### У коді:

```python
from app.agents.parser import WorkoutParserAgent

# Створити агента
agent = WorkoutParserAgent()

# Парсити повідомлення
intent = await agent.parse(
    message="легка пробіжка 55 хвилин",
    conversation_history=[
        {"role": "user", "content": "хочу побігати"},
        {"role": "assistant", "content": "Скільки часу?"},
    ]
)

print(intent.workout_type)  # "continuous"
print(intent.duration_minutes)  # 55
print(intent.target_bpm_min)  # 110
```

---

## ⚙️ Feature Flags

**Доступні feature flags:**

- `USE_LANGCHAIN_PARSER` - використовувати LangChain WorkoutParserAgent
- `USE_LANGCHAIN_CURATOR` - використовувати LangChain MusicCuratorAgent (ще не реалізовано)
- `USE_LANGCHAIN_SUPERVISOR` - використовувати LangChain Supervisor (ще не реалізовано)

**За замовчуванням:** всі `false` (використовується legacy система)

---

## 🔍 Debugging

### Увімкнути verbose режим:

В `apps/backend/app/agents/parser.py`:
```python
self.agent_executor = AgentExecutor(
    ...
    verbose=True,  # Змінити на True
    ...
)
```

### Перевірити логи:

```bash
tail -f logs/runbeat_*.log | grep "LangChain\|WorkoutParserAgent"
```

---

## 📊 Порівняння: Legacy vs LangChain

| Критерій | Legacy | LangChain |
|----------|--------|-----------|
| **Швидкість** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ (rule-based first) |
| **Точність** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ (tools + memory) |
| **Розширюваність** | ⭐⭐ | ⭐⭐⭐⭐⭐ (легко додавати tools) |
| **Memory** | Ручне | Автоматичне |
| **Observability** | ⭐⭐ | ⭐⭐⭐⭐ (LangSmith) |

---

## ✅ Переваги LangChain версії

1. ✅ **Tools** - легко додавати нові інструменти
2. ✅ **Memory** - автоматичне управління conversation history
3. ✅ **Structured Outputs** - вбудована підтримка Pydantic
4. ✅ **Error Handling** - краща обробка помилок
5. ✅ **Observability** - можливість використовувати LangSmith

---

## 🐛 Troubleshooting

### Помилка: "LangChain not available"

**Рішення:**
```bash
pip install langchain langchain-openai langchain-community
```

### Помилка: "ImportError: cannot import name WorkoutParserAgent"

**Рішення:**
Перевірте, чи файл `apps/backend/app/agents/parser.py` існує та чи правильно імпортується.

### Помилка: "OpenAI API error"

**Рішення:**
Перевірте `OPENAI_API_KEY` в `.env` файлі.

---

## 📚 Документація

- [Детальний план міграції](LANGCHAIN_MIGRATION_PLAN.md)
- [Аналіз архітектури](LANGCHAIN_MULTIAGENT_ANALYSIS.md)
- [Статус міграції](LANGCHAIN_MIGRATION_STATUS.md)
- [Приклад реалізації](LANGCHAIN_IMPLEMENTATION_EXAMPLE.md)

---

## 🎯 Наступні кроки

1. Протестувати WorkoutParserAgent в реальних умовах
2. Реалізувати MusicCuratorAgent
3. Реалізувати ConversationAgent
4. Реалізувати WorkoutManagerAgent
5. Створити Supervisor

