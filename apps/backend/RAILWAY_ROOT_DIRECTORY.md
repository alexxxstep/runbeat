# 🔧 Налаштування Root Directory в Railway

## Проблема

Railway не може автоматично визначити Python проект в monorepo структурі, тому що файли знаходяться в `apps/backend/`, а не в корені репозиторію.

## ✅ Рішення: Встановити Root Directory

**Це найпростіший та найнадійніший спосіб!**

### Покрокова інструкція:

1. **Відкрийте Railway Dashboard**
   - Перейдіть на https://railway.app
   - Відкрийте ваш проект `runbeat`

2. **Відкрийте Settings**
   - Натисніть на іконку ⚙️ (Settings) в лівому меню
   - Або натисніть на назву проекту → **Settings**

3. **Знайдіть Root Directory**
   - Прокрутіть вниз до секції **"Root Directory"**
   - За замовчуванням там буде порожньо або `/`

4. **Встановіть Root Directory**
   - В поле **"Root Directory"** введіть:
     ```
     apps/backend
     ```
   - **ВАЖЛИВО:** Без слеша на початку та в кінці!

5. **Збережіть зміни**
   - Натисніть **"Save"** або **"Update"**
   - Railway автоматично перезапустить deployment

6. **Перевірте deployment**
   - Перейдіть в **"Deployments"** вкладку
   - Подивіться на новий deployment
   - Він повинен пройти успішно!

---

## 📸 Візуальний гайд

```
Railway Dashboard
├── Your Project (runbeat)
│   ├── Deployments
│   ├── Variables
│   ├── Settings ⚙️  ← Натисніть тут
│   │   ├── General
│   │   ├── Root Directory  ← Знайдіть тут
│   │   │   └── [apps/backend]  ← Введіть це
│   │   └── ...
│   └── ...
```

---

## ✅ Після встановлення Root Directory

Railway буде:
- ✅ Шукати `requirements.txt` в `apps/backend/`
- ✅ Шукати `app/main.py` в `apps/backend/app/`
- ✅ Автоматично визначати Python проект
- ✅ Використовувати правильні шляхи для збірки

---

## 🔍 Перевірка

Після встановлення Root Directory, перевірте:

1. **Deployment логи:**
   - Railway Dashboard → Deployments → View Logs
   - Повинні бути логи про встановлення Python залежностей

2. **Health check:**
   ```bash
   curl https://ваш-проект.railway.app/health
   ```

3. **Структура файлів:**
   Railway тепер бачить:
   ```
   apps/backend/          ← Root Directory
   ├── app/
   │   └── main.py
   ├── requirements.txt
   └── ...
   ```

---

## 🐛 Якщо все ще не працює

1. **Перевірте що Root Directory правильний:**
   - Має бути: `apps/backend`
   - НЕ: `/apps/backend` або `apps/backend/`

2. **Перевірте що файли закомічені:**
   ```bash
   git ls-files apps/backend/
   ```

3. **Перевірте логи:**
   - Railway Dashboard → Deployments → View Logs
   - Шукайте помилки про відсутні файли

4. **Спробуйте видалити nixpacks.toml:**
   - Іноді `nixpacks.toml` конфліктує з Root Directory
   - Видаліть `nixpacks.toml` з кореня
   - Встановіть Root Directory = `apps/backend`
   - Railway використає автоматичне визначення

---

## 💡 Альтернативне рішення

Якщо Root Directory не працює, можна створити окремий репозиторій тільки для backend:

```bash
# Створіть новий репозиторій
mkdir runbeat-backend
cd runbeat-backend

# Скопіюйте файли
cp -r ../apps/backend/* .

# Ініціалізуйте git
git init
git add .
git commit -m "feat: initial backend"
git remote add origin https://github.com/ваш-username/runbeat-backend.git
git push -u origin main
```

Потім в Railway оберіть новий репозиторій.

---

**Рекомендація:** Використовуйте Root Directory - це найпростіше рішення! 🎯

