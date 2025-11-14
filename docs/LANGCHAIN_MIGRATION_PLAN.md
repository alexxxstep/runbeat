# Детальний план міграції на LangChain Multi-Agent System

**Дата:** 2025-11-14
**Статус:** 🚧 В процесі

---

## 📋 Загальний огляд

**Мета:** Мігрувати поточну систему на LangChain Multi-Agent System для покращення структури коду, спрощення розширення та додавання нових можливостей.

**Тривалість:** 8-12 днів
**Підхід:** Поетапна міграція з backward compatibility

---

## 🎯 Фаза 1: Підготовка (День 1-2)

### Завдання 1.1: Встановити залежності

**Файл:** `apps/backend/requirements.txt`

```bash
# Додати:
langchain==0.1.0
langchain-openai==0.0.2
langchain-community==0.0.10
langsmith==0.0.65  # Для observability (опціонально)
```

**Критерії успіху:**
- ✅ Всі залежності встановлені
- ✅ Немає конфліктів версій
- ✅ Тести проходять

---

### Завдання 1.2: Створити структуру директорій

**Структура:**
```
apps/backend/app/
├── agents/
│   ├── __init__.py
│   ├── base.py              # Базовий клас агента
│   ├── conversation.py      # ConversationAgent
│   ├── parser.py            # WorkoutParserAgent
│   ├── curator.py           # MusicCuratorAgent
│   ├── manager.py           # WorkoutManagerAgent
│   └── supervisor.py        # ConversationOrchestrator
│
├── agents/
│   └── tools/
│       ├── __init__.py
│       ├── spotify_tools.py
│       ├── database_tools.py
│       ├── parser_tools.py
│       └── workout_tools.py
│
└── agents/
    └── prompts/
        ├── __init__.py
        ├── conversation_prompts.py
        ├── parser_prompts.py
        ├── curator_prompts.py
        └── manager_prompts.py
```

**Критерії успіху:**
- ✅ Всі директорії створені
- ✅ `__init__.py` файли на місці
- ✅ Структура готова для коду

---

### Завдання 1.3: Створити базові класи

**Файл:** `apps/backend/app/agents/base.py`

**Функціональність:**
- Базовий клас `BaseAgent`
- Загальна логіка для всіх агентів
- Memory management
- Error handling

**Критерії успіху:**
- ✅ Базовий клас створено
- ✅ Можна наслідувати для інших агентів

---

## 🎯 Фаза 2: Tools (День 2-3)

### Завдання 2.1: Parser Tools

**Файл:** `apps/backend/app/agents/tools/parser_tools.py`

**Tools:**
- `rule_based_parse(message: str) -> Optional[WorkoutIntent]`
- `validate_intent(intent: WorkoutIntent) -> bool`
- `infer_missing_fields(intent: WorkoutIntent) -> WorkoutIntent`

**Критерії успіху:**
- ✅ Всі tools створені
- ✅ Інтегровані з існуючим RuleBasedParser
- ✅ Тести проходять

---

### Завдання 2.2: Database Tools

**Файл:** `apps/backend/app/agents/tools/database_tools.py`

**Tools:**
- `get_user_preferences(user_id: str) -> Dict`
- `save_conversation(conversation_id: str, messages: List) -> bool`
- `get_conversation_history(conversation_id: str) -> List`
- `create_workout(user_id: str, workout_intent: WorkoutIntent) -> str`
- `activate_workout(workout_id: str) -> bool`

**Критерії успіху:**
- ✅ Всі tools створені
- ✅ Інтегровані з SupabaseService
- ✅ Тести проходять

---

### Завдання 2.3: Spotify Tools

**Файл:** `apps/backend/app/agents/tools/spotify_tools.py`

**Tools:**
- `search_spotify_tracks(query: str, genre: str, bpm_range: Tuple[int, int], limit: int = 10) -> List[Track]`
- `get_user_music_history(user_id: str) -> List[Playlist]`
- `create_spotify_playlist(user_id: str, tracks: List[Track], name: str) -> Dict`

**Критерії успіху:**
- ✅ Всі tools створені
- ✅ Інтегровані з SpotifyService
- ✅ Тести проходять

---

### Завдання 2.4: Workout Tools

**Файл:** `apps/backend/app/agents/tools/workout_tools.py`

