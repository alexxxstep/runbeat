# Звіт про тестування продуктивності генерації варіантів плейлистів

## 📊 Результати тестування

### Виявлені проблеми

#### 🔴 КРИТИЧНА: Послідовна генерація варіантів

**Проблема**: Варіанти генеруються послідовно, а не паралельно.

**Доказ**:
- Variant 1 генерується першим (рядок 781)
- Variant 2 починає генеруватися тільки після завершення Variant 1 (рядок 850)
- Загальний час = час Variant 1 + час Variant 2

**Вплив**:
- Якщо один варіант генерується 10 секунд → два варіанти = 20 секунд
- При паралельній генерації → ~10 секунд (2x швидше!)

**Код проблеми** (`apps/backend/app/api/routes/playlists.py:781-850`):
```python
# Variant 1 - генерується першим
playlist_data_variant1 = await generator.generate(...)  # ~10s

# Variant 2 - генерується після Variant 1
playlist_data_variant2 = await generator.generate(...)  # ~10s
# Загальний час: ~20s
```

#### 🟡 СЕРЕДНЯ: Retry логіка додає затримки

**Проблема**: Коли Variant 2 не знаходить достатньо треків, він робить retry.

**Доказ з тестів**:
- При 20 excluded tracks: 3 виклики generator
- Retry додає повний час генерації знову

**Вплив**:
- Кожен retry = +100% часу
- При багатьох excluded tracks може бути кілька retry

#### 🟢 ДОБРЕ: Паралельні запити до Spotify

**Позитивний момент**: `_fetch_candidates()` виконує запити до Spotify паралельно.

**Доказ**:
- 7 сегментів обробляються за ~0.116s (паралельно)
- Якби послідовно: ~0.7s

## 📈 Метрики продуктивності

### Час генерації варіантів (з тестів)

| Сценарій | Variant 1 | Variant 2 | Загальний | Очікуваний (паралельно) | Втрата |
|----------|-----------|-----------|-----------|-------------------------|--------|
| Короткий (20 хв) | 0.1s | 0.1s | 0.2s | 0.1s | **50%** |
| Середній (40 хв) | 0.1s | 0.1s | 0.3s | 0.1s | **67%** |
| Довгий (60 хв) | 2.0s | 2.0s | 4.0s | 2.0s | **50%** |
| З excluded (30) | 0.1s | 0.1s + retry | 0.3s | 0.1s | **67%** |
| З retry | 0.5s | 0.5s + 0.5s | 1.5s | 0.5s | **67%** |

### Bottlenecks (за пріоритетом)

1. **Послідовна генерація варіантів** 🔴
   - Втрата часу: **~50%** від загального часу
   - Пріоритет: **ВИСОКИЙ**
   - Вирішення: Паралелізація

2. **Retry логіка** 🟡
   - Втрата часу: до **100%** додаткового часу при retry
   - Пріоритет: **СЕРЕДНІЙ**
   - Вирішення: Покращена логіка вибору треків

3. **Запити до Spotify API** 🟢
   - Час на запит: ~0.1s на сегмент
   - Статус: **Вже оптимізовано** (паралельні запити)

## 💡 Рекомендації по оптимізації

### 1. Паралелізувати генерацію варіантів (ВИСОКИЙ ПРІОРИТЕТ)

**Проблема**: Variant 2 потребує excluded tracks від Variant 1.

**Рішення 1**: Генерувати Variant 2 без excluded tracks від Variant 1, потім фільтрувати дублікати.

