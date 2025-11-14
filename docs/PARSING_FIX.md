# Виправлення проблеми з парсингом тренувань

**Дата:** 2025-11-14
**Проблема:** AI повторював питання про уточнення, навіть коли користувач надав достатньо інформації

---

## 🐛 Проблема

Користувач писав:
1. "хочу пробігти 37 хв під легку мотивуючу музику"
2. "37 хв в легкому темпі"

AI обидва рази відповідав: "Не зовсім зрозумів. Опиши тренування детальніше: скільки часу і яка інтенсівність?"

---

## ✅ Виправлення

### 1. Додано приклади для української мови

**Файл:** `apps/backend/app/services/prompts/prompt_builder.py`

Додано приклади:
- "37 хв в легкому темпі" → complete intent
- "Хочу пробігти 37 хв під легку мотивуючу музику" → complete intent

### 2. Покращено інструкції для розпізнавання інтенсивності

Додано чітке маппінг:
- "легкий", "легкому", "easy", "recovery", "відновлення" → low intensity → Zone 1-2 (110-130 BPM)
- "темповий", "tempo", "помірний", "moderate" → moderate intensity → Zone 2-3 (130-160 BPM)
- "швидкий", "fast", "інтервали", "intervals", "висока" → high intensity → Zone 4-5 (160-180 BPM)

### 3. Покращено логіку перевірки completeness

**Файл:** `apps/backend/app/services/conversation_manager.py`

**Зміни:**
- Якщо intent має всі необхідні поля, ігноруємо `needs_clarification` flag
- Знижено confidence threshold з 0.7 до 0.6
- Додано логіку: якщо всі поля присутні, приймаємо навіть з confidence 0.6-0.7

### 4. Покращено Task instruction

Додано важливе правило:
> "IMPORTANT: If the user provides duration AND intensity/pace information,
> the intent is COMPLETE and you should set needs_clarification=false with high confidence (0.9+)."

---

## 📝 Змінені файли

1. `apps/backend/app/services/prompts/prompt_builder.py`
   - Додано приклади українською
   - Покращено інструкції для розпізнавання інтенсивності
   - Додано важливе правило про completeness

2. `apps/backend/app/services/conversation_manager.py`
   - Покращено логіку `_decide_next_action()` - ігнорує `needs_clarification` якщо intent повний
   - Знижено confidence threshold до 0.6
   - Додано логіку для moderate confidence

---

## 🧪 Очікуваний результат

Тепер коли користувач пише:
- "37 хв в легкому темпі" → AI розпізнає як complete intent і згенерує плейлист
- "Хочу пробігти 37 хв під легку мотивуючу музику" → AI розпізнає як complete intent

---

## ✅ Статус

Виправлено ✅

