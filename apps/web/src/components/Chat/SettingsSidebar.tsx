import { useState, useEffect } from 'react';
import type { WorkoutSettings, IntervalStage } from '../../types/settings';
import { api } from '../../services/api';

interface SettingsSidebarProps {
  settings: WorkoutSettings;
  onSettingsChange: (settings: WorkoutSettings) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  userId?: string;
  onSave?: () => void; // Callback after successful save
  onWorkoutActivated?: (workout: {
    id?: string; // Workout ID if saved
    type: string;
    duration_minutes: number;
    intensity: string;
    hr_zones: number[];
  }) => void; // Callback when workout is saved and should be activated
}

const WORKOUT_TYPES: Array<{ value: WorkoutSettings['type']; label: string }> =
  [
    { value: 'steady', label: 'Стабільна' },
    { value: 'progressive', label: 'Прогресивна' },
    { value: 'intervals', label: 'Інтервальна' },
    { value: 'fartlek', label: 'Фартлек' },
  ];

const INTENSITIES: Array<{
  value: WorkoutSettings['intensity'];
  label: string;
}> = [
  { value: 'low', label: 'Легка' },
  { value: 'moderate', label: 'Середня' },
  { value: 'high', label: 'Висока' },
];

const MUSIC_GENRES = [
  'Pop',
  'Rock',
  'Electronic',
  'Hip-Hop',
  'R&B',
  'Country',
  'Jazz',
  'Classical',
  'Reggae',
  'Metal',
  'Indie',
  'Alternative',
  'Dance',
  'House',
  'Techno',
];