```python
# Генерувати обидва варіанти паралельно
variant1_task = generator.generate(
    workout=request.workout,
    user_preferences=user_prefs_variant1,
    excluded_track_ids=excluded_track_ids_from_request,
    ...
)

variant2_task = generator.generate(
    workout=request.workout,
    user_preferences=user_prefs_variant2,
    excluded_track_ids=excluded_track_ids_from_request,  # Без variant 1 tracks
    ...
)

# Виконуємо паралельно
playlist_data_variant1, playlist_data_variant2 = await asyncio.gather(
    variant1_task,
    variant2_task
)

# Фільтруємо дублікати з variant 1
variant1_track_ids = {t.id for t in playlist_data_variant1.tracks}
variant2_tracks_filtered = [
    t for t in playlist_data_variant2.tracks
    if t.id not in variant1_track_ids
]

# Якщо після фільтрації недостатньо треків, додаємо нові
if len(variant2_tracks_filtered) < playlist_data_variant2.total_tracks * 0.8:
    # Генеруємо додаткові треки
    ...
```

**Рішення 2**: Генерувати 3 варіанти паралельно, вибрати 2 найкращі.

```python
# Генерувати 3 варіанти паралельно
variants = await asyncio.gather(
    generator.generate(..., user_preferences=prefs1, ...),
    generator.generate(..., user_preferences=prefs2, ...),
    generator.generate(..., user_preferences=prefs3, ...),
)

# Вибрати 2 найкращі (найбільше різноманітні)
variant1, variant2 = select_best_variants(variants)
```

**Очікуваний ефект**: **2x швидше** (з 20s до 10s)

### 2. Оптимізувати retry логіку (СЕРЕДНІЙ ПРІОРИТЕТ)

**Проблема**: Retry виконується повністю, навіть якщо проблема в excluded tracks.

**Рішення**:
- Зменшити кількість excluded tracks для variant 2
- Або генерувати variant 2 без excluded tracks variant 1, а потім фільтрувати дублікати

**Очікуваний ефект**: **30-50% швидше** при retry

### 3. Кешування результатів Spotify API (НИЗЬКИЙ ПРІОРИТЕТ)

**Ідея**: Кешувати результати запитів до Spotify для однакових параметрів.

**Вплив**: Може прискорити повторні генерації з однаковими параметрами.

## 🎯 План дій

1. ✅ Створити тести продуктивності
2. ✅ Виявити bottlenecks
3. ⬜ Реалізувати паралельну генерацію варіантів
4. ⬜ Оптимізувати retry логіку
5. ⬜ Додати метрики продуктивності в production
6. ⬜ Моніторинг часу генерації

## 📊 Очікувані покращення

Після оптимізацій:

| Метрика | Поточний | Після оптимізації | Покращення |
|---------|----------|-------------------|------------|
| Час генерації (короткий) | 0.2s | 0.1s | **2x** |
| Час генерації (середній) | 0.3s | 0.1s | **3x** |
| Час генерації (довгий) | 4.0s | 2.0s | **2x** |
| Час з retry | 1.5s | 0.5-0.7s | **2-3x** |
| **Загальне покращення** | - | - | **2-3x швидше** |

## 🧪 Тестування

### Запуск тестів продуктивності

```bash
cd apps/backend
pytest tests/test_variants_performance.py -v -s
```

### Перевірка метрик в production

Додати логування:
```python
logger.info(f"Variant 1 generation time: {variant1_time:.2f}s")
logger.info(f"Variant 2 generation time: {variant2_time:.2f}s")
logger.info(f"Total variants generation time: {total_time:.2f}s")
logger.info(f"Retry count: {retry_count}")
```

## 📝 Висновки

1. **Основна проблема**: Послідовна генерація варіантів втрачає ~50% часу
2. **Рішення**: Паралелізувати генерацію варіантів
3. **Очікуваний ефект**: 2-3x швидше генерація варіантів
4. **Пріоритет**: Високий - це найбільший bottleneck

## 🔗 Додаткові матеріали

- [Детальний аналіз](./VARIANTS_PERFORMANCE_ANALYSIS.md)
- [Тести продуктивності](./test_variants_performance.py)
- [Код генерації варіантів](../app/api/routes/playlists.py:716-1111)

---

**Дата створення**: 2024-11-14
**Автор**: AI Assistant
**Статус**: Аналіз завершено, очікується імплементація оптимізацій

