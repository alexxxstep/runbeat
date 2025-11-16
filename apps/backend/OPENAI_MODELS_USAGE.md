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
- Parser tools - парсинг даних з повідомлень
- `WorkoutBuilder` (ConversationAgent) - розмова та створення воркаутів
- `SupervisorAgent` - координація потоку розмови

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

- **Parser tools**: `temperature=0.3` (низька для точного парсингу)
- **WorkoutBuilder**: `temperature=0.7` (вища для природної розмови)
- **SupervisorAgent**: Використовує WorkoutBuilder та інші компоненти

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
OPENAI_MODEL_PARSER=gpt-4  # Для parser tools
OPENAI_MODEL_CONVERSATION=gpt-3.5-turbo  # Для WorkoutBuilder (дешевше)
OPENAI_MODEL_SUPERVISOR=gpt-4  # Для SupervisorAgent
```

### На production (Railway)

Встановіть змінні середовища в Railway Dashboard → Variables:

```
OPENAI_MODEL=gpt-4-turbo-preview
# Або окремо для кожного агента:
OPENAI_MODEL_PARSER=gpt-4
OPENAI_MODEL_CONVERSATION=gpt-3.5-turbo
```

### Програмно (для окремих агентів)

Можна передати іншу модель при ініціалізації агента:

```python
# В BaseAgent можна передати model_name
agent = WorkoutParserAgent()
# Але зараз це не використовується - агенти автоматично використовують
# відповідну модель з settings (OPENAI_MODEL_PARSER, OPENAI_MODEL_CONVERSATION, тощо)
# або fallback на OPENAI_MODEL
```

## Використання в різних компонентах

### 1. Парсинг даних

**Parser tools** → `BaseAgent.llm` → `ChatOpenAI(model=settings.OPENAI_MODEL_PARSER or settings.OPENAI_MODEL)`

### 2. Генерація плейлистів

**PlaylistGenerator** → використовує Spotify API напряму (без OpenAI)

### 3. Розмова та створення воркаутів

**WorkoutBuilder** → `BaseAgent.llm` → `ChatOpenAI(model=settings.OPENAI_MODEL_CONVERSATION or settings.OPENAI_MODEL)`
**SupervisorAgent** → `BaseAgent.llm` → `ChatOpenAI(model=settings.OPENAI_MODEL_SUPERVISOR or settings.OPENAI_MODEL)`

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

