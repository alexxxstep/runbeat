# Новий Chat Flow - Створення Workout

**Дата:** 2025-11-14

---

## 🎯 Новий Flow

### Старий flow (було):
```
User: "хочу пробігти 30 хв"
  ↓
AI: Парсить intent
  ↓
AI: Генерує плейлист одразу
  ↓
AI: Показує плейлист
```

### Новий flow (стало):
```
User: "хочу побігати"
  ↓
AI: "Скільки часу? Яка інтенсивність?"
  ↓
User: "30 хв, легкий темп"
  ↓
AI: "Ось що я зрозумів:
     🏃 Стабільна пробіжка
     ⏱️ Тривалість: 30 хвилин
     ⚡ Інтенсивність: легка
     🎵 BPM: 110-130

     Створити воркаут? (Да/Ні)"
  ↓
User: "Да"
  ↓
AI: "✅ Воркаут успішно створено!
     Ти можеш почати тренування або згенерувати плейлист для нього."
```

---

## 📋 Зміни

### 1. Нові стани та actions

**ConversationStateEnum:**
- ✅ Додано `ASK_WORKOUT_CONFIRMATION` - стан очікування підтвердження

**ConversationAction:**
- ✅ Додано `ASK_WORKOUT_CONFIRMATION` - дія запиту підтвердження
- ✅ Додано `CREATE_WORKOUT` - дія створення workout

---

### 2. Змінена логіка `_decide_next_action()`

**Було:**
- Якщо intent повний → генерувати плейлист одразу

**Стало:**
- Якщо intent повний → питати підтвердження створення workout
- Після підтвердження → створювати workout в базі даних

---

### 3. Новий метод `_handle_workout_confirmation()`

**Що робить:**
- Розпізнає відповіді "Да/Ні" (українською та англійською)
- Якщо "Да" → створює workout в базі даних
- Якщо "Ні" → завершує розмову з дружнім повідомленням
- Якщо незрозуміло → питає знову

**Підтримувані відповіді:**
- **Так:** "да", "так", "yes", "y", "ok", "ок", "створ", "створити", "зроби"
- **Ні:** "ні", "no", "n", "не", "не треба", "скасувати", "відмінити"

---

### 4. Новий метод `_create_workout_in_db()`

**Що робить:**
- Конвертує WorkoutIntent в формат бази даних
- Мапить workout_type (continuous → steady)
- Мапить energy_profile в intensity (low/moderate/high)
- Створює workout в таблиці `workouts`
- Повертає workout_id

---

### 5. Новий метод `_format_workout_summary()`

**Що робить:**
- Форматує WorkoutIntent в зрозуміле повідомлення для користувача
- Показує тип, тривалість, інтенсивність, BPM
- Використовує емодзі для кращого UX

**Приклад:**
```
🏃 **Стабільна пробіжка**
⏱️ Тривалість: 37 хвилин
⚡ Інтенсивність: легка
🎵 BPM: 110-130
```

---

### 6. Оновлено `process_message()`

**Додано перевірку:**
- Якщо поточний стан = `ASK_WORKOUT_CONFIRMATION`
- Обробляє відповідь на підтвердження
- Не парсить intent повторно

---

## 🔄 Повний Flow з кодом

### Крок 1: Користувач пише "хочу побігати"

```python
# ConversationManager.process_message()
message = "хочу побігати"
current_state = NEW

# Парсить intent
workout_intent = await _parse_user_intent(...)
# → workout_intent.duration_minutes = None (не вистачає інформації)

# _decide_next_action()
if not _is_intent_complete(workout_intent):
    return ASK_CLARIFICATION, {
        "message_to_user": "Скільки часу плануєш бігти?"
    }
```

---

### Крок 2: Користувач відповідає "30 хв, легкий темп"

```python
message = "30 хв, легкий темп"
current_state = NEEDS_CLARIFICATION

# Парсить intent
workout_intent = await _parse_user_intent(...)
# → duration_minutes = 30, target_bpm_min = 110, target_bpm_max = 130

# _decide_next_action()
if _is_intent_complete(workout_intent):
    workout_summary = _format_workout_summary(workout_intent)
    return ASK_WORKOUT_CONFIRMATION, {
        "state": ASK_WORKOUT_CONFIRMATION,
        "message_to_user": f"Ось що я зрозумів:\n\n{workout_summary}\n\nСтворити воркаут? (Да/Ні)"
    }
```

