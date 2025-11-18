# Spotify API Setup Guide

## Проблема: 403 Forbidden Error

Якщо ви бачите помилки типу:

```
HTTP Error for GET to https://api.spotify.com/v1/search returned 403
Check settings on developer.spotify.com/dashboard, the user may not be registered.
```

Це означає, що ваш Spotify додаток знаходиться в **Development Mode** і має обмежений доступ до API.

---

## Рішення: Активація Extended Quota Mode

### Крок 1: Перейдіть на Spotify Developer Dashboard

Відкрийте: https://developer.spotify.com/dashboard

### Крок 2: Виберіть ваш додаток

Знайдіть додаток RunBeat (або як він називається у вас) і клікніть на нього.

### Крок 3: Перевірте поточний режим

У верхній частині сторінки ви побачите статус:

- **Development Mode** ❌ (обмежений доступ, тільки для зареєстрованих користувачів)
- **Extended Quota Mode** ✅ (повний доступ до API)

### Крок 4: Запросіть Extended Quota Mode

1. Клікніть на кнопку **"Request Extension"** або **"Settings"**
2. Заповніть форму запиту:

   - **App Name**: RunBeat (або ваша назва)
   - **App Description**: Workout playlist generator that creates personalized music playlists based on workout parameters
   - **Commercial or Non-Commercial**: Виберіть відповідний варіант
   - **Expected Users**: Вкажіть очікувану кількість користувачів

3. Натисніть **"Submit"**

### Крок 5: Дочекайтеся схвалення

Spotify зазвичай розглядає запити протягом **1-2 робочих днів**.

---

## Альтернативне рішення: Додавання тестових користувачів (тимчасово)

Якщо ви не хочете чекати схвалення, можете додати користувачів вручну:

1. Перейдіть у **Settings** вашого додатку
2. Знайдіть розділ **"User Management"**
3. Додайте email-адреси користувачів, які матимуть доступ
4. Користувачі повинні прийняти запрошення

⚠️ **Обмеження**: Максимум 25 користувачів у Development Mode.

---

## Перевірка після активації

Після активації Extended Quota Mode:

1. Перезапустіть backend:

   ```bash
   docker-compose restart backend
   ```

2. Перевірте логи:

   ```bash
   docker-compose logs -f backend
   ```

3. Ви повинні побачити:

   ```
   INFO: SpotifyService initialized
   ```

   Без помилок 403.

---

## Додаткова інформація

### Які API endpoints потребують Extended Quota Mode?

- `/v1/search` - пошук треків, артистів, плейлистів
- `/v1/recommendations` - отримання рекомендацій
- `/v1/audio-features` - отримання характеристик треків

### Документація Spotify

- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
- [Quota Extension Guide](https://developer.spotify.com/documentation/web-api/concepts/quota-modes)

---

## Контакти

Якщо у вас виникли питання або проблеми, зверніться до команди розробки.
