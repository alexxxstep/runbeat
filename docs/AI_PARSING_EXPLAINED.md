# Як AI розуміє повідомлення користувача

**Дата:** 2025-11-14

---

## ✅ Так, асистент використовує AI!

Асистент використовує **OpenAI GPT-4** для розуміння та парсингу повідомлень користувача.

---

## 🔄 Повний Flow

```
User: "хочу побігати"
    ↓
Chat API (/api/v1/chat/message)
    ↓
ConversationManager.process_message()
    ↓
ConversationManager._parse_user_intent()
    ↓
LLMService.parse_workout()
    ↓
PromptBuilder.build_messages()
    ├─ System Prompt: WORKOUT_EXPERT_SYSTEM (знання про тренування)
    └─ User Prompt: Conversation history + User message + Examples
    ↓
OpenAI GPT-4 API
    ├─ Model: gpt-4
    ├─ Structured Output: WorkoutIntent (Pydantic model)
    └─ Temperature: 0.3 (низька для точності)
    ↓
WorkoutIntent {
  workout_type: "continuous",
  duration_minutes: 30,
  target_bpm_min: 120,
  target_bpm_max: 140,
  confidence: 0.8,
  needs_clarification: true,
  clarification_question: "Скільки часу плануєш бігти?"
}
    ↓
ConversationManager._decide_next_action()
    ↓
Response: "Скільки часу плануєш бігти?"
```

---

## 🧠 Як працює AI парсинг

### 1. PromptBuilder будує промпт

**System Prompt:**

```
You are RunBeat AI, an expert assistant for runners...

## Workout Expertise

You are an expert running coach...
[весь WORKOUT_EXPERT_SYSTEM з:
 - Heart rate zones
 - Interval training principles
 - Workout types
 - BPM mapping
 - Examples]
```

**User Prompt:**

```
## Conversation History
User: хочу побігати

## Task
Parse the user's workout request into structured JSON format...

User message: "30 хв легкий темп"

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
2. Map intensity keywords:
   - "легкий", "легкому" → low intensity → Zone 1-2 (110-130 BPM)
   ...
```

---

### 2. OpenAI GPT-4 обробляє промпт

**Використовується:**

- **Model:** GPT-4 (з `settings.OPENAI_MODEL`)
- **Structured Output:** `WorkoutIntent` (Pydantic model)
- **Temperature:** 0.3 (низька для точності парсингу)
- **Max Tokens:** 500

**OpenAI автоматично:**

- Розуміє контекст розмови
- Розпізнає ключові слова ("легкий", "30 хв")
- Мапить їх на структуровані поля
- Повертає валідний JSON відповідно до Pydantic схеми

---

### 3. Результат парсингу

**WorkoutIntent (Pydantic модель):**

```python
WorkoutIntent(
    workout_type="continuous",
    duration_minutes=30,
    target_bpm_min=110,
    target_bpm_max=130,
    energy_profile="steady",
    confidence=0.95,
    needs_clarification=False,
    clarification_question=None
)
```

---

## 📝 Приклади як AI розуміє

### Приклад 1: "хочу побігати"

**AI розуміє:**

- Це запит на тренування
- Але не вистачає деталей (тривалість, інтенсивність)
- Встановлює `needs_clarification=True`
- Генерує питання: "Скільки часу плануєш бігти?"

**WorkoutIntent:**

```python
{
  "workout_type": "continuous",  # За замовчуванням
  "duration_minutes": 30,  # Припущення
  "target_bpm_min": 120,
  "target_bpm_max": 140,
  "confidence": 0.4,  # Низька впевненість
  "needs_clarification": True,
  "clarification_question": "Скільки часу плануєш бігти?"
}
```

---

### Приклад 2: "37 хв в легкому темпі"

**AI розуміє:**

- Тривалість: 37 хвилин
- Інтенсивність: "легкий темп" → low intensity
- BPM: 110-130 (для легкого темпу)
- Тип: steady (стабільна пробіжка)
- Всі дані є → `needs_clarification=False`

**WorkoutIntent:**

```python
{
  "workout_type": "continuous",
  "duration_minutes": 37,
  "target_bpm_min": 110,
  "target_bpm_max": 130,
  "energy_profile": "steady",
  "confidence": 0.95,  # Висока впевненість
  "needs_clarification": False
}
```

---

### Приклад 3: "інтенсивне тренування, 55 хвилин"

**AI розуміє:**

- Тривалість: 55 хвилин
- Інтенсивність: "інтенсивне" → high intensity
- BPM: 160-180 (для високої інтенсивності)
- Тип: intervals або progressive

**WorkoutIntent:**

```python
{
  "workout_type": "intervals",  # Або "progressive"
  "duration_minutes": 55,
  "target_bpm_min": 160,
  "target_bpm_max": 180,
  "energy_profile": "building",
  "confidence": 0.85,
  "needs_clarification": False  # Або True якщо потрібні деталі інтервалів
}
```