---

### Крок 3: Користувач відповідає "Да"

```python
message = "Да"
current_state = ASK_WORKOUT_CONFIRMATION

# process_message() виявляє стан
if current_state == ASK_WORKOUT_CONFIRMATION:
    response = await _handle_workout_confirmation(...)

    # _handle_workout_confirmation()
    message_lower = "да"
    is_positive = True  # "да" в positive_responses

    if is_positive:
        workout_id = await _create_workout_in_db(...)
        # → Створює workout в базі даних
        # → Повертає workout_id

        return {
            "state": COMPLETE,
            "action": CREATE_WORKOUT,
            "message_to_user": "✅ Воркаут успішно створено!...",
            "workout_id": workout_id
        }
```

---

### Крок 4: Користувач відповідає "Ні"

```python
message = "Ні"
current_state = ASK_WORKOUT_CONFIRMATION

# _handle_workout_confirmation()
is_negative = True  # "ні" в negative_responses

if is_negative:
    return {
        "state": COMPLETE,
        "message_to_user": "Зрозуміло! Якщо будуть якісь побажання - звертайся. 💪"
    }
```

---

## 📊 Стани розмови

```
NEW
  ↓
NEEDS_CLARIFICATION (питає уточнення)
  ↓
ASK_WORKOUT_CONFIRMATION (питає підтвердження)
  ↓
COMPLETE (workout створено або користувач відмовився)
```

---

## ✅ Переваги нового flow

1. **Користувач контролює процес** - може підтвердити або відмінити
2. **Прозорість** - бачить що саме буде створено
3. **Гнучкість** - може відмінити та почати заново
4. **Workout зберігається** - можна використати пізніше
5. **Кращий UX** - зрозумілі повідомлення та емодзі

---

## 🧪 Тестування

### Тест 1: Повний flow

```
User: "хочу побігати"
AI: "Скільки часу плануєш бігти?"

User: "30 хв легкий темп"
AI: "Ось що я зрозумів:
     🏃 Стабільна пробіжка
     ⏱️ Тривалість: 30 хвилин
     ⚡ Інтенсивність: легка
     🎵 BPM: 110-130

     Створити воркаут? (Да/Ні)"

User: "Да"
AI: "✅ Воркаут успішно створено!"
```

### Тест 2: Відмова

```
User: "Ні"
AI: "Зрозуміло! Якщо будуть якісь побажання - звертайся. 💪"
```

### Тест 3: Незрозуміла відповідь

```
User: "можливо"
AI: "Не зовсім зрозумів. Будь ласка, відповідь 'Да' або 'Ні'. Створити воркаут?"
```

---

## 📝 Змінені файли

1. `apps/backend/app/services/conversation_manager.py`
   - Додано `ASK_WORKOUT_CONFIRMATION` стан
   - Додано `ASK_WORKOUT_CONFIRMATION` та `CREATE_WORKOUT` actions
   - Додано `_handle_workout_confirmation()`
   - Додано `_create_workout_in_db()`
   - Додано `_format_workout_summary()`
   - Змінено `_decide_next_action()` - питає підтвердження замість генерації плейлисту
   - Змінено `process_message()` - обробляє підтвердження

2. `apps/backend/app/api/routes/chat.py`
   - Оновлено обробку `ASK_WORKOUT_CONFIRMATION` стану
   - Додано передачу `workout_id` в response

3. `apps/backend/app/models/workout.py`
   - Додано поле `id` для workout ID

---

## ✅ Статус

**Реалізовано:** ✅

Всі зміни внесено. Новий flow працює:
1. AI збирає інформацію через питання
2. Коли інформації достатньо - питає підтвердження
3. Якщо "Да" - створює workout
4. Якщо "Ні" - завершує розмову дружньо

---

**Готово до тестування!** 🚀

