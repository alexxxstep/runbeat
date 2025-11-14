# Діагностика проблем з LangChain генерацією варіантів плейлистів

## Проблема

Після міграції на LangChain перестали генеруватись варіанти плейлистів.

## Перевірка API ключа

### 1. Чи потрібен окремий API ключ для LangChain?

**Відповідь: НІ** - LangChain використовує той самий `OPENAI_API_KEY`, що й legacy код.

### 2. Як передається API ключ

LangChain отримує API ключ через `BaseAgent.__init__()`:

```python
# apps/backend/app/agents/base.py:30-34
self.llm = ChatOpenAI(
    model=model_name or settings.OPENAI_MODEL,
    temperature=temperature,
    api_key=settings.OPENAI_API_KEY,  # ← Той самий ключ
    max_tokens=max_tokens,
)
```

### 3. Перевірка налаштувань

**На production (Railway) переконайтеся, що встановлено:**

```bash
OPENAI_API_KEY=sk-proj-ваш_ключ  # Той самий ключ, що використовувався раніше
OPENAI_MODEL=gpt-4  # або gpt-4-turbo-preview
USE_LANGCHAIN_CURATOR=true  # або 1
```

## Можливі причини проблеми

### 1. API ключ не встановлений або невірний

**Симптоми:**
- Помилки типу "Invalid API key" в логах
- Agent не ініціалізується

**Рішення:**
```bash
# Перевірте в Railway Variables
echo $OPENAI_API_KEY  # Має починатися з sk-proj- або sk-
```

### 2. Timeout або iteration limit

**Симптоми:**
- Генерація починається, але не завершується
- Помилки "iteration limit" або "execution time" в логах

**Налаштування в коді:**
```python
# apps/backend/app/agents/curator.py:78-86
self.agent_executor = AgentExecutor(
    agent=self.agent,
    tools=self.tools,
    memory=self.memory,
    verbose=False,
    handle_parsing_errors=True,
    max_iterations=8,  # Максимум 8 ітерацій
    max_execution_time=45,  # 45 секунд максимум
)
```

**Можливе рішення:** Збільшити `max_iterations` або `max_execution_time`.

### 3. Помилки в agent execution

**Симптоми:**
- Agent виконується, але повертає помилки
- Fallback на legacy метод

**Перевірка логів:**
Шукайте в логах:
- `"Error generating playlist:"`
- `"Agent reached iteration/time limit"`
- `"OpenAI rate limit reached"`

### 4. Проблеми з паралельною генерацією

**Симптоми:**
- Variant 1 генерується, але Variant 2 падає
- Помилки при використанні `asyncio.gather()`

**Рішення:** Перевірте, чи правильно обробляються винятки в паралельній генерації.

## Діагностичні кроки

### Крок 1: Перевірте логи

Шукайте в логах Railway:

```bash
# Успішна ініціалізація
"MusicCuratorAgent initialized with LangChain"
"PlaylistGenerator: Using LangChain MusicCuratorAgent"

# Помилки
"Error generating playlist:"
"Failed to generate variant"
"Agent reached iteration/time limit"
```

### Крок 2: Перевірте environment variables

В Railway Dashboard → Variables:

```
✅ OPENAI_API_KEY - має бути встановлений
✅ OPENAI_MODEL - має бути gpt-4 або gpt-4-turbo-preview
✅ USE_LANGCHAIN_CURATOR - має бути true або 1
```

### Крок 3: Перевірте fallback

Якщо LangChain не працює, код має автоматично перейти на legacy метод:

```python
# apps/backend/app/services/playlist_generator.py:273-275
except Exception as e:
    logger.error(f"MusicCuratorAgent failed, falling back to legacy: {e}")
    # Fall through to legacy generation
```

**Якщо fallback не спрацьовує:**
- Перевірте, чи не викидається виняток раніше
- Перевірте, чи legacy метод все ще працює

### Крок 4: Тестування локально

```bash
cd apps/backend
python -c "
from app.core.config import settings
print(f'OPENAI_API_KEY: {settings.OPENAI_API_KEY[:10]}...')
print(f'OPENAI_MODEL: {settings.OPENAI_MODEL}')
print(f'USE_LANGCHAIN_CURATOR: {settings.USE_LANGCHAIN_CURATOR}')

from app.agents.curator import MusicCuratorAgent
agent = MusicCuratorAgent()
print('MusicCuratorAgent initialized successfully')
"
```

## Рішення проблем

### Рішення 1: Вимкнути LangChain тимчасово

Якщо потрібно швидко відновити роботу:

```bash
# В Railway Variables
USE_LANGCHAIN_CURATOR=false
```

Або в `.env`:
```
USE_LANGCHAIN_CURATOR=False
```

### Рішення 2: Збільшити timeout/iterations

Якщо проблема в timeout:

```python
# apps/backend/app/agents/curator.py:84-85
max_iterations=12,  # Збільшити з 8 до 12
max_execution_time=60,  # Збільшити з 45 до 60 секунд
```

### Рішення 3: Додати більше логування

Додайте детальне логування для діагностики:

```python
# В apps/backend/app/agents/curator.py:110
async def generate_playlist(...):
    try:
        logger.info(f"Starting playlist generation with LangChain...")
        logger.debug(f"Workout intent: {workout_intent}")
        # ... existing code ...
    except Exception as e:
        logger.error(f"Error generating playlist: {e}", exc_info=True)
        # ... existing code ...
```

## Перевірка роботи

### Тест 1: Перевірка ініціалізації

```python
from app.services.playlist_generator import PlaylistGenerator
from app.services.spotify_service import SpotifyService

spotify = SpotifyService()
generator = PlaylistGenerator(spotify)

print(f"Using LangChain: {generator.use_langchain_curator}")
print(f"Curator agent: {generator.curator_agent}")
```

### Тест 2: Тест генерації

```python
from app.models.workout import Workout

workout = Workout(
    type="steady",
    duration_minutes=30,
    intensity="moderate",
    hr_zones=[130, 150]
)

result = await generator.generate(
    workout=workout,
    user_preferences={"top_genres": ["pop"]}
)

print(f"Generated {result.total_tracks} tracks")
```

## Висновок

**Відповідь на питання:** НІ, додатковий API ключ не потрібен. LangChain використовує той самий `OPENAI_API_KEY`, що й legacy код.

**Найчастіші проблеми:**
1. API ключ не встановлений або невірний
2. Timeout/iteration limits занадто малі
3. Помилки в agent execution (перевірте логи)

**Рекомендації:**
1. Перевірте логи на production
2. Переконайтеся, що `OPENAI_API_KEY` встановлений в Railway
3. Якщо проблема критична, тимчасово вимкніть LangChain (`USE_LANGCHAIN_CURATOR=false`)

