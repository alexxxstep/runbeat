# 🔧 Виправлення помилки Railway "Railpack could not determine how to build"

## Проблема

Railway показує помилку:
```
✖ Railpack could not determine how to build the app.
```

Це відбувається тому що Railway не може автоматично визначити Python проект в monorepo структурі.

## ✅ Рішення 1: Встановити Root Directory (НАЙПРОСТІШЕ!)

**Це найпростіше та найнадійніше рішення!**

### Покрокова інструкція:

1. **Відкрийте Railway Dashboard**
   - https://railway.app → ваш проект `runbeat`

2. **Відкрийте Settings**
   - Натисніть ⚙️ (Settings) в лівому меню

3. **Знайдіть Root Directory**
   - Прокрутіть до секції **"Root Directory"**

4. **Встановіть Root Directory**
   - Введіть: `apps/backend`
   - **БЕЗ слешів на початку/кінці!**

5. **Збережіть**
   - Натисніть **"Save"**
   - Railway автоматично перезапустить deployment

6. **Перевірте**
   - Deployment повинен пройти успішно!

**Дивіться детальну інструкцію:** [apps/backend/RAILWAY_ROOT_DIRECTORY.md](./apps/backend/RAILWAY_ROOT_DIRECTORY.md)

---

## ✅ Рішення 2: Використати railway.json (Вже створено)

Якщо Root Directory не працює, використайте `railway.json` в корені репозиторію.

Файл `railway.json` вже створено в корені з правильною конфігурацією.

### Як використати:

1. **Закомітьте зміни:**
   ```bash
   git add railway.json nixpacks.toml
   git commit -m "fix: add Railway configuration for monorepo"
   git push
   ```

2. **В Railway Dashboard:**
   - Відкрийте ваш проект
   - Railway автоматично використає `railway.json`

---

## ✅ Рішення 3: Створити Dockerfile (Альтернатива)

Якщо нічого не працює, можна створити Dockerfile:

```dockerfile
# apps/backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY apps/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/backend/ .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "$PORT"]
```

Потім в Railway оберіть Dockerfile builder.

---

## 📋 Чеклист виправлення

- [ ] Спробували встановити Root Directory = `apps/backend`
- [ ] Закомітили `railway.json` та `nixpacks.toml`
- [ ] Перевірили що всі файли закомічені (`git ls-files apps/backend/`)
- [ ] Перевірили логи в Railway Dashboard
- [ ] Health check працює (`curl https://ваш-проект.railway.app/health`)

---

## 🎯 Рекомендація

**Спочатку спробуйте Рішення 1 (Root Directory)** - це найпростіше та найнадійніше!

Якщо не працює - використайте Рішення 2 (railway.json).

---

**Після виправлення:** Deployment повинен пройти успішно! 🎉

