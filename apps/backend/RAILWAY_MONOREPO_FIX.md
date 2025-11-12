# 🔧 Виправлення помилки Railway для Monorepo

## Проблема

Railway не може знайти файли проекту, тому що це monorepo структура:
```
runbeat/
├── apps/
│   └── backend/    ← Backend знаходиться тут
│       ├── app/
│       ├── requirements.txt
│       └── ...
```

Railway шукає файли в корені репозиторію, а не в `apps/backend/`.

## ✅ Рішення 1: Встановити Root Directory в Railway (Рекомендовано)

### Крок 1: Відкрийте Railway Dashboard

1. Перейдіть в ваш проект на Railway
2. Відкрийте **Settings** (⚙️ іконка)
3. Знайдіть секцію **"Root Directory"**

### Крок 2: Встановіть Root Directory

1. В полі **"Root Directory"** введіть:
   ```
   apps/backend
   ```
2. Натисніть **"Save"**
3. Railway автоматично перезапустить deployment

### Крок 3: Перевірка

Після перезапуску deployment повинен пройти успішно.

---

## ✅ Рішення 2: Створити окремий репозиторій для Backend

Якщо Root Directory не працює, можна створити окремий репозиторій:

### Крок 1: Створіть новий репозиторій

```bash
# Створіть тимчасову папку
mkdir runbeat-backend-only
cd runbeat-backend-only

# Скопіюйте файли backend
cp -r ../apps/backend/* .

# Ініціалізуйте git
git init
git add .
git commit -m "feat: initial backend setup"

# Додайте remote
git remote add origin https://github.com/ваш-username/runbeat-backend.git
git push -u origin main
```

### Крок 2: Деплой з нового репозиторію

1. В Railway Dashboard → **New Project**
2. Оберіть новий репозиторій `runbeat-backend`
3. Railway автоматично визначить Python проект

---

## ✅ Рішення 3: Використати nixpacks.toml (Вже створено)

Якщо ви хочете залишити monorepo структуру, файл `nixpacks.toml` вже створено в корені проекту.

Переконайтесь що:
1. Файл `nixpacks.toml` знаходиться в корені репозиторію
2. Railway використовує Nixpacks builder (за замовчуванням)

---

## 🔍 Перевірка конфігурації

### Переконайтесь що є всі необхідні файли:

В `apps/backend/`:
- ✅ `requirements.txt`
- ✅ `Procfile` або `railway.json`
- ✅ `app/main.py`

В корені репозиторію:
- ✅ `nixpacks.toml` (якщо використовуєте Solution 3)

---

## 📝 Оновлення Railway Settings

Після встановлення Root Directory, перевірте:

1. **Root Directory**: `apps/backend`
2. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. **Build Command**: (залиште порожнім, Railway використає Nixpacks)

---

## 🐛 Troubleshooting

### Помилка все ще є?

1. **Перевірте логи:**
   - Railway Dashboard → Deployments → View Logs
   - Шукайте помилки про відсутні файли

2. **Перевірте структуру:**
   ```bash
   # В корені репозиторію
   ls apps/backend/requirements.txt
   ls apps/backend/app/main.py
   ```

3. **Перевірте git:**
   ```bash
   git ls-files apps/backend/
   ```
   Всі файли повинні бути закомічені.

4. **Спробуйте видалити railway.json:**
   - Іноді railway.json конфліктує з Nixpacks
   - Видаліть `apps/backend/railway.json`
   - Встановіть Root Directory = `apps/backend`
   - Railway використає Nixpacks автоматично

---

## ✅ Рекомендований підхід

**Найпростіше рішення:**
1. В Railway Dashboard → Settings → Root Directory
2. Встановіть: `apps/backend`
3. Збережіть
4. Railway автоматично перезапустить deployment

Це найпростіший спосіб для monorepo структури!

---

**Після виправлення:** Deployment повинен пройти успішно! 🎉

