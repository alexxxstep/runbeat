# RunBeat — Архітектурний огляд

> **Версія**: 2.1 | **Дата**: 19 листопада 2025 | **Статус**: Production Ready

Цей документ описує високорівневу архітектуру RunBeat — AI-driven системи для створення персоналізованих workout-планів та Spotify плейлистів через природний діалог.

**Пов'язані документи**:

- [AI Conversation Architecture](./AI_CONVERSATION_ARCHITECTURE.md) — деталізація LangChain агентів, промптів та conversation flow
- [Root README](../README.md) — швидкий старт, тести, деплой

---

## 1. Загальна архітектура

```
┌─────────────┐
│    User     │ 👤
│  (Browser)  │
└──────┬──────┘
       │ Chat UI
       ▼
┌─────────────────────────┐
│   React + Vite SPA      │
│   • Zustand (useChat)   │
│   • Tailwind CSS        │
│   • TypeScript          │
└──────────┬──────────────┘
           │ REST API
           │ /api/v1/*
           ▼
┌──────────────────────────────────────────┐
│         FastAPI Backend                  │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │      SupervisorAgent               │ │
│  │  (Оркестратор розмови)             │ │
│  └──────────┬─────────────────────────┘ │
│             │                            │
│             ▼                            │
│  ┌────────────────────────────────────┐ │
│  │      WorkoutBuilder                │ │
│  │  (LangChain AI Agent)              │ │
│  │                                    │ │
│  │  Tools:                            │ │
│  │  • extract_workout_parameters      │ │
│  │  • create_workout_from_params      │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │      PlaylistGenerator             │ │
│  │  (Spotify Integration)             │ │
│  └────────────────────────────────────┘ │
└──────────┬───────────────┬───────────────┘
           │               │
           ▼               ▼
    ┌──────────┐    ┌──────────────┐
    │ Supabase │    │  Spotify API │
    │(Postgres)│    │   (OAuth)    │
    └──────────┘    └──────────────┘
```

**Ключові компоненти**:

- **Frontend**: React 18 + Vite, Tailwind CSS, Zustand (`useChat` hook), TypeScript
- **Backend**: FastAPI (async), LangChain multi-agent (Supervisor + WorkoutBuilder), Pydantic V2
- **AI Models**: OpenAI GPT-4/4o (конфігурується через `.env`: `OPENAI_MODEL_CONVERSATION`, `OPENAI_MODEL_SUPERVISOR`, `OPENAI_MODEL_PARSER`)
- **Інтеграції**: Supabase (Postgres + Auth), Spotify API (OAuth + recommendations)
- **Деплой**: Railway (Nixpacks для backend та web)

---

## 2. Backend Layers

| Layer     | Відповідальність                                                         | Ключові модулі                                                                                  |
| --------- | ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| API       | REST маршрути `/api/v1/chat`, `/workouts`, `/playlists`                  | `app/api/routes/*`                                                                              |
| Services  | Конверсійний сервіс, генератор плейлистів, інтеграція з Spotify/Supabase | `conversation_service.py`, `playlist_generator.py`, `spotify_service.py`, `supabase_service.py` |
| AI Agents | Оркестрація розмови, агрегація параметрів, створення воркаутів           | `agents/supervisor.py`, `services/workout_builder.py`, `agents/tools/*`, `agents/prompts/*`     |
| Schemas   | Pydantic моделі для API та міжсервісної взаємодії                        | `schemas/chat.py`, `schemas/workout.py`, `schemas/playlist.py`, `schemas/conversation.py`       |

**Стан розмови**
`ConversationState` містить `history`, `collected_parameters`, `last_question`, `active_workout`, `prompt`, `_metadata`. Supervisor тримає стан у пам’яті та після кожного кроку синхронізує з Supabase через `ConversationService`.

---

## 3. AI Conversation Stack

