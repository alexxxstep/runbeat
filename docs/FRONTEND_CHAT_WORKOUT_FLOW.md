# Frontend Chat Workout Flow - Документація

**Дата:** 2025-11-14

---

## 🔄 Поточний Flow створення workout з чату

### 1. Користувач пише повідомлення
```
Користувач: "хочу побігати 30 хв"
```

### 2. Frontend відправляє запит
```typescript
const response = await api.sendMessage({
  message: "хочу побігати 30 хв",
  user_id: userId,
  conversation_id: conversationId
});
```

### 3. Backend обробляє та повертає
```json
{
  "message": "Створити воркаут? (Да/Ні)",
  "workout": {
    "type": "continuous",
    "duration_minutes": 30,
    "intensity": "low",
    "hr_zones": [110, 130]
  },
  "needs_clarification": false,
  "is_complete": true,
  "conversation_id": "..."
}
```

**Статус:** `ASK_WORKOUT_CONFIRMATION` (внутрішній стан backend)

### 4. Frontend обробляє відповідь

**useChat.ts:**
- Додає AI повідомлення з workout інформацією
- Повертає `workout` об'єкт (без `id`, бо ще не створено)

**ChatPage.tsx:**
- Перевіряє: `workout && !workout.needs_clarification`
- Встановлює `activeWorkout = workout`
- Встановлює `activeWorkoutId = null` (ще не створено)
- Показує кнопки "Так/Ні"

### 5. Користувач натискає "Так"

**Frontend відправляє:**
```typescript
await sendMessage('Да', user?.id);
```

### 6. Backend створює workout

**ConversationManager:**
- Розпізнає "Да" як підтвердження
- Викликає `_create_workout_in_db()`
- Зберігає workout в БД з `genres` та `prompt` (якщо є)
- Повертає `workout_id`

**Відповідь:**
```json
{
  "message": "✅ Воркаут успішно створено!...",
  "workout": {
    "id": "workout-uuid-123",  // ← НОВИЙ ID!
    "type": "continuous",
    "duration_minutes": 30,
    "intensity": "low",
    "hr_zones": [110, 130]
  },
  "workout_id": "workout-uuid-123",
  "needs_clarification": false,
  "is_complete": true
}
```

### 7. Frontend обробляє створений workout

**useChat.ts:**
- Додає AI повідомлення про успішне створення
- Повертає `workout` з `id`

**ChatPage.tsx:**
- Перевіряє: `workout && workout.id`
- Встановлює `activeWorkoutId = workout.id`
- Показує кнопку "Так, згенерувати плейлист"

### 8. Користувач натискає "Так, згенерувати плейлист"

**Frontend викликає:**
```typescript
generateVariants(); // Генерує варіанти плейлистів
```

---

## ✅ Виправлення

### Проблема 1: Кнопки "Так/Ні" не відправляли відповідь в чат

**Було:**
```typescript
<button onClick={generateVariants}>Так</button>
```

**Стало:**
```typescript
<button onClick={async () => {
  const confirmedWorkout = await sendMessage('Да', user?.id);
  if (confirmedWorkout && confirmedWorkout.id) {
    setActiveWorkoutId(confirmedWorkout.id);
    setActiveWorkout(confirmedWorkout);
  }
}}>Так</button>
```

### Проблема 2: Frontend не розрізняв стани

**Було:**
- Завжди показував питання про плейлист
- Не перевіряв, чи workout вже створено

**Стало:**
- Перевіряє `activeWorkoutId`:
  - Якщо `null` → показує кнопки для підтвердження створення workout
  - Якщо є `id` → показує кнопку для генерації плейлисту

### Проблема 3: Workout не мав поля `id`

**Було:**
```typescript
export interface Workout {
  // ... без id
}
```

**Стало:**
```typescript
export interface Workout {
  id?: string; // Workout ID from database (if saved)
  // ...
}
```

---

## 🎯 Результат

Тепер flow працює правильно:

1. ✅ Користувач пише повідомлення
2. ✅ AI питає "Створити воркаут? (Да/Ні)"
3. ✅ Frontend показує кнопки "Так/Ні"
4. ✅ При натисканні "Так" - відправляє "Да" в чат
5. ✅ Backend створює workout в БД
6. ✅ Frontend отримує `workout_id`
7. ✅ Показує кнопку "Так, згенерувати плейлист"
8. ✅ Генерує варіанти плейлистів

---

**Статус:** ✅ Виправлено

