# Spotify API Troubleshooting Guide

## Проблема: 404 помилки при виклику Spotify Recommendations API

### Можливі причини:

1. **Client Credentials токен не має доступу до Recommendations API**
   - **ВАЖЛИВО:** Spotify Recommendations API може не працювати з Client Credentials токеном
   - Рішення: Використовувати `seed_tracks` замість `seed_genres`
2. **Неправильні або відсутні credentials**
3. **Проблеми з аутентифікацією**
4. **Конфлікт параметрів у запиті**

---

## Крок 1: Перевірка Credentials

### 1.1. Перевірте змінні середовища

Переконайтеся, що в Railway (або локально) встановлені:

- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`

### 1.2. Перевірка в Spotify Dashboard

1. Перейдіть на https://developer.spotify.com/dashboard
2. Увійдіть у свій акаунт
3. Знайдіть ваш додаток RunBeat
4. Перевірте:
   - **Client ID** - має відповідати `SPOTIFY_CLIENT_ID`
   - **Client Secret** - натисніть "View client secret" та перевірте `SPOTIFY_CLIENT_SECRET`

### 1.3. Перевірка через логи

Після оновлення коду, у логах має з'явитися:

```
Spotify Client ID: [перші 10 символів]...
Secret: **********
```

Якщо бачите `MISSING` - credentials не встановлені.

---

## Крок 2: Тестування аутентифікації

### 2.1. Локальне тестування

Запустіть тестовий скрипт:

```bash
cd apps/backend
python test_spotify_simple.py
```

Очікуваний результат:

```
[OK] Spotify credentials found
[TEST] Testing Spotify API connection...
[OK] Got 5 tracks!
[SUCCESS] Spotify API connection works!
```

Якщо бачите помилку - перевірте credentials.

### 2.2. Перевірка токену в логах

Після оновлення коду, у логах має з'явитися:

```
Spotify access token obtained successfully
```

Якщо бачите помилку про токен - credentials неправильні.

---

## Крок 3: Перевірка параметрів запиту

### 3.1. Проблема з tempo параметрами

Spotify API може відхиляти запити з усіма трьома параметрами:

- `target_tempo`
- `min_tempo`
- `max_tempo`

**Рішення:** Код тепер автоматично:

1. Спочатку використовує тільки `min_tempo` та `max_tempo`
2. При 404 помилці пробує мінімальний запит (тільки seeds + energy)
3. Логує, який варіант спрацював

### 3.2. Перевірка логів

Шукайте в логах:

```
Attempting recommendations with params: {...}
Recommendations request successful
```

Або при помилці:

```
404 error - this may indicate:
1) Invalid Spotify credentials,
2) Spotify API endpoint issue, or
3) Parameter format problem
Retrying with minimal parameters (no tempo constraints)
```

---

## Крок 4: Перезапуск сервера

### 4.1. Після змін у коді

**Важливо:** Після оновлення коду потрібно перезапустити сервер!

1. **Локально:**

   ```bash
   # Зупиніть сервер (Ctrl+C)
   # Запустіть знову
   uvicorn app.main:app --reload
   ```

2. **На Railway:**
   - Зміни автоматично деплояться
   - Але перевірте, що деплой завершився успішно

### 4.2. Перевірка версії коду

У логах перевірте номери рядків:

- Старий код: рядки 136, 153
- Новий код: рядки 192-196, 225-230

Якщо бачите старі номери - сервер не перезапустився.

---

## Крок 5: Діагностика через логи

### 5.1. Успішний запит

```
SpotifyService initialized
Spotify access token obtained successfully
Attempting recommendations with params: {...}
Recommendations request successful
Fetched X candidate tracks
```

### 5.2. Помилка аутентифікації

```
Failed to get Spotify access token: [помилка]
Spotify authentication failed: [деталі]
```

**Рішення:** Перевірте credentials в Spotify Dashboard.

### 5.3. 404 помилка

```
HTTP Error for GET to https://api.spotify.com/v1/recommendations
returned 404 due to None
404 error - this may indicate:
1) Invalid Spotify credentials,
2) Spotify API endpoint issue, or
3) Parameter format problem
Retrying with minimal parameters (no tempo constraints)
```

**Рішення:**

1. Перевірте credentials
2. Якщо мінімальний запит теж не працює - проблема з credentials
3. Якщо мінімальний запит працює - проблема з tempo параметрами (вже виправлено)

---

## Крок 6: Альтернативні рішення

### 6.1. Оновлення spotipy

Якщо проблема залишається, спробуйте оновити spotipy:

```bash
pip install --upgrade spotipy
```

### 6.2. Перевірка версії API

Spotify API може змінюватися. Перевірте:

- https://developer.spotify.com/documentation/web-api/reference/get-recommendations
- Чи не змінилися вимоги до параметрів

### 6.3. Контакт з підтримкою Spotify

Якщо нічого не допомагає:

- https://community.spotify.com/t5/Spotify-for-Developers/bd-p/Spotify_Developer
- Створіть тікет з деталями помилки

---

## Швидка перевірка чеклист

- [ ] `SPOTIFY_CLIENT_ID` встановлений
- [ ] `SPOTIFY_CLIENT_SECRET` встановлений
- [ ] Credentials правильні в Spotify Dashboard
- [ ] Сервер перезапущений після змін
- [ ] У логах є "Spotify access token obtained successfully"
- [ ] Тестовий скрипт `test_spotify_simple.py` працює
- [ ] У логах немає помилок про credentials

---

## Контакти та ресурси

- **Spotify Developer Dashboard:** https://developer.spotify.com/dashboard
- **API Documentation:** https://developer.spotify.com/documentation/web-api
- **Community Forum:** https://community.spotify.com/t5/Spotify-for-Developers/bd-p/Spotify_Developer
