# RunBeat Architecture Overview

Актуальний опис цільової архітектури RunBeat (листопад 2025). Документ сфокусований лише на компонентах, які визначають архітектуру системи. Для деталізації розмовного флоу та промптів дивись `AI_CONVERSATION_ARCHITECTURE.md`.

---

## 1. High-level View

```
User → React/Vite SPA → FastAPI backend → Supabase (Postgres)
                               │
                               ├─ SupervisorAgent ─▶ WorkoutBuilder (LangChain)
                               │            │
                               │            ├─ extract_workout_parameters tool
                               │            └─ create_workout_from_params tool
                               │
                               ├─ PlaylistGenerator ─▶ Spotify API
                               └─ ConversationService / Logging
```

- **Frontend**: React 18 + Vite, Tailwind UI, Zustand store (`useChat`) для повідомлень та стану воркаутів.
- **Backend**: FastAPI, asyncio, Supabase client, LangChain agents, чіткі Pydantic V2 схеми.
- **AI**: Supervisor + WorkoutBuilder агенти, що керують збором параметрів тренування, опціональним `prompt` і створенням воркаута.
- **Інтеграції**: Spotify (playlists & recommendations), Supabase (DB/auth), OpenAI (GPT‑4/4o, моделі з `.env`).

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

1. **User input** → `sendMessage` (frontend).
2. **Backend**: `/api/v1/chat` → Supervisor → WorkoutBuilder. Агент збирає параметри, логуючи кожний крок.
3. **Confirmation**: користувач підтверджує → агент/tool створює воркаут → Supervisor очищає стан, відповідає у чат.
4. **Playlist CTA**: фронтенд показує кнопку. За потреби можна активувати історичний воркаут (кнопка з’являється знову).
5. **Playlist API**: `generatePlaylist` або `preview-variants` → `PlaylistGenerator` будує сегменти з урахуванням `prompt`, створює плейлист у Spotify та Supabase.
6. **UI update**: плейлист додається як нове повідомлення з треками, посиланням та CTA.

---

## 7. Stack Snapshot

- **Backend**: Python 3.11+, FastAPI, LangChain, Supabase Python client, Spotipy, asyncio.
- **Frontend**: React 18, Vite 5, TypeScript, Tailwind CSS, Zustand, Vitest.
- **Infra/Deploy**: Railway (Nixpacks build, `apps/web/nixpacks.toml`), Supabase (DB/Auth/File storage), OpenAI API (моделі задаються `.env`: `OPENAI_MODEL_PARSER`, `OPENAI_MODEL_CONVERSATION`, `OPENAI_MODEL_SUPERVISOR`).

---

## 8. Пов’язані документи

- `AI_CONVERSATION_ARCHITECTURE.md` — поглиблені деталі промптів, станів та логів.
- `README.md` в корені — загальний огляд проєкту та операційні інструкції.

> Останнє оновлення: **19 листопада 2025**