**Tools:**
- `calculate_bpm_progression(workout_type: str, duration: int) -> List[int]`
- `get_active_workout(user_id: str) -> Optional[Workout]`

**Критерії успіху:**
- ✅ Всі tools створені
- ✅ Тести проходять

---

## 🎯 Фаза 3: WorkoutParserAgent (День 3-4)

### Завдання 3.1: Створити промпти

**Файл:** `apps/backend/app/agents/prompts/parser_prompts.py`

**Промпти:**
- `PARSER_AGENT_SYSTEM_PROMPT`
- `PARSER_AGENT_USER_PROMPT_TEMPLATE`

**Критерії успіху:**
- ✅ Промпти створені
- ✅ Включають всі необхідні інструкції
- ✅ Тестування на прикладах

---

### Завдання 3.2: Реалізувати WorkoutParserAgent

**Файл:** `apps/backend/app/agents/parser.py`

**Функціональність:**
- Ініціалізація з LangChain
- Інтеграція з RuleBasedParser
- Structured outputs (Pydantic)
- Memory management
- Error handling

**Критерії успіху:**
- ✅ Agent створено
- ✅ Працює з rule-based fallback
- ✅ Повертає WorkoutIntent
- ✅ Тести проходять

---

### Завдання 3.3: Інтегрувати в ConversationManager

**Файл:** `apps/backend/app/services/conversation_manager.py`

**Зміни:**
- Додати опцію використання LangChain WorkoutParserAgent
- Зберегти backward compatibility
- Додати feature flag

**Критерії успіху:**
- ✅ Інтеграція завершена
- ✅ Backward compatibility збережено
- ✅ Можна перемикати між старим та новим
- ✅ Тести проходять

---

### Завдання 3.4: Тести

**Файл:** `apps/backend/tests/test_langchain_parser_agent.py`

**Тести:**
- Rule-based parsing
- AI parsing fallback
- Memory management
- Error handling
- Integration tests

**Критерії успіху:**
- ✅ Всі тести проходять
- ✅ Покриття > 80%

---

## 🎯 Фаза 4: MusicCuratorAgent (День 5-6)

### Завдання 4.1: Створити промпти

**Файл:** `apps/backend/app/agents/prompts/curator_prompts.py`

**Промпти:**
- `CURATOR_AGENT_SYSTEM_PROMPT`
- Інтеграція з існуючими music_curator промптами

**Критерії успіху:**
- ✅ Промпти створені
- ✅ Включають музичну науку
- ✅ Тестування

---

### Завдання 4.2: Реалізувати MusicCuratorAgent

**Файл:** `apps/backend/app/agents/curator.py`

**Функціональність:**
- Генерація плейлисту
- Використання Spotify tools
- Structured outputs (PlaylistResponse)
- User preferences integration

**Критерії успіху:**
- ✅ Agent створено
- ✅ Генерує плейлисти
- ✅ Використовує Spotify tools
- ✅ Тести проходять

---

### Завдання 4.3: Інтегрувати в систему

**Зміни:**
- Оновити ConversationManager
- Оновити LLMService (додати fallback)

**Критерії успіху:**
- ✅ Інтеграція завершена
- ✅ Тести проходять

---

## 🎯 Фаза 5: ConversationAgent (День 7)

### Завдання 5.1: Створити промпти

**Файл:** `apps/backend/app/agents/prompts/conversation_prompts.py`

**Промпти:**
- `CONVERSATION_AGENT_SYSTEM_PROMPT`
- Guidelines для спілкування

**Критерії успіху:**
- ✅ Промпти створені
- ✅ Тестування

---

### Завдання 5.2: Реалізувати ConversationAgent

**Файл:** `apps/backend/app/agents/conversation.py`

**Функціональність:**
- Спілкування з користувачем
- Використання database tools
- Memory management
- Natural language responses

**Критерії успіху:**
- ✅ Agent створено
- ✅ Спілкується з користувачем
- ✅ Тести проходять

---

## 🎯 Фаза 6: WorkoutManagerAgent (День 8)

### Завдання 6.1: Створити промпти

**Файл:** `apps/backend/app/agents/prompts/manager_prompts.py`

**Промпти:**
- `MANAGER_AGENT_SYSTEM_PROMPT`

