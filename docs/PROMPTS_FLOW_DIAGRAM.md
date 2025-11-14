# Prompts System - Flow Diagram

**Дата:** 2025-11-14

---

## 🔄 Повний Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER MESSAGE                                  │
│              "Хочу пробігти 30 хв"                              │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              ConversationManager.process_message()               │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              LLMService.parse_workout()                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PromptBuilder.build_messages(task="parse_workout")      │  │
│  │                                                           │  │
│  │  1. build_system_prompt()                                │  │
│  │     ├─ BASE_SYSTEM_PROMPT                                │  │
│  │     └─ WORKOUT_EXPERT_SYSTEM ✅                          │  │
│  │                                                           │  │
│  │  2. build_workout_parsing_prompt()                       │  │
│  │     ├─ Conversation history                              │  │
│  │     ├─ User message                                      │  │
│  │     ├─ Output format (JSON)                              │  │
│  │     └─ Examples                                          │  │
│  │                                                           │  │
│  │  Returns: [                                              │  │
│  │    {"role": "system", "content": "..."},                 │  │
│  │    {"role": "user", "content": "..."}                    │  │
│  │  ]                                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                       │                                          │
└───────────────────────┼──────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OpenAI GPT-4 API                              │
│              (structured output: WorkoutIntent)                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              WorkoutIntent                                       │
│  {                                                               │
│    "workout_type": "steady",                                    │
│    "duration_minutes": 30,                                      │
│    "target_bpm_min": 120,                                       │
│    "target_bpm_max": 140,                                       │
│    "confidence": 0.95                                           │
│  }                                                               │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│         ConversationManager._decide_next_action()                │
│                                                                  │
│  if intent_complete:                                            │
│    └─► Generate Playlist                                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              LLMService.generate_playlist()                      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PromptBuilder.build_playlist_generation_prompt()        │  │
│  │                                                           │  │
│  │  1. _build_music_curator_system_prompt()                 │  │
│  │     ├─ MUSIC_CURATOR_SYSTEM ✅                            │  │
│  │     ├─ MUSIC_CURATOR_EXAMPLES                            │  │
│  │     ├─ User preferences                                  │  │
│  │     └─ Learning from previous playlists                  │  │
│  │                                                           │  │
│  │  2. _build_playlist_request_prompt()                     │  │
│  │     ├─ Workout type                                      │  │
│  │     ├─ Duration                                          │  │
│  │     ├─ BPM range                                         │  │
│  │     └─ Energy profile                                    │  │
│  │                                                           │  │
│  │  Returns: [                                              │  │
│  │    {"role": "system", "content": "..."},                 │  │
│  │    {"role": "user", "content": "..."}                    │  │
│  │  ]                                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                       │                                          │
└───────────────────────┼──────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OpenAI GPT-4 API                              │
│            (structured output: PlaylistResponse)                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              PlaylistResponse                                    │
│  {                                                               │
│    "playlist_name": "RunBeat: Steady Run (30 min)",            │
│    "total_tracks": 15,                                          │
│    "tracks": [...],                                             │
│    "bpm_range": [120, 140]                                      │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Компоненти

### 1. PromptBuilder (Оркестратор)

```
PromptBuilder
├── build_system_prompt()
│   ├── BASE_SYSTEM_PROMPT
│   ├── WORKOUT_EXPERT_SYSTEM (якщо include_workout_expert=True)
│   └── MUSIC_CURATOR_SYSTEM (якщо include_music_curator=True)
│
├── build_workout_parsing_prompt()
│   ├── Conversation history
│   ├── User message
│   ├── Output format
│   └── Examples
│
├── build_playlist_generation_prompt()
│   ├── _build_music_curator_system_prompt()
│   └── _build_playlist_request_prompt()
│
└── build_messages()
    └── Комбінує system + user prompts
```

### 2. WorkoutExpert (workout_expert.py)

```
WORKOUT_EXPERT_SYSTEM
├── Heart Rate Zones (Zone 1-5)
├── BPM Mapping
├── Interval Training Principles
├── Workout Types
└── Examples
```

### 3. MusicCurator (music_curator.py)

```
MUSIC_CURATOR_SYSTEM
├── BPM Science
├── Genre Selection
├── Playlist Structure
└── Validation Functions
```

---

## 🎯 Ключові моменти

1. **Модульність:** Кожен компонент має свою відповідальність
2. **Комбінування:** PromptBuilder комбінує компоненти за потреби
3. **Контекст:** User context та conversation state додаються динамічно
4. **Структуровані виходи:** Використовується OpenAI structured outputs

---

## ✅ Результати тестування

```
✅ PromptBuilder створюється успішно
✅ Системний промпт: 4473 символів (містить WORKOUT_EXPERT)
✅ Промпт для парсингу: 1500 символів (містить history + message)
✅ Промпт для генерації: 2 повідомлення (містить MUSIC_CURATOR)
```

---

**Статус:** ✅ Всі компоненти працюють правильно