```
👤 User
  │
  │ 1. Вводить повідомлення: "хочу легку пробіжку 30 хв"
  ▼
┌─────────────────────────────────────────┐
│          Frontend (React)               │
│  • useChat hook                         │
│  • sendMessage()                        │
└────────────┬────────────────────────────┘
             │
             │ 2. POST /api/v1/chat/message
             ▼
┌─────────────────────────────────────────┐
│         Chat API Endpoint               │
└────────────┬────────────────────────────┘
             │
             │ 3. handle_message(user_id, text)
             ▼
┌─────────────────────────────────────────┐
│        SupervisorAgent                  │
│  • Завантажує ConversationState         │
│  • Делегує WorkoutBuilder               │
└────────────┬────────────────────────────┘
             │
             │ 4. process_message(state, text)
             ▼
┌─────────────────────────────────────────┐
│        WorkoutBuilder                   │
│  (LangChain AgentExecutor)              │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ 5. Автовиклик Tools:              │ │
│  │                                   │ │
│  │ a) extract_workout_parameters     │ │
│  │    → duration: 30, intensity: low │ │
│  │                                   │ │
│  │ b) create_workout_from_params     │ │
│  │    (якщо підтверджено)            │ │
│  │    → created_workout              │ │
│  └───────────────────────────────────┘ │
│                                         │
│  6. Формує відповідь:                   │
│     "Супер! 30 хв легка пробіжка.       │
│      Яку музику?"                       │
└────────────┬────────────────────────────┘
             │
             │ 7. ConversationUpdate
             │    (response + metadata + workout)
             ▼
┌─────────────────────────────────────────┐
│        SupervisorAgent                  │
│  • Зберігає стан у Supabase             │
│  • Повертає ChatResponse                │
└────────────┬────────────────────────────┘
             │
             │ 8. ChatResponse
             ▼
┌─────────────────────────────────────────┐
│          Frontend                       │
│  • Рендерить відповідь AI               │
│  • Показує CTA (якщо workout готовий)   │
└─────────────────────────────────────────┘
             │
             ▼
👤 User бачить відповідь + кнопку "Згенерувати плейлист"
```

1. **SupervisorAgent**

   - Викликається з `/api/v1/chat/message`.
   - Ініціалізує або відновлює `ConversationState`.
   - Делегує текст до WorkoutBuilder та зберігає повернений `ConversationUpdate`.
   - Виконує fallback `_create_workout_from_params_internal`, якщо користувач підтвердив створення, але агент не викликав tool.
   - Позначає розмову завершеною та очищає стан після success/decline.

2. **WorkoutBuilder**

   - LangChain `AgentExecutor` з кастомним системним промптом (`CONVERSATION_AGENT_SYSTEM_PROMPT`).
   - Після кожного повідомлення:
     - Автоматично викликає `extract_workout_parameters` (через tool і дублюючий авто-запуск) і мерджить параметри.
     - Враховує історію (останніх ≤15 повідомлень) через `ConversationBufferMemory`.
     - Забезпечує емодзі-дружні відповіді, жодних повторених питань, завжди посилається на зібрані дані.
     - Коли duration + intensity + genres зібрані, один раз питає про опціональний `prompt` (атмосфера/артисти/жанри), зберігає його та переходить до фінального підтвердження.
   - Викликає `create_workout_from_params` лише після підтвердження (так/yes/ок).
   - Повертає `ConversationUpdate` з `created_workout`, `needs_clarification`, `is_complete`.

3. **Tools**

   - `extract_workout_parameters`: rule-based parser з нормалізацією (жанри, інтенсивність, тривалість 5‑300 хв), повертає `all_collected`.
   - `create_workout_from_params`: Pydantic-схема з optional duration/intensity (валидація всередині), додає `prompt`, genres у воркаут та повертає табличний запис.

4. **Помилки**
   - Всі помилки з `duration/intensity` перехоплюються в agent builder + `/chat` endpoint і повертають дружнє повідомлення, не розриваючи ланцюг.
   - Supervisor логічно гасить стан після success/decline, що усуває дублікати питань.

---

## 4. Playlist & Prompt Flow

