# Prompt Optimization Recommendations

## 📊 Базовано на тестуванні та аналізі

**Дата**: 2025-11-18
**Версія промпту**: 2.0
**Статус**: Рекомендації для покращення

---

## 🎯 Поточний стан

### Що працює добре ✅:
1. **Context awareness** — агент не повторює питання
2. **Parameter extraction** — 100% точність на тестових даних
3. **Genre normalization** — коректна нормалізація до англійських назв
4. **Parameter accumulation** — параметри акумулюються між повідомленнями
5. **Edge cases handling** — 33/33 edge case тестів пройшли

### Що можна покращити 🔧:
1. **Verbosity** — агент може бути занадто багатослівним
2. **Confirmation flow** — іноді потрібно 2 підтвердження
3. **Ambiguity handling** — не завжди чітко обробляє неоднозначні відповіді
4. **Error recovery** — fallback responses можуть бути кращими

---

## 📝 Рекомендації для оптимізації

### 1. Скоротити відповіді агента

**Проблема**: Агент іноді дає занадто довгі відповіді

**Поточний промпт**:
```
- Keep responses SHORT (1-3 sentences max)
```

**Рекомендована зміна**:
```
- Keep responses VERY SHORT (1-2 sentences max, preferably 1)
- Use simple, direct language
- Avoid unnecessary elaboration
- Example: "Супер! 45 хвилин. Яка інтенсивність?" instead of "Супер! 45 хвилин — чудова тривалість для інтервального тренування. Яка буде інтенсивність?"
```

---

### 2. Покращити handling неоднозначних відповідей

**Проблема**: Коли користувач каже "так" без контексту

**Додати до промпту**:
```
## HANDLING AMBIGUOUS RESPONSES

If user says "так"/"yes"/"ok" without clear context:
1. Check what you last asked
2. If you asked for duration/intensity → politely clarify
3. If you asked for confirmation → proceed with creation
4. If unclear → ask specific question

Example:
User: "так"
Context: You asked "Яка інтенсивність?"
Response: "Я розумію, але мені потрібно знати інтенсивність — легка, середня чи висока?"
```

---

### 3. Оптимізувати confirmation flow

**Проблема**: Іноді потрібно 2 підтвердження

**Поточний flow**:
```
AI: "Створюємо воркаут?"
User: "так"
AI: "Добре! Створюю воркаут..."
```

**Рекомендована зміна**:
```
AI: "Створюємо воркаут?"
User: "так"
AI: [calls create_workout_from_params immediately]
AI: "✅ Готово! Воркаут створено."

CRITICAL: Do NOT ask for confirmation twice!
After user confirms, IMMEDIATELY call create_workout_from_params tool.
```

---

### 4. Покращити error recovery

**Додати до промпту**:
```
## ERROR RECOVERY

If tool call fails:
1. Apologize briefly
2. Explain what went wrong (if known)
3. Suggest next action
4. Keep positive tone

Example:
"Вибачте, виникла помилка при створенні воркауту. Спробуємо ще раз? Або хочеш змінити параметри?"
```

---

### 5. Додати examples для edge cases

**Додати до промпту**:
```
## EDGE CASES HANDLING

### User provides incomplete info:
User: "інтервальна"
AI: "Чудово! Інтервали. Скільки часу плануєш бігти і яка інтенсивність?"

### User provides conflicting info:
User: "легка інтенсивна пробіжка"
AI: "Хм, трохи незрозуміло — легка чи інтенсивна? Обери одне 😊"

### User asks question:
User: "скільки хвилин рекомендуєш?"
AI: "Для інтервального тренування зазвичай 30-45 хвилин. Що обираєш?"

### User changes mind:
User: "ні, краще 45 хвилин"
AI: "Добре! Змінюю на 45 хвилин. Яка буде інтенсивність?"
```

---

### 6. Покращити motivational tone

**Додати до промпту**:
```
## MOTIVATIONAL LANGUAGE

Use encouraging phrases naturally:
- "Чудовий вибір!" (Great choice!)
- "Звучить потужно!" (Sounds powerful!)
- "Це буде справжній виклик!" (This will be a real challenge!)
- "Ідеально для твоєї мети!" (Perfect for your goal!)

But keep it SHORT and natural. Don't overdo it.
```

---

### 7. Оптимізувати genre recognition

**Поточний стан**: Добре працює

**Рекомендація**: Додати більше варіацій

```python
# Додати до GENRE_MAPPING:
"electronic": [
    ...,
    "електроніка",
    "електро музика",
    "електронний",
    "edm music"
],
"rock": [
    ...,
    "рок музика",
    "рок-н-рол",
    "rock music",
    "rock'n'roll"
],
```

---

### 8. Додати handling для "не знаю"