**Критерії успіху:**
- ✅ Промпти створені

---

### Завдання 6.2: Реалізувати WorkoutManagerAgent

**Файл:** `apps/backend/app/agents/manager.py`

**Функціональність:**
- Створення workout
- Активація workout
- Використання workout tools

**Критерії успіху:**
- ✅ Agent створено
- ✅ Тести проходять

---

## 🎯 Фаза 7: Supervisor (День 9-10)

### Завдання 7.1: Створити ConversationOrchestrator

**Файл:** `apps/backend/app/agents/supervisor.py`

**Функціональність:**
- Координація всіх агентів
- Routing між агентами
- State management
- Error handling

**Критерії успіху:**
- ✅ Supervisor створено
- ✅ Координує всіх агентів
- ✅ Тести проходять

---

### Завдання 7.2: Інтегрувати Supervisor

**Зміни:**
- Оновити ConversationManager для використання Supervisor
- Додати feature flag
- Зберегти backward compatibility

**Критерії успіху:**
- ✅ Інтеграція завершена
- ✅ Можна перемикати між старим та новим
- ✅ Тести проходять

---

## 🎯 Фаза 8: Оптимізація та тестування (День 11-12)

### Завдання 8.1: Performance tuning

**Оптимізації:**
- Кешування
- Паралельні виклики
- Streaming (якщо потрібно)

**Критерії успіху:**
- ✅ Performance покращено
- ✅ Latency < 2s для простих запитів

---

### Завдання 8.2: Observability

**Додати:**
- LangSmith tracing (опціонально)
- Детальне логування
- Metrics

**Критерії успіху:**
- ✅ Логування працює
- ✅ Можна відстежувати виклики

---

### Завдання 8.3: Фінальне тестування

**Тести:**
- Integration tests
- End-to-end tests
- Performance tests
- Load tests

**Критерії успіху:**
- ✅ Всі тести проходять
- ✅ Покриття > 85%
- ✅ Performance прийнятний

---

## 📊 Чеклист міграції

### Фаза 1: Підготовка
- [ ] Встановити залежності
- [ ] Створити структуру директорій
- [ ] Створити базові класи

### Фаза 2: Tools
- [ ] Parser tools
- [ ] Database tools
- [ ] Spotify tools
- [ ] Workout tools

### Фаза 3: WorkoutParserAgent
- [ ] Створити промпти
- [ ] Реалізувати agent
- [ ] Інтегрувати в систему
- [ ] Тести

### Фаза 4: MusicCuratorAgent
- [ ] Створити промпти
- [ ] Реалізувати agent
- [ ] Інтегрувати в систему
- [ ] Тести

### Фаза 5: ConversationAgent
- [ ] Створити промпти
- [ ] Реалізувати agent
- [ ] Тести

### Фаза 6: WorkoutManagerAgent
- [ ] Створити промпти
- [ ] Реалізувати agent
- [ ] Тести

### Фаза 7: Supervisor
- [ ] Створити supervisor
- [ ] Інтегрувати в систему
- [ ] Тести

### Фаза 8: Оптимізація
- [ ] Performance tuning
- [ ] Observability
- [ ] Фінальне тестування

---

## 🔄 Backward Compatibility

**Стратегія:**
- Використовувати feature flags
- Паралельна робота старої та нової системи
- Поступовий перехід

**Feature Flags:**
```python
USE_LANGCHAIN_PARSER = os.getenv("USE_LANGCHAIN_PARSER", "false") == "true"
USE_LANGCHAIN_CURATOR = os.getenv("USE_LANGCHAIN_CURATOR", "false") == "true"
USE_LANGCHAIN_SUPERVISOR = os.getenv("USE_LANGCHAIN_SUPERVISOR", "false") == "true"
```

---

## 📝 Наступні кроки

1. **Зараз:** Почати з Фази 1 (Підготовка)
2. **Потім:** Фаза 2 (Tools)
3. **Потім:** Фаза 3 (WorkoutParserAgent)
4. **І так далі...**

---

## ✅ Критерії успіху міграції

1. ✅ Всі тести проходять
2. ✅ Backward compatibility збережено
3. ✅ Performance не погіршився
4. ✅ Код більш структурований
5. ✅ Легше додавати нові функції
6. ✅ Observability покращено