```
┌─────────────────────────────────────────┐
│        WorkoutBuilder                   │
│  Збирає параметри:                      │
│  • duration_minutes ✓                   │
│  • intensity ✓                          │
│  • genres ✓                             │
└────────────┬────────────────────────────┘
             │
             │ Всі базові параметри зібрані?
             ▼
        ┌─────────┐
        │   ТАК   │
        └────┬────┘
             │
             │ Питає: "Маєш побажання до атмосфери?"
             ▼
┌─────────────────────────────────────────┐
│  User відповідає:                       │
│  "нічний драйв, synthwave"              │
└────────────┬────────────────────────────┘
             │
             │ Зберігає у ConversationState
             ▼
┌─────────────────────────────────────────┐
│  collected_parameters:                  │
│  {                                      │
│    duration: 30,                        │
│    intensity: "moderate",               │
│    genres: ["electronic", "rock"],      │
│    prompt: "нічний драйв, synthwave" ✨ │
│  }                                      │
└────────────┬────────────────────────────┘
             │
             │ create_workout_from_params
             ▼
┌─────────────────────────────────────────┐
│  Workout створено в БД                  │
│  • prompt зберігається у workout        │
└────────────┬────────────────────────────┘
             │
             │ ChatResponse → Frontend
             ▼
┌─────────────────────────────────────────┐
│  Frontend (ChatPage)                    │
│  • Синхронізує workout.prompt           │
│    → WorkoutSettings.prompt             │
│  • Показує CTA "Згенерувати плейлист"   │
└────────────┬────────────────────────────┘
             │
             │ User клікає "Так, згенерувати"
             ▼
┌─────────────────────────────────────────┐
│  generatePlaylist(workout, prompt, ...) │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│      PlaylistGenerator                  │
│                                         │
│  1. Інтерпретує prompt:                 │
│     "нічний драйв, synthwave"           │
│     → додає "synthwave" до genres       │
│     → зміщує energy: 0.6 → 0.7          │
│                                         │
│  2. Будує сегменти workout              │
│  3. Викликає Spotify API                │
│  4. Формує назву плейлиста з prompt     │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Spotify Playlist створено 🎵           │
│  • Зберігається в Supabase              │
│  • Повертається у Frontend              │
└─────────────────────────────────────────┘
             │
             ▼
👤 User бачить плейлист з треками + посилання Spotify
```

1. Після збирання базових параметрів WorkoutBuilder питає про додаткові музичні побажання (атмосфера, mood, виконавці). Відповідь зберігається у `collected_parameters["prompt"]` та маркер `_prompt_checked`.
2. Коли воркаут створено, `prompt` потрапляє в `workout.prompt` і прокидується у фронтенд.
3. На фронті `useChat` синхронізує `prompt` з `WorkoutSettings`, тож при генерації плейлистів (`generatePlaylist`, `generateVariants`) значення передається в API.
4. `PlaylistGenerator` використовує `prompt` для:
   - Підсилення жанрових ваг (`_infer_prompt_genres`).
   - Підбору енергії/BPM (`_apply_prompt_energy_bias`).
   - Формування назви/опису плейлиста (HR зони, жанри, prompt-snippet + емодзі).

---

## 5. Frontend Touchpoints

| Компонент       | Опис                                                                                                                   |
| --------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `useChat` hook  | Веде чергу повідомлень, зберігає `_metadata` (needsClarification/isComplete), синхронізує `activeWorkout` та `prompt`. |
| `ChatPage`      | Обробляє CTA “Так, згенерувати плейлист”, показує історичні воркаути, активує генерацію варіантів.                     |
| `MessageBubble` | Відображає тренування, плейлисти, нові стилі повідомлень (білий текст + тінь) та таймстемпи.                           |
| `InputBar`      | Фокусується після кожної відправки, забезпечуючи безперервний діалог.                                                  |

---

## 6. End-to-End Data Flow

### 🔄 Повний цикл: від повідомлення до плейлиста

