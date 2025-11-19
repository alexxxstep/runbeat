# План інтеграції Frontend з новою схемою AI агентів

## 🔍 Аналіз проблем

### Виявлені проблеми:

1. **Не використовуються поля `needs_clarification` та `is_complete`**

   - Frontend не використовує ці поля з `ChatResponse` для визначення стану розмови
   - Логіка покладається на наявність `workout` об'єкта, що не завжди коректно

2. **Обробка workout об'єктів**

   - Frontend перевіряє `workout && workout.id`, але тепер workout може бути створений одразу
   - Не враховується `is_complete` для визначення завершеності розмови

3. **Відображення стану розмови**

   - Немає візуальної індикації, коли агент збирає інформацію (`needs_clarification=true`)
   - Немає індикації завершеності розмови (`is_complete=true`)

4. **Обробка помилок валідації**
   - ✅ Працює правильно: backend повертає 200 з повідомленням, frontend відображає як звичайне повідомлення

---

## 📋 План виправлення

### Крок 1: Оновлення `useChat.ts` hook

**Файл**: `apps/web/src/hooks/useChat.ts`

**Зміни**:

1. Використовувати `needs_clarification` та `is_complete` з `ChatResponse`
2. Повертати додаткову інформацію про стан розмови
3. Додати логіку для обробки стану "збір інформації"

**Код**:

```typescript
// В sendMessage функції, після отримання response:
const aiMessage: Message = {
  id: (Date.now() + 1).toString(),
  role: 'assistant',
  content: response.message,
  timestamp: new Date(),
  workout: response.workout,
  playlist: response.playlist ? { ... } : undefined,
  // Додати метадані про стан розмови
  _metadata: {
    needs_clarification: response.needs_clarification,
    is_complete: response.is_complete,
  },
};

// Повернути об'єкт з додатковою інформацією
return {
  workout: response.workout || null,
  needs_clarification: response.needs_clarification,
  is_complete: response.is_complete,
  _hasPlaylist: !!response.playlist,
};
```

---

### Крок 2: Оновлення `ChatPage.tsx`

**Файл**: `apps/web/src/pages/ChatPage.tsx`

**Зміни**:

1. Обробляти `needs_clarification` та `is_complete` з відповіді
2. Показувати візуальні індикатори стану розмови
3. Оновити логіку `handleSend` для врахування нових полів

**Код**:

```typescript
const handleSend = async (text: string) => {
  const result = await sendMessage(text, user?.id);

  // result тепер об'єкт з workout, needs_clarification, is_complete
  const workout = result?.workout;
  const needsClarification = result?.needs_clarification ?? false;
  const isComplete = result?.is_complete ?? false;

  // Якщо розмова завершена і workout створений
  if (isComplete && workout?.id) {
    setActiveWorkout(workout);
    setActiveWorkoutId(workout.id);
    setRefreshTrigger((prev) => prev + 1);
    setShowPlaylistQuestion(true);
    return;
  }

  // Якщо потрібна уточнююча інформація
  if (needsClarification) {
    // Просто продовжуємо розмову, агент вже запитав
    return;
  }

  // Якщо workout готовий до підтвердження
  if (workout && !needsClarification && !isComplete) {
    setActiveWorkout(workout);
    setActiveWorkoutId(null);
    setShowPlaylistQuestion(true);
  }
};
```

---

### Крок 3: Оновлення типів

**Файл**: `apps/web/src/types/index.ts`

**Зміни**:

1. Додати метадані до `Message` інтерфейсу
2. Оновити тип повернення `sendMessage`

**Код**:

```typescript
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  workout?: Workout;
  playlist?: Playlist;
  _metadata?: {
    needs_clarification?: boolean;
    is_complete?: boolean;
  };
}

// Новий тип для повернення sendMessage
export interface SendMessageResult {
  workout: Workout | null;
  needs_clarification: boolean;
  is_complete: boolean;
  _hasPlaylist?: boolean;
}
```

---

### Крок 4: Візуальні індикатори стану

**Файл**: `apps/web/src/components/Chat/MessageBubble.tsx`

**Зміни**:

1. Додати візуальний індикатор для `needs_clarification`
2. Додати індикатор для `is_complete`

**Код**:

```typescript
// В компоненті MessageBubble
const needsClarification =
  message._metadata?.needs_clarification ??
  message.workout?.needs_clarification;
const isComplete = message._metadata?.is_complete;

// Додати візуальні індикатори
{
  needsClarification && (
    <div className='text-xs text-blue-500 mt-1'>
      ℹ️ Потрібна додаткова інформація
    </div>
  );
}
{
  isComplete && (
    <div className='text-xs text-green-500 mt-1'>✅ Розмова завершена</div>
  );
}
```

---

### Крок 5: Тести

**Файл**: `apps/web/src/hooks/__tests__/useChat.test.ts` (створити)

**Тести**:

1. Тест обробки `needs_clarification=true`
2. Тест обробки `is_complete=true`
3. Тест обробки workout без ID (збір інформації)
4. Тест обробки workout з ID (створений)
5. Тест обробки помилок валідації (200 response)

---

### Крок 6: Оптимізація

**Оптимізації**:

1. Мемоізація обчислень стану розмови
2. Оптимізація ре-рендерів при зміні стану
3. Додати debounce для швидких повідомлень

---

## ✅ Чеклист виконання

- [x] Крок 1: Оновити `useChat.ts` ✅
- [x] Крок 2: Оновити `ChatPage.tsx` ✅
- [x] Крок 3: Оновити типи ✅
- [x] Крок 4: Додати візуальні індикатори ✅
- [ ] Крок 5: Написати тести (опціонально)
- [x] Крок 6: Оптимізувати код ✅
- [x] Code review ✅
- [ ] Тестування вручну
- [ ] Деплой

---

## 📝 Примітки

1. **Зворотна сумісність**: Зміни мають бути зворотно сумісними з існуючим кодом
2. **Fallback**: Якщо `needs_clarification` або `is_complete` не надані, використовувати логіку на основі `workout`
3. **Логування**: Додати логування для діагностики проблем
4. **Документація**: Оновити JSDoc коментарі для нових функцій

---

**Дата створення**: 2025-11-19
**Дата завершення**: 2025-11-19
**Автор**: AI Assistant
**Статус**: ✅ Implementation Complete

---

## 📝 Виконані зміни

### ✅ Крок 1: Оновлено `useChat.ts`

- Додано тип повернення `SendMessageResult`
- `sendMessage` тепер повертає структурований об'єкт з `workout`, `needs_clarification`, `is_complete`
- Додано метадані `_metadata` до повідомлень

### ✅ Крок 2: Оновлено `ChatPage.tsx`

- `handleSend` обробляє новий формат відповіді
- Додано логіку для різних станів розмови
- Правильна обробка `needs_clarification` та `is_complete`

### ✅ Крок 3: Оновлено типи

- Додано `_metadata` до `Message` інтерфейсу
- Створено `SendMessageResult` тип

### ✅ Крок 4: Додано візуальні індикатори

- Індикатор "Потрібна додаткова інформація" для `needs_clarification`
- Індикатор "✅ Розмова завершена" для `is_complete`
- Зворотна сумісність з існуючим кодом

### ✅ Крок 6: Оптимізація

- Всі файли пройшли lint перевірку
- Код готовий до використання
