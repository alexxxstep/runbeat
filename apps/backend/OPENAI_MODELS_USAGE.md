# Використання моделей OpenAI в проекті RunBeat

## Огляд

Проект використовує одну модель OpenAI для всіх компонентів, яка налаштовується через змінну середовища `OPENAI_MODEL`.

## Модель за замовчуванням

**Модель**: `gpt-4`
**Конфігурація**: `apps/backend/app/core/config.py:27`

```python
OPENAI_MODEL: str = "gpt-4"
```

## Де використовується

### 1. LangChain Agents (через BaseAgent)

**Файл**: `apps/backend/app/agents/base.py:30-35`

Всі LangChain агенти використовують `ChatOpenAI` з моделлю з налаштувань:

```python
self.llm = ChatOpenAI(
    model=model_name or settings.OPENAI_MODEL,  # ← gpt-4 за замовчуванням
    temperature=temperature,
    api_key=settings.OPENAI_API_KEY,
    max_tokens=max_tokens,
)
```

**Агенти, що використовують цю модель**:
- `WorkoutParserAgent` - парсинг воркаутів з повідомлень
- `MusicCuratorAgent` - генерація плейлистів
- `ConversationAgent` - обробка загальних питань
- `ConversationOrchestrator` (Supervisor) - координація агентів

### 2. Legacy LLMService

**Файл**: `apps/backend/app/services/llm_service.py:82, 157`

Legacy сервіс використовує `AsyncOpenAI` з structured outputs:

```python
# Для парсингу воркаутів
response = await self.client.beta.chat.completions.parse(
    model=settings.OPENAI_MODEL,  # ← gpt-4
    messages=messages,
    response_format=WorkoutIntent,
    **model_params,
)

# Для генерації плейлистів
response = await self.client.beta.chat.completions.parse(
    model=settings.OPENAI_MODEL,  # ← gpt-4
    messages=messages,
    response_format=PlaylistResponse,
    temperature=0.7,
    max_tokens=3000,
)
```

## Налаштування температури

### LangChain Agents

- **WorkoutParserAgent**: `temperature=0.3` (низька для точного парсингу)
- **MusicCuratorAgent**: `temperature=0.7` (вища для креативності при генерації плейлистів)
- **ConversationAgent**: `temperature=0.7` (вища для природної розмови)
- **ConversationOrchestrator**: Використовує температури під-агентів

### Legacy LLMService

- **Парсинг воркаутів**: `temperature=0.3` (з PromptBuilder)
- **Генерація плейлистів**: `temperature=0.7` (вища для креативності)

## Підтримувані моделі

Згідно з документацією, проект підтримує:

1. **`gpt-4`** (за замовчуванням)
   - Найкраща якість
   - Найвища вартість (~$0.03/1K токенів вхідні, ~$0.06/1K токенів вихідні)

2. **`gpt-4-turbo-preview`** (альтернатива)
   - Швидше та дешевше ніж gpt-4
   - Можна використовувати для production

3. **`gpt-3.5-turbo`** (для тестування)
   - Найдешевше
   - Менша якість, але достатня для тестування

## Як змінити модель

### Локально (.env файл)

**Варіант 1: Одна модель для всіх агентів**
```env
OPENAI_MODEL=gpt-4-turbo-preview
```

**Варіант 2: Різні моделі для різних агентів**
```env
OPENAI_MODEL=gpt-4  # Fallback для всіх агентів
OPENAI_MODEL_PARSER=gpt-4  # Для WorkoutParserAgent
OPENAI_MODEL_CURATOR=gpt-4-turbo-preview  # Для MusicCuratorAgent (швидше)
OPENAI_MODEL_CONVERSATION=gpt-3.5-turbo  # Для ConversationAgent (дешевше)
OPENAI_MODEL_SUPERVISOR=gpt-4  # Для ConversationOrchestrator
```

### На production (Railway)

Встановіть змінні середовища в Railway Dashboard → Variables:

```
OPENAI_MODEL=gpt-4-turbo-preview
# Або окремо для кожного агента:
OPENAI_MODEL_PARSER=gpt-4
OPENAI_MODEL_CURATOR=gpt-4-turbo-preview
OPENAI_MODEL_CONVERSATION=gpt-3.5-turbo
```

### Програмно (для окремих агентів)

Можна передати іншу модель при ініціалізації агента:

```python
# В BaseAgent можна передати model_name
agent = WorkoutParserAgent()
# Але зараз це не використовується - агенти автоматично використовують
# відповідну модель з settings (OPENAI_MODEL_PARSER, OPENAI_MODEL_CURATOR, тощо)
# або fallback на OPENAI_MODEL
```

## Використання в різних компонентах

### 1. Парсинг воркаутів

**LangChain**: `WorkoutParserAgent` → `BaseAgent.llm` → `ChatOpenAI(model=settings.OPENAI_MODEL)`
**Legacy**: `LLMService.parse_workout()` → `AsyncOpenAI.beta.chat.completions.parse(model=settings.OPENAI_MODEL)`

### 2. Генерація плейлистів

**LangChain**: `MusicCuratorAgent` → `BaseAgent.llm` → `ChatOpenAI(model=settings.OPENAI_MODEL)`
**Legacy**: `LLMService.generate_playlist()` → `AsyncOpenAI.beta.chat.completions.parse(model=settings.OPENAI_MODEL)`

### 3. Розмова

**LangChain**: `ConversationAgent` → `BaseAgent.llm` → `ChatOpenAI(model=settings.OPENAI_MODEL)`
**Supervisor**: `ConversationOrchestrator` → `BaseAgent.llm` → `ChatOpenAI(model=settings.OPENAI_MODEL)`

## Вартість використання

### GPT-4
- Вхідні токени: ~$0.03 за 1K токенів
- Вихідні токени: ~$0.06 за 1K токенів
- **Рекомендовано**: $5-10 для тестування

### GPT-4 Turbo
- Дешевше ніж GPT-4
- Швидше обробка

### GPT-3.5 Turbo
- Найдешевше
- ~$0.0015 за 1K токенів (вхідні)
- ~$0.002 за 1K токенів (вихідні)

## Рекомендації

1. **Development**: Використовуйте `gpt-4` для найкращої якості
2. **Testing**: Можна використовувати `gpt-3.5-turbo` для економії
3. **Production**: Рекомендовано `gpt-4` або `gpt-4-turbo-preview` залежно від бюджету

## Перевірка поточної моделі

```python
from app.core.config import settings
print(f"Current OpenAI model: {settings.OPENAI_MODEL}")
```

## Висновок

Проект використовує **одну модель OpenAI** (`gpt-4` за замовчуванням) для всіх компонентів:
- ✅ LangChain агенти (через BaseAgent)
- ✅ Legacy LLMService
- ✅ Structured outputs для парсингу та генерації

Модель налаштовується через змінну середовища `OPENAI_MODEL` і може бути змінена на `gpt-4-turbo-preview` або `gpt-3.5-turbo` за потреби.