---

## 🎯 Що дає AI

### 1. Розуміння природної мови

AI розуміє:

- "хочу побігати" = запит на тренування
- "легкий темп" = low intensity
- "інтенсивне" = high intensity
- "30 хв" = duration_minutes: 30

### 2. Контекст розмови

AI пам'ятає попередні повідомлення:

```
User: "хочу побігати"
AI: "Скільки часу?"
User: "30 хв"  ← AI розуміє що це відповідь на попереднє питання
```

### 3. Інтелектуальні припущення

AI може:

- Припустити тривалість за типом тренування
- Визначити BPM за інтенсивністю
- Зрозуміти синоніми ("легкий" = "easy" = "recovery")

### 4. Структуровані виходи

AI повертає структурований об'єкт:

- Валідація через Pydantic
- Типобезпека
- Гарантована структура

---

## 🔍 Детальний розбір коду

### ConversationManager.\_parse_user_intent()

```python
async def _parse_user_intent(self, message, conversation_history, ...):
    # 1. Будує conversation history для LLM
    llm_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in conversation_history[:-1]
    ]

    # 2. Створює UserContext та ConversationState
    user_context = UserContext(language="uk")
    conversation_state = ConversationState(messages=llm_history)

    # 3. Викликає LLMService для парсингу
    intent = await self.llm_service.parse_workout(
        user_message=message,
        user_context=user_context,
        conversation_state=conversation_state,
    )

    return intent  # WorkoutIntent об'єкт
```

---

### LLMService.parse_workout()

```python
async def parse_workout(self, user_message, user_context, conversation_state):
    # 1. Будує промпти через PromptBuilder
    messages = self.prompt_builder.build_messages(
        user_message=user_message,
        user_context=user_context,
        conversation_state=conversation_state,
        task="parse_workout",
    )
    # → [
    #   {"role": "system", "content": "You are RunBeat AI..."},
    #   {"role": "user", "content": "## Task\n...\nUser message: \"30 хв\""}
    # ]

    # 2. Відправляє в OpenAI з structured output
    response = await self.client.beta.chat.completions.parse(
        model="gpt-4",
        messages=messages,
        response_format=WorkoutIntent,  # Pydantic модель
        temperature=0.3,
        max_tokens=500,
    )

    # 3. Отримує вже валідований WorkoutIntent
    parsed = response.choices[0].message.parsed
    return parsed  # WorkoutIntent об'єкт
```

---

## 🎨 Структуровані виходи (Structured Outputs)

**Що це:**
OpenAI GPT-4 може повертати дані у форматі Pydantic моделі.

**Переваги:**

- ✅ Автоматична валідація
- ✅ Типобезпека
- ✅ Гарантована структура
- ✅ Немає потрібності парсити JSON вручну

**Приклад:**

```python
# OpenAI автоматично повертає WorkoutIntent об'єкт
intent = await llm_service.parse_workout("30 хв легкий темп")

# Вже валідований та типізований
print(intent.duration_minutes)  # 30
print(intent.target_bpm_min)    # 110
```

---

## 📊 Що AI знає (з WORKOUT_EXPERT_SYSTEM)

AI має знання про:

1. **Heart Rate Zones:**

   - Zone 1 (Recovery): 50-60% HRmax → 100-120 BPM
   - Zone 2 (Aerobic): 60-70% HRmax → 120-140 BPM
   - Zone 3 (Tempo): 70-80% HRmax → 140-160 BPM
   - Zone 4 (Threshold): 80-90% HRmax → 160-175 BPM
   - Zone 5 (VO2max): 90-100% HRmax → 175-180+ BPM

2. **Workout Types:**

   - Steady (стабільна)
   - Progressive (прогресивна)
   - Intervals (інтервали)
   - Fartlek (фартлек)

3. **Intensity Mapping:**

   - "легкий", "easy" → low → Zone 1-2
   - "темповий", "tempo" → moderate → Zone 2-3
   - "інтенсивне", "hard" → high → Zone 4-5

4. **Examples:**
   - "Easy 30 minute run" → Steady, 30min, low, Zone 1-2
   - "5x 1km intervals" → Intervals, ~30min, high, Zone 4-5

---

## ✅ Висновок

**Так, асистент використовує AI (OpenAI GPT-4) для розуміння повідомлень!**

**Як це працює:**

1. Користувач пише повідомлення
2. PromptBuilder будує промпт з контекстом та знаннями
3. OpenAI GPT-4 парсить повідомлення
4. Повертає структурований WorkoutIntent
5. ConversationManager використовує intent для прийняття рішень

**Переваги:**

- ✅ Розуміє природну мову
- ✅ Пам'ятає контекст розмови
- ✅ Робить інтелектуальні припущення
- ✅ Повертає структуровані дані

---

**Статус:** ✅ AI інтегровано та працює
