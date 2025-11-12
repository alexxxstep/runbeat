# Налаштування Google OAuth в Supabase

Ця інструкція допоможе налаштувати авторизацію через Google для RunBeat.

## Як це працює

1. **Google Auth** - для входу в додаток (створює сесію в Supabase Auth)
2. **Spotify OAuth** - для підключення Spotify акаунту (створює плейлисти в Spotify)

Користувач може:

- Увійти через Google → отримати доступ до додатку
- Підключити Spotify → створювати плейлисти в своєму Spotify акаунті

## Крок 1: Створення Google OAuth Credentials

1. Перейдіть на [Google Cloud Console](https://console.cloud.google.com/)
2. Створіть новий проект або оберіть існуючий
3. Увімкніть **Google+ API**:

   - Перейдіть в **APIs & Services** > **Library**
   - Знайдіть "Google+ API" або "Google Identity"
   - Натисніть **Enable**

4. Створіть OAuth 2.0 credentials:

   - Перейдіть в **APIs & Services** > **Credentials**
   - Натисніть **Create Credentials** > **OAuth client ID**
   - Якщо потрібно, налаштуйте OAuth consent screen:
     - **User Type**: External (для тестування) або Internal (для організацій)
     - Заповніть обов'язкові поля
   - **Application type**: Web application
   - **Name**: RunBeat (або будь-яка назва)
   - **Authorized redirect URIs**:
     ```
     https://[ваш-проект].supabase.co/auth/v1/callback
     ```
     Для локальної розробки:
     ```
     http://localhost:54321/auth/v1/callback
     ```

5. Скопіюйте **Client ID** та **Client Secret**

---

## Крок 2: Налаштування в Supabase Dashboard

1. Перейдіть в ваш проект Supabase
2. Перейдіть в **Authentication** > **Providers**
3. Знайдіть **Google** в списку провайдерів
4. Увімкніть Google провайдер
5. Вставте:
   - **Client ID** (з Google Cloud Console)
   - **Client Secret** (з Google Cloud Console)
6. Натисніть **Save**

---

## Крок 3: Налаштування Redirect URL

### Для Production:

1. В Google Cloud Console, додайте до **Authorized redirect URIs**:

   ```
   https://[ваш-проект].supabase.co/auth/v1/callback
   ```

2. Переконайтеся, що в Supabase Dashboard > **Authentication** > **URL Configuration**:
   - **Site URL**: `https://runbeatweb-production.up.railway.app` (або ваш frontend URL)
   - **Redirect URLs**: Додайте ваш frontend URL з `/auth/callback`

### Для Development:

1. В Google Cloud Console, додайте:

   ```
   http://localhost:54321/auth/v1/callback
   http://localhost:3000/auth/callback
   ```

2. В Supabase Dashboard:
   - **Site URL**: `http://localhost:3000`
   - **Redirect URLs**: `http://localhost:3000/auth/callback`

---

## Крок 4: Перевірка

1. Запустіть frontend:

   ```bash
   cd apps/web
   npm run dev
   ```

2. Перейдіть на `/login`
3. Натисніть "Увійти через Google"
4. Виберіть Google акаунт
5. Після успішної авторизації ви маєте бути перенаправлені на головну сторінку

---

## Важливі примітки

1. **Google OAuth для авторизації в додатку**

   - Користувачі можуть увійти через Google
   - Це створює сесію в Supabase Auth

2. **Spotify OAuth для створення плейлистів**

   - Після входу через Google, користувач може окремо підключити Spotify
   - Spotify token зберігається в таблиці `users` в базі даних
   - Для створення плейлистів потрібен Spotify token

3. **Зв'язок між Google Auth та Spotify**
   - Supabase Auth user ID використовується як `user_id` в таблиці `users`
   - При створенні плейлиста, система шукає Spotify token по `user_id`

---

## Troubleshooting

### Помилка "redirect_uri_mismatch"

- Перевірте, що redirect URI в Google Console точно відповідає Supabase callback URL
- Формат: `https://[проект].supabase.co/auth/v1/callback`

### Помилка "invalid_client"

- Перевірте Client ID та Client Secret в Supabase Dashboard
- Переконайтеся, що Google OAuth credentials активні

### Користувач не може увійти

- Перевірте, що Google+ API увімкнено в Google Cloud Console
- Перевірте OAuth consent screen налаштування

---

## Додаткова інформація

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
