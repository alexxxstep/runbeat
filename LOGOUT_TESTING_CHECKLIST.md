# Logout Feature Testing Checklist

## Перевірка перед запуском

- [ ] Backend запущено (`cd apps/backend && uvicorn app.main:app --reload`)
- [ ] Frontend запущено (`cd apps/web && npm run dev`)
- [ ] База даних Supabase доступна

## Backend тестування

### 1. Unit тести
```bash
cd apps/backend
pytest tests/test_logout.py -v
```

**Очікуваний результат**: Всі тести проходять ✅

### 2. Endpoint тестування
```bash
cd apps/backend
./test_logout_endpoint.sh
```

**Очікуваний результат**:
- ✅ Test 1: Success (200)
- ✅ Test 2: Expected 404
- ✅ Test 3: Expected 422

### 3. Ручне тестування API

#### Test 1: Успішний logout
```bash
curl -X POST "http://localhost:8000/auth/logout?user_id=YOUR_USER_ID"
```
**Очікувана відповідь**:
```json
{
  "success": true,
  "message": "Logged out successfully",
  "user_id": "YOUR_USER_ID"
}
```

#### Test 2: Неіснуючий користувач
```bash
curl -X POST "http://localhost:8000/auth/logout?user_id=fake-user-id"
```
**Очікувана відповідь**: 404 Not Found

#### Test 3: Відсутній user_id
```bash
curl -X POST "http://localhost:8000/auth/logout"
```
**Очікувана відповідь**: 422 Validation Error

## Frontend тестування

### 1. Візуальна перевірка Navbar

- [ ] Navbar відображається на ChatPage
- [ ] Navbar відображається на HistoryPage
- [ ] Navbar відображається на PlayerPage
- [ ] Логотип "RunBeat" відображається зліва
- [ ] Кнопка "Вийти" червоного кольору справа
- [ ] Кнопка має hover ефект

### 2. Функціональна перевірка Logout

#### Крок 1: Початковий стан
- [ ] Відкрити DevTools → Application → Local Storage
- [ ] Перевірити наявність `spotify_user_id`
- [ ] Записати значення для порівняння

#### Крок 2: Виконати logout
- [ ] Натиснути кнопку "Вийти"
- [ ] Кнопка змінюється на "Вихід..." ⏳
- [ ] Кнопка стає disabled (неактивною)

#### Крок 3: Після logout
- [ ] Користувач перенаправлений на `/login`
- [ ] Local Storage порожній (перевірити в DevTools)
- [ ] Session Storage порожній
- [ ] Відображається сторінка входу через Spotify

#### Крок 4: Повторний вхід
- [ ] Натиснути "Увійти через Spotify"
- [ ] Пройти OAuth flow Spotify
- [ ] Успішний вхід в систему
- [ ] Новий `spotify_user_id` в localStorage (може відрізнятися)

### 3. Перевірка на різних сторінках

#### ChatPage
- [ ] Navbar відображається вгорі
- [ ] Кнопка "Вийти" працює
- [ ] Після logout перенаправлення на `/login`

#### HistoryPage
- [ ] Navbar відображається вгорі
- [ ] Кнопка "Вийти" працює
- [ ] Після logout перенаправлення на `/login`

#### PlayerPage
- [ ] Navbar відображається вгорі
- [ ] Кнопка "Вийти" працює
- [ ] Після logout перенаправлення на `/login`

### 4. Перевірка помилок

#### Test 1: Backend недоступний
- [ ] Зупинити backend
- [ ] Натиснути "Вийти"
- [ ] Frontend все одно очищає localStorage
- [ ] Користувач перенаправлений на `/login`
- [ ] Помилка логується в console

#### Test 2: Повторний logout
- [ ] Вийти з системи
- [ ] Спробувати вручну викликати logout API
- [ ] Отримати 404 (користувач не знайдений)

### 5. Responsive дизайн

- [ ] Desktop (>1024px): Navbar розтягується на всю ширину
- [ ] Tablet (768-1024px): Navbar коректно відображається
- [ ] Mobile (<768px): Navbar адаптується до маленького екрану

### 6. Dark Mode

- [ ] Увімкнути dark mode
- [ ] Navbar має темний фон
- [ ] Кнопка "Вийти" має коректні кольори для dark mode
- [ ] Hover ефект працює в dark mode

## База даних перевірка

### Перевірка очищення токенів

```sql
-- Перевірити токени до logout
SELECT
  id,
  spotify_user_id,
  spotify_access_token IS NOT NULL as has_access_token,
  spotify_refresh_token IS NOT NULL as has_refresh_token,
  spotify_token_expires_at
FROM users
WHERE id = 'YOUR_USER_ID';

-- Після logout має бути:
-- has_access_token: false
-- has_refresh_token: false
-- spotify_token_expires_at: NULL
```

### Перевірка збереження даних

```sql
-- Ці дані мають залишитися після logout
SELECT
  id,
  email,
  spotify_user_id,  -- НЕ очищується
  created_at,
  updated_at        -- Оновлюється
FROM users
WHERE id = 'YOUR_USER_ID';
```

## Перевірка безпеки

- [ ] Токени видалені з бази даних після logout
- [ ] localStorage повністю очищено
- [ ] sessionStorage повністю очищено
- [ ] Неможливо використати старий токен після logout
- [ ] При новому вході генерується новий токен

## Performance перевірка

- [ ] Logout виконується швидко (<2 секунди)
- [ ] Немає затримок при перенаправленні
- [ ] Немає memory leaks (перевірити в DevTools Performance)

## Accessibility перевірка

- [ ] Кнопка "Вийти" має `title` атрибут
- [ ] Кнопка доступна через Tab navigation
- [ ] Можна активувати кнопку через Enter/Space
- [ ] Disabled стан візуально зрозумілий

## Підсумок

**Дата тестування**: _______________
**Тестувальник**: _______________
**Результат**: ⬜ Пройдено ⬜ Не пройдено

**Знайдені проблеми**:
1. _______________
2. _______________
3. _______________

**Коментарі**:
_______________________________________________
_______________________________________________
_______________________________________________

---

✅ **Всі тести пройдено** - функціонал готовий до production
⚠️ **Є зауваження** - потрібні виправлення
❌ **Тести не пройдено** - потрібна додаткова робота