**Додати до промпту**:
```
## HANDLING "НЕ ЗНАЮ" / "DON'T KNOW"

If user says they don't know:
1. Provide helpful suggestions
2. Give typical values
3. Ask if they want recommendations

Example:
User: "не знаю яку інтенсивність"
AI: "Без проблем! Для інтервалів зазвичай обирають середню або високу.
     Середня — якщо хочеш попрацювати, висока — якщо готовий до виклику. Що обираєш?"
```

---

### 9. Покращити multi-genre handling

**Поточний стан**: Працює, але можна краще

**Додати до промпту**:
```
## MULTI-GENRE HANDLING

When user mentions multiple genres:
1. Acknowledge ALL genres
2. Confirm you understood correctly
3. Ask if they want to add more or proceed

Example:
User: "рок поп джаз"
AI: "Супер! Rock, pop і jazz — різноманітний мікс! Це все, чи додамо ще щось?"
```

---

### 10. Додати timeout handling

**Додати до промпту**:
```
## TIMEOUT / LONG PAUSES

If conversation seems stuck or user takes long to respond:
- Stay patient
- Don't repeat the same question
- Offer help if needed

Note: This is handled by backend, but agent should be aware.
```

---

## 🧪 A/B Testing Recommendations

### Test 1: Response Length
- **Variant A**: Current (1-3 sentences)
- **Variant B**: Ultra-short (1 sentence only)
- **Metric**: User satisfaction, conversation completion rate

### Test 2: Confirmation Flow
- **Variant A**: Current (ask → confirm → create)
- **Variant B**: Direct (ask → create immediately)
- **Metric**: Time to workout creation, user confusion rate

### Test 3: Motivational Language
- **Variant A**: Current (moderate motivation)
- **Variant B**: High motivation (more emojis, enthusiastic)
- **Metric**: User engagement, return rate

---

## 📊 Metrics to Track

### Conversation Quality:
1. **Completion rate** — % conversations that result in workout creation
2. **Average messages** — fewer is better (target: 5-7 messages)
3. **Repetition rate** — % of repeated questions (target: 0%)
4. **Error rate** — % of conversations with errors (target: <5%)

### User Satisfaction:
1. **Response time** — time to get AI response (target: <2s)
2. **Clarity score** — user feedback on response clarity
3. **Helpfulness score** — user feedback on helpfulness

### Technical Performance:
1. **Tool call success rate** — % successful tool calls (target: >95%)
2. **Parameter extraction accuracy** — % correct extractions (target: >90%)
3. **API error rate** — % OpenAI API errors (target: <1%)

---

## 🔄 Implementation Plan

### Phase 1: Quick Wins (1-2 days)
- [ ] Shorten response length guideline
- [ ] Add edge case examples to prompt
- [ ] Improve error recovery messages
- [ ] Add "не знаю" handling

### Phase 2: Testing (1 week)
- [ ] A/B test response length
- [ ] A/B test confirmation flow
- [ ] Collect user feedback
- [ ] Analyze metrics

### Phase 3: Optimization (ongoing)
- [ ] Refine prompt based on data
- [ ] Add more genre variations
- [ ] Improve motivational language
- [ ] Optimize for specific user segments

---

## 📝 Prompt Version History

### v2.0 (Current - 2025-11-18)
- AI-driven parameter extraction через tools
- Context awareness rules
- Examples of good conversations
- Rules to avoid loops

### v2.1 (Planned)
- Shorter responses
- Better edge case handling
- Improved error recovery
- Multi-genre optimization

### v2.2 (Future)
- Personalization based on user patterns
- Adaptive language (formal/informal)
- Proactive suggestions
- Multi-language support

---

## 🎯 Success Criteria

Prompt вважається оптимізованим, якщо:

1. ✅ **Completion rate > 80%** — більшість діалогів завершуються успішно
2. ✅ **Average messages < 7** — швидкий шлях до створення workout
3. ✅ **Repetition rate = 0%** — жодних повторень питань
4. ✅ **User satisfaction > 4.0/5.0** — користувачі задоволені
5. ✅ **Parameter accuracy > 90%** — параметри витягуються коректно

---

## 💡 Additional Ideas

### Personalization:
- "Бачу, ти зазвичай бігаєш 45 хвилин. Сьогодні теж 45?"
- "Минулого разу тобі сподобався rock. Знову rock?"

### Proactive Suggestions:
- "Для інтервалів рекомендую electronic або techno — високий темп!"
- "Вчора ти зробив 5 км. Сьогодні спробуємо більше?"

### Contextual Help:
- Якщо користувач новачок → пояснити терміни
- Якщо досвідчений → пропускати пояснення

---

**Автор**: AI Assistant
**Дата**: 2025-11-18
**Статус**: Рекомендації готові до імплементації ✅

