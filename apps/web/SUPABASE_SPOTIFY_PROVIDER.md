# Використання Supabase Spotify провайдера

## Що це дає

Додавання Spotify провайдера в Supabase Dashboard дає наступні переваги:

### ✅ Переваги

1. **Спрощення авторизації**

   - Не потрібно власний OAuth flow в backend
   - Supabase автоматично обробляє OAuth callback
   - Менше коду для підтримки

2. **Автоматичне управління сесіями**

   - Supabase Auth автоматично керує сесіями
   - Автоматичне оновлення токенів
   - Вбудована безпека

3. **Зберігання токенів**

   - Supabase автоматично зберігає access tokens та refresh tokens
   - Доступ до токенів через Supabase Auth API
   - Автоматичне оновлення токенів при закінченні

4. **Стандартний підхід**
   - Використання стандартного Supabase Auth API
   - Краща інтеграція з іншими Supabase функціями
   - Менше кастомного коду

---

## Як це використати в нашому проекті

### Варіант 1: Повна заміна (рекомендовано)

Замінити власний OAuth flow на Supabase Auth:

#### Frontend (`useAuth.ts`)

```typescript
import { supabase } from '../services/supabase';

const signInWithSpotify = async () => {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'spotify',
    options: {
      redirectTo: `${window.location.origin}/auth/callback`,
      scopes:
        'user-read-private user-read-email user-top-read playlist-modify-private playlist-modify-public',
    },
  });

  if (error) throw error;
};
```

#### Отримання Spotify токенів

```typescript
// Після авторизації через Supabase
const {
  data: { session },
} = await supabase.auth.getSession();

// Отримати Spotify токени через Supabase Auth
// Токени зберігаються в session.provider_token та session.provider_refresh_token
const spotifyAccessToken = session?.provider_token;
const spotifyRefreshToken = session?.provider_refresh_token;
```

#### Backend - отримання токенів

```python
# Через Supabase Admin API можна отримати токени користувача
from supabase import create_client

supabase_admin = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY
)

# Отримати user з Supabase Auth
user = supabase_admin.auth.admin.get_user_by_id(user_id)

# Отримати Spotify токени
# (потрібно перевірити структуру відповіді Supabase)
```

### Варіант 2: Гібридний підхід (поточний + Supabase)

Залишити поточний OAuth flow, але додати можливість використання Supabase провайдера:

- Користувач може вибрати: власний OAuth або Supabase OAuth
- Обидва підходи зберігають токени в таблиці `users`
- Більша гнучкість, але більше коду

---

## Що потрібно зробити

### 1. Налаштування в Supabase Dashboard

✅ **Вже зроблено:**

- Додано Spotify провайдера
- Налаштовано Client ID та Client Secret
- Callback URL: `https://eivkfrsspjawftocjwmg.supabase.co/auth/v1/callback`

### 2. Додати Redirect URL в Spotify Dashboard

1. Перейдіть в [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Відкрийте ваш додаток
3. Натисніть **"Edit Settings"**
4. В секції **"Redirect URIs"** додайте:
   ```
   https://eivkfrsspjawftocjwmg.supabase.co/auth/v1/callback
   ```
5. Натисніть **"Add"** та **"Save"**

### 3. Налаштувати Redirect URLs в Supabase

1. Supabase Dashboard → **Authentication** → **URL Configuration**
2. В **Redirect URLs** додайте:
   ```
   https://runbeatweb-production.up.railway.app/auth/callback
   http://localhost:3000/auth/callback
   ```

### 4. Оновити код (якщо використовуємо Варіант 1)

- Замінити `signInWithSpotify` на використання Supabase Auth
- Оновити `AuthCallbackPage` для обробки Supabase callback
- Оновити backend для отримання токенів з Supabase Auth

---

## Порівняння підходів

| Аспект                  | Поточний підхід       | Supabase провайдер            |
| ----------------------- | --------------------- | ----------------------------- |
| **Складність**          | Власний OAuth flow    | Стандартний Supabase Auth     |
| **Код**                 | Більше коду в backend | Менше коду, більше в frontend |
| **Управління токенами** | Власна логіка         | Автоматичне через Supabase    |
| **Оновлення токенів**   | Власна логіка         | Автоматичне                   |
| **Безпека**             | Власна реалізація     | Вбудована в Supabase          |
| **Гнучкість**           | Повний контроль       | Обмежена Supabase API         |

---

## Рекомендація

**Рекомендую використати Supabase Spotify провайдера** з наступних причин:

1. ✅ Менше коду для підтримки
2. ✅ Автоматичне управління токенами
3. ✅ Краща безпека (вбудована в Supabase)
4. ✅ Стандартний підхід
5. ✅ Легше масштабувати

**Але потрібно:**

- Перевірити, як отримувати Spotify токени з Supabase Auth для створення плейлистів
- Можливо, потрібно буде зберігати токени в таблиці `users` для backend доступу
- Оновити логіку авторизації в frontend

---

## Наступні кроки

1. **Протестувати Supabase Spotify провайдера:**

   - Спробувати авторизуватися через `supabase.auth.signInWithOAuth`
   - Перевірити, чи зберігаються токени
   - Перевірити доступ до токенів

2. **Якщо все працює:**

   - Замінити поточний OAuth flow на Supabase Auth
   - Оновити backend для отримання токенів з Supabase
   - Спростити код

3. **Якщо потрібні токени в backend:**
   - Можна зберігати токени в таблиці `users` після авторизації через Supabase
   - Або використовувати Supabase Admin API для отримання токенів