```
КРОК 1: Створення Workout
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 User: "хочу легку пробіжку 30 хв під рок"
  │
  ▼
┌──────────────────────────────────────┐
│  Frontend (ChatPage)                 │
│  • useChat.sendMessage()             │
└──────────────┬───────────────────────┘
               │
               │ POST /api/v1/chat/message
               │ { user_id, message }
               ▼
┌──────────────────────────────────────┐
│  Backend API                         │
│  • /chat/message endpoint            │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  SupervisorAgent                     │
│  • Завантажує ConversationState      │
│  • Делегує WorkoutBuilder            │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  WorkoutBuilder (LangChain)          │
│  • extract_workout_parameters        │
│    → duration: 30, intensity: low,   │
│      genres: ["rock"]                │
│  • Формує відповідь: "Супер! Маєш    │
│    ще побажання до атмосфери?"       │
└──────────────┬───────────────────────┘
               │
               │ ConversationUpdate
               ▼
┌──────────────────────────────────────┐
│  SupervisorAgent                     │
│  • Зберігає у Supabase               │
│  • Повертає ChatResponse             │
└──────────────┬───────────────────────┘
               │
               │ ChatResponse
               │ { message, workout, needs_clarification }
               ▼
┌──────────────────────────────────────┐
│  Frontend                            │
│  • Рендерить відповідь AI            │
│  • Зберігає activeWorkout            │
└──────────────────────────────────────┘
               │
               ▼
👤 User бачить: "Супер! Маєш ще побажання до атмосфери?"


КРОК 2: Підтвердження та створення
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 User: "нічний вайб"
  │
  │ (повторюється процес з Кроку 1)
  ▼
WorkoutBuilder:
  • Зберігає prompt: "нічний вайб"
  • Питає: "Створюємо воркаут?"

👤 User: "так"
  │
  ▼
WorkoutBuilder:
  • create_workout_from_params
  • Workout створено в БД ✅
  │
  ▼
Frontend:
  • Показує: "✅ Воркаут створено!"
  • Кнопка: "Так, згенерувати плейлист" 🎵


КРОК 3: Генерація плейлиста
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 User: [клік "Так, згенерувати плейлист"]
  │
  ▼
┌──────────────────────────────────────┐
│  Frontend                            │
│  • generatePlaylist()                │
│  • Передає: workout, prompt, genres  │
└──────────────┬───────────────────────┘
               │
               │ POST /api/v1/playlists/generate
               │ { workout, user_preferences, prompt }
               ▼
┌──────────────────────────────────────┐
│  Backend API                         │
│  • /playlists/generate endpoint      │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  PlaylistGenerator                   │
│  • Будує workout profile (сегменти)  │
│  • Застосовує prompt bias            │
│  • Викликає Spotify API              │
│    (recommendations + create)        │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  Spotify API                         │
│  • Recommendations (BPM, energy)     │
│  • Create Playlist                   │
│  • Add Tracks                        │
└──────────────┬───────────────────────┘
               │
               │ Playlist створено
               ▼
┌──────────────────────────────────────┐
│  Backend                             │
│  • Зберігає playlist у Supabase      │
│  • Повертає PlaylistResponse         │
└──────────────┬───────────────────────┘
               │
               │ PlaylistResponse
               │ { playlist_id, spotify_url, tracks }
               ▼
┌──────────────────────────────────────┐
│  Frontend                            │
│  • Додає playlist як нове повідомл.  │
│  • Показує треки + Spotify link      │
└──────────────────────────────────────┘
               │
               ▼
👤 User бачить:
   🎵 Плейлист готовий! (15 треків, 30 хв)
   [Відкрити в Spotify] 🔗
```

---

## 7. Stack Snapshot

- **Backend**: Python 3.11+, FastAPI, LangChain, Supabase Python client, Spotipy, asyncio.
- **Frontend**: React 18, Vite 5, TypeScript, Tailwind CSS, Zustand, Vitest.
- **Infra/Deploy**: Railway (Nixpacks build, `apps/web/nixpacks.toml`), Supabase (DB/Auth/File storage), OpenAI API (моделі задаються `.env`: `OPENAI_MODEL_PARSER`, `OPENAI_MODEL_CONVERSATION`, `OPENAI_MODEL_SUPERVISOR`).

---

## 8. Додаткові ресурси

- **[AI Conversation Architecture](./AI_CONVERSATION_ARCHITECTURE.md)** — детальна документація LangChain агентів, промптів, conversation state machine
- **[Root README](../README.md)** — швидкий старт, команди для тестування та деплою
- **[Backend ENV Setup](../apps/backend/ENV_SETUP_GUIDE.md)** — налаштування змінних середовища для OpenAI, Spotify, Supabase
- **[Backend README](../apps/backend/README.md)** — специфіка запуску та структура backend
- **[Web README](../apps/web/README.md)** — специфіка frontend застосунку

---

> **Останнє оновлення**: 19 листопада 2025
> **Версія документації**: 2.1
> **Автор**: RunBeat Team
