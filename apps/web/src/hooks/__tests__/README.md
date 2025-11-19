# Tests for useChat Hook

## Запуск тестів

```bash
# Запустити всі тести
npm run test

# Запустити тести в watch режимі
npm run test -- --watch

# Запустити тести з UI
npm run test:ui

# Запустити тести з покриттям коду
npm run test:coverage
```

## Покриття тестами

Тести покривають наступні сценарії:

### sendMessage
- ✅ Обробка `needs_clarification=true`
- ✅ Обробка `is_complete=true` з workout
- ✅ Обробка workout без ID (очікування підтвердження)
- ✅ Обробка playlist в відповіді
- ✅ Обробка помилок
- ✅ Оновлення conversation ID
- ✅ Стан завантаження (loading)
- ✅ Очищення помилок при новому повідомленні

### generatePlaylist
- ✅ Успішна генерація плейлисту
- ✅ Обробка помилок генерації

### clearMessages
- ✅ Очищення повідомлень та стану

### addWorkoutActivationMessage
- ✅ Додавання повідомлення про активацію workout

### metadata handling
- ✅ Включення метаданих в повідомлення
- ✅ Обробка `needs_clarification` та `is_complete`
- ✅ Fallback для `undefined is_complete`

## Встановлення залежностей

Якщо тести не запускаються, встановіть залежності:

```bash
npm install
```

## Структура тестів

Тести використовують:
- **Vitest** - тестовий фреймворк
- **React Testing Library** - для тестування React hooks
- **jsdom** - для емуляції DOM середовища

