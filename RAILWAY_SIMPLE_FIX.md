# ✅ Просте рішення для Railway Monorepo

## Проблема

Railway не може автоматично визначити Python проект в monorepo структурі.

## ✅ Рішення: Встановити Root Directory

**Це найпростіше та найнадійніше рішення!**

### Покрокова інструкція:

1. **Відкрийте Railway Dashboard**
   - https://railway.app → ваш проект `runbeat`

2. **Відкрийте Settings**
   - Натисніть ⚙️ (Settings) в лівому меню або на назві проекту

3. **Знайдіть Root Directory**
   - Прокрутіть до секції **"Root Directory"**

4. **Встановіть Root Directory**
   - Введіть: `apps/backend`
   - **БЕЗ слешів на початку/кінці!**
   - Просто: `apps/backend`

5. **Збережіть**
   - Натисніть **"Save"** або **"Update"**
   - Railway автоматично перезапустить deployment

6. **Перевірте**
   - Перейдіть в **"Deployments"**
   - Новий deployment повинен пройти успішно!

---

## 🎯 Чому це працює?

Коли ви встановлюєте Root Directory = `apps/backend`, Railway:
- ✅ Бачить `requirements.txt` в корені (відносно Root Directory)
- ✅ Бачить `app/main.py` в правильному місці
- ✅ Автоматично визначає Python проект
- ✅ Використовує правильні шляхи для збірки

---

## 📋 Альтернатива: Використати railway.json

Якщо Root Directory не працює, файл `railway.json` вже створено в корені репозиторію.

Railway автоматично використає його після наступного push.

---

## ✅ Після встановлення Root Directory

1. **Перевірте deployment:**
   - Railway Dashboard → Deployments → View Logs
   - Повинні бути логи про встановлення Python залежностей

2. **Health check:**
   ```bash
   curl https://ваш-проект.railway.app/health
   ```

3. **Очікуваний результат:**
   ```json
   {"status":"healthy","timestamp":"...","service":"runbeat-api"}
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

3. **Видаліть старий deployment:**
   - Railway Dashboard → Deployments
   - Видаліть failed deployment
   - Railway створить новий автоматично

---

**Рекомендація:** Використовуйте Root Directory - це найпростіше рішення! 🎯