export function SettingsSidebar({
  settings,
  onSettingsChange,
  collapsed = false,
  onToggleCollapse,
  userId,
  onSave,
  onWorkoutActivated,
}: SettingsSidebarProps) {
  const [localSettings, setLocalSettings] = useState<WorkoutSettings>(settings);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setLocalSettings(settings);
  }, [settings]);

  const updateSettings = (updates: Partial<WorkoutSettings>) => {
    const newSettings = { ...localSettings, ...updates };
    setLocalSettings(newSettings);
    onSettingsChange(newSettings);
  };

  const addIntervalStage = () => {
    const newStage: IntervalStage = {
      id: Date.now().toString(),
      name: `Етап ${(localSettings.intervalStages?.length || 0) + 1}`,
      durationMinutes: 5,
      hrZone: [130, 150],
      bpmRange: [140, 160],
    };
    updateSettings({
      intervalStages: [...(localSettings.intervalStages || []), newStage],
    });
  };

  const updateIntervalStage = (id: string, updates: Partial<IntervalStage>) => {
    if (!localSettings.intervalStages) return;
    const updated = localSettings.intervalStages.map((stage) =>
      stage.id === id ? { ...stage, ...updates } : stage
    );
    updateSettings({ intervalStages: updated });
  };

  const removeIntervalStage = (id: string) => {
    if (!localSettings.intervalStages) return;
    const filtered = localSettings.intervalStages.filter(
      (stage) => stage.id !== id
    );
    updateSettings({ intervalStages: filtered });
  };

  const toggleGenre = (genre: string) => {
    const genres = localSettings.genres.includes(genre)
      ? localSettings.genres.filter((g) => g !== genre)
      : [...localSettings.genres, genre];
    updateSettings({ genres });
  };

  const handleSave = async () => {
    if (!userId) {
      console.error('Помилка: користувач не авторизований');
      return;
    }

    setSaving(true);
    try {
      const workout = {
        type: localSettings.type,
        duration_minutes: localSettings.durationMinutes,
        intensity: localSettings.intensity,
        hr_zones: localSettings.hrZones,
      };

      // Prepare interval stages for backend
      const intervalStages = localSettings.intervalStages?.map((stage) => ({
        name: stage.name,
        duration_minutes: stage.durationMinutes,
        hr_zone: stage.hrZone,
        bpm_range: stage.bpmRange,
      }));

      const savedWorkout = await api.createWorkout(
        workout,
        userId,
        localSettings.genres,
        intervalStages,
        localSettings.prompt
      );
      if (onSave) {
        onSave();
      }
      // Activate the workout after saving (with saved ID)
      if (onWorkoutActivated) {
        onWorkoutActivated({
          ...workout,
          id: savedWorkout.id, // Include saved workout ID
        });
      }
      // Workout saved successfully - no alert needed
    } catch (error) {
      console.error('Failed to save workout:', error);
      // Error logged to console - no alert shown
    } finally {
      setSaving(false);
    }
  };

  const convertDurationToMinutes = (hours: number, minutes: number) => {
    return hours * 60 + minutes;
  };

  const convertMinutesToHoursMinutes = (totalMinutes: number) => {
    return {
      hours: Math.floor(totalMinutes / 60),
      minutes: totalMinutes % 60,
    };
  };

  const [durationHours, setDurationHours] = useState(
    convertMinutesToHoursMinutes(localSettings.durationMinutes).hours
  );
  const [durationMinutes, setDurationMinutes] = useState(
    convertMinutesToHoursMinutes(localSettings.durationMinutes).minutes
  );

  useEffect(() => {
    const total = convertDurationToMinutes(durationHours, durationMinutes);
    if (total !== localSettings.durationMinutes) {
      updateSettings({ durationMinutes: total });
    }
  }, [durationHours, durationMinutes]);

  if (collapsed) {
    return (
      <div className='w-12 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col h-full items-center py-4 transition-all duration-500 ease-in-out'>
        <button
          onClick={onToggleCollapse}
          className='p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-all duration-200 ease-in-out hover:scale-110'
          title='Розгорнути налаштування'
        >
          <svg
            className='w-5 h-5 text-gray-600 dark:text-gray-400 transition-transform duration-300 ease-in-out'
            fill='none'
            stroke='currentColor'
            viewBox='0 0 24 24'
          >
            <path
              strokeLinecap='round'
              strokeLinejoin='round'
              strokeWidth={2}
              d='M15 19l-7-7 7-7'
            />
          </svg>
        </button>
      </div>
    );
  }

  return (
    <div className='flex-[1.5] bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col h-full overflow-y-auto transition-all duration-500 ease-in-out min-w-0'>
      <div className='p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center transition-all duration-300 ease-in-out'>
        <h2 className='text-lg font-semibold text-gray-900 dark:text-white transition-all duration-300 ease-in-out'>
          Воркаут
        </h2>
        {onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            className='p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-all duration-200 ease-in-out hover:scale-110 active:scale-95'
            title='Згорнути налаштування'
          >
            <svg
              className='w-5 h-5 text-gray-600 dark:text-gray-400 transition-transform duration-300 ease-in-out'
              fill='none'
              stroke='currentColor'
              viewBox='0 0 24 24'
            >
              <path
                strokeLinecap='round'
                strokeLinejoin='round'
                strokeWidth={2}
                d='M9 5l7 7-7 7'
              />
            </svg>
          </button>
        )}
      </div>

      <div className='flex-1 p-4 space-y-6 transition-all duration-300 ease-in-out'>
        {/* Workout Type */}
        <div>
          <label className='block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2'>
            Тип тренування
          </label>
          <div className='grid grid-cols-2 gap-2'>
            {WORKOUT_TYPES.map((type) => (
              <button
                key={type.value}
                onClick={() => updateSettings({ type: type.value })}
                className={`px-3 py-2 text-sm rounded-lg border transition-colors ${
                  localSettings.type === type.value
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'
                }`}
              >
                {type.label}
              </button>
            ))}
          </div>
        </div>

        {/* Duration */}
        <div>
          <label className='block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2'>
            Тривалість
          </label>
          <div className='space-y-3'>
            <div>
              <label className='text-xs text-gray-500 dark:text-gray-400 mb-1 block'>
                Години: {durationHours}
              </label>
              <input
                type='range'
                min='0'
                max='3'
                value={durationHours}
                onChange={(e) => setDurationHours(parseInt(e.target.value))}
                className='w-full'
              />
            </div>
            <div>
              <label className='text-xs text-gray-500 dark:text-gray-400 mb-1 block'>
                Хвилини: {durationMinutes}
              </label>
              <input
                type='range'
                min='0'
                max='59'
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(parseInt(e.target.value))}
                className='w-full'
              />
            </div>
            <p className='text-xs text-gray-500 dark:text-gray-400'>
              Всього: {convertDurationToMinutes(durationHours, durationMinutes)}{' '}
              хв
            </p>
          </div>
        </div>

        {/* Intensity */}
        <div>
          <label className='block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2'>
            Інтенсивність
          </label>
          <div className='flex gap-2'>
            {INTENSITIES.map((intensity) => (
              <button
                key={intensity.value}
                onClick={() => updateSettings({ intensity: intensity.value })}
                className={`flex-1 px-3 py-2 text-sm rounded-lg border transition-colors ${
                  localSettings.intensity === intensity.value
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'
                }`}
              >
                {intensity.label}
              </button>
            ))}
          </div>
        </div>

        {/* Heart Rate Zones */}
        <div>
          <label className='block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2'>
            Частота серцебиття
          </label>
          <div className='space-y-2'>
            <div>
              <label className='text-xs text-gray-500 dark:text-gray-400 mb-1 block'>
                Мінімум: {localSettings.hrZones[0]} уд/хв
              </label>
              <input
                type='range'
                min='60'
                max='200'
                value={localSettings.hrZones[0]}
                onChange={(e) =>
                  updateSettings({
                    hrZones: [
                      parseInt(e.target.value),
                      localSettings.hrZones[1],
                    ],
                  })
                }
                className='w-full'
              />
            </div>
            <div>
              <label className='text-xs text-gray-500 dark:text-gray-400 mb-1 block'>
                Максимум: {localSettings.hrZones[1]} уд/хв
              </label>
              <input
                type='range'
                min='60'
                max='200'
                value={localSettings.hrZones[1]}
                onChange={(e) =>
                  updateSettings({
                    hrZones: [
                      localSettings.hrZones[0],
                      parseInt(e.target.value),
                    ],
                  })
                }
                className='w-full'
              />
            </div>
            <p className='text-xs text-gray-500 dark:text-gray-400'>
              Діапазон: {localSettings.hrZones[0]} - {localSettings.hrZones[1]}{' '}
              уд/хв
            </p>
          </div>
        </div>

        {/* Interval Stages (only for intervals type) */}
        {localSettings.type === 'intervals' && (
          <div>
            <div className='flex justify-between items-center mb-2'>
              <label className='block text-sm font-medium text-gray-700 dark:text-gray-300'>
                Етапи тренування
              </label>
              <button
                onClick={addIntervalStage}
                className='text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700'
              >
                + Додати етап
              </button>
            </div>
            <div className='space-y-3'>
              {localSettings.intervalStages?.map((stage) => (
                <div
                  key={stage.id}
                  className='p-3 bg-gray-50 dark:bg-gray-700 rounded-lg'
                >
                  <div className='flex justify-between items-start mb-2'>
                    <input
                      type='text'
                      value={stage.name}
                      onChange={(e) =>
                        updateIntervalStage(stage.id, {
                          name: e.target.value,
                        })
                      }
                      className='flex-1 text-sm font-medium bg-transparent border-b border-gray-300 dark:border-gray-600 focus:outline-none focus:border-blue-500'
                      placeholder='Назва етапу'
                    />
                    <button
                      onClick={() => removeIntervalStage(stage.id)}
                      className='ml-2 text-red-500 hover:text-red-700'
                    >
                      <svg
                        className='w-4 h-4'
                        fill='none'
                        stroke='currentColor'
                        viewBox='0 0 24 24'
                      >
                        <path
                          strokeLinecap='round'
                          strokeLinejoin='round'
                          strokeWidth={2}
                          d='M6 18L18 6M6 6l12 12'
                        />
                      </svg>
                    </button>
                  </div>
                  <div className='space-y-2 text-xs'>
                    <div>
                      <label className='text-gray-500 dark:text-gray-400'>
                        Тривалість: {stage.durationMinutes} хв
                      </label>
                      <input
                        type='range'
                        min='1'
                        max='30'
                        value={stage.durationMinutes}
                        onChange={(e) =>
                          updateIntervalStage(stage.id, {
                            durationMinutes: parseInt(e.target.value),
                          })
                        }
                        className='w-full'
                      />
                    </div>
                    <div>
                      <label className='text-gray-500 dark:text-gray-400'>
                        ЧСС: {stage.hrZone[0]} - {stage.hrZone[1]} уд/хв
                      </label>
                      <div className='flex gap-2'>
                        <input
                          type='range'
                          min='60'
                          max='200'
                          value={stage.hrZone[0]}
                          onChange={(e) =>
                            updateIntervalStage(stage.id, {
                              hrZone: [
                                parseInt(e.target.value),
                                stage.hrZone[1],
                              ],
                            })
                          }
                          className='flex-1'
                        />
                        <input
                          type='range'
                          min='60'
                          max='200'
                          value={stage.hrZone[1]}
                          onChange={(e) =>
                            updateIntervalStage(stage.id, {
                              hrZone: [
                                stage.hrZone[0],
                                parseInt(e.target.value),
                              ],
                            })
                          }
                          className='flex-1'
                        />
                      </div>
                    </div>
                    <div>
                      <label className='text-gray-500 dark:text-gray-400'>
                        BPM: {stage.bpmRange[0]} - {stage.bpmRange[1]}
                      </label>
                      <div className='flex gap-2'>
                        <input
                          type='range'
                          min='60'
                          max='200'
                          value={stage.bpmRange[0]}
                          onChange={(e) =>
                            updateIntervalStage(stage.id, {
                              bpmRange: [
                                parseInt(e.target.value),
                                stage.bpmRange[1],
                              ],
                            })
                          }
                          className='flex-1'
                        />
                        <input
                          type='range'
                          min='60'
                          max='200'
                          value={stage.bpmRange[1]}
                          onChange={(e) =>
                            updateIntervalStage(stage.id, {
                              bpmRange: [
                                stage.bpmRange[0],
                                parseInt(e.target.value),
                              ],
                            })
                          }
                          className='flex-1'
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              {(!localSettings.intervalStages ||
                localSettings.intervalStages.length === 0) && (
                <p className='text-xs text-gray-500 dark:text-gray-400 text-center py-4'>
                  Немає етапів. Додайте етап для інтервального тренування.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Music Genres */}
        <div>
          <label className='block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2'>
            Жанри музики
          </label>
          <div className='flex flex-wrap gap-2'>
            {MUSIC_GENRES.map((genre) => (
              <button
                key={genre}
                onClick={() => toggleGenre(genre)}
                className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                  localSettings.genres.includes(genre)
                    ? 'bg-green-600 text-white border-green-600'
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'
                }`}
              >
                {genre}
              </button>
            ))}
          </div>
        </div>

        {/* Prompt Field */}
        <div>
          <label className='block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2'>
            Промпт (опціонально)
          </label>
          <textarea
            value={localSettings.prompt || ''}
            onChange={(e) => updateSettings({ prompt: e.target.value })}
            placeholder='Опиши додаткові побажання до музики, наприклад: "енергійна музика для ранкового бігу", "релаксуючі мелодії", "улюблені треки 2024 року" тощо...'
            className='w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none'
            rows={4}
          />
          <p className='text-xs text-gray-500 dark:text-gray-400 mt-1'>
            Цей промпт допоможе уточнити пошук та генерацію варіантів плейлистів
          </p>
        </div>
      </div>

      {/* Save Button */}
      <div className='p-4 border-t border-gray-200 dark:border-gray-700'>
        <button
          onClick={handleSave}
          disabled={saving || !userId}
          className='w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium'
        >
          {saving ? 'Збереження...' : 'Зберегти'}
        </button>
      </div>
    </div>
  );
}
