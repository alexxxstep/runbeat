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
    const updatedStages = [...(localSettings.intervalStages || []), newStage];

    // Calculate total duration from all stages
    const totalDuration = updatedStages.reduce(
      (sum, stage) => sum + stage.durationMinutes,
      0
    );

    updateSettings({
      intervalStages: updatedStages,
      durationMinutes: totalDuration,
    });
  };

  const updateIntervalStage = (id: string, updates: Partial<IntervalStage>) => {
    if (!localSettings.intervalStages) return;
    const updated = localSettings.intervalStages.map((stage) =>
      stage.id === id ? { ...stage, ...updates } : stage
    );

    // Calculate total duration from all stages
    const totalDuration = updated.reduce(
      (sum, stage) => sum + stage.durationMinutes,
      0
    );

    updateSettings({
      intervalStages: updated,
      durationMinutes: totalDuration,
    });
  };

  const removeIntervalStage = (id: string) => {
    if (!localSettings.intervalStages) return;
    const filtered = localSettings.intervalStages.filter(
      (stage) => stage.id !== id
    );

    // Calculate total duration from remaining stages
    const totalDuration = filtered.reduce(
      (sum, stage) => sum + stage.durationMinutes,
      0
    );

    updateSettings({
      intervalStages: filtered,
      durationMinutes: totalDuration,
    });
  };

  const duplicateIntervalStage = (id: string) => {
    if (!localSettings.intervalStages) return;
    const stageIndex = localSettings.intervalStages.findIndex(
      (stage) => stage.id === id
    );
    if (stageIndex === -1) return;

    const originalStage = localSettings.intervalStages[stageIndex];
    const duplicatedStage: IntervalStage = {
      ...originalStage,
      id: Date.now().toString(),
      name: `${originalStage.name} (копія)`,
    };

    const newStages = [...localSettings.intervalStages];
    newStages.splice(stageIndex + 1, 0, duplicatedStage);

    // Calculate total duration from all stages
    const totalDuration = newStages.reduce(
      (sum, stage) => sum + stage.durationMinutes,
      0
    );

    updateSettings({
      intervalStages: newStages,
      durationMinutes: totalDuration,
    });
  };

  const moveIntervalStageUp = (id: string) => {
    if (!localSettings.intervalStages) return;
    const stageIndex = localSettings.intervalStages.findIndex(
      (stage) => stage.id === id
    );
    if (stageIndex <= 0) return; // Already at the top or not found

    const newStages = [...localSettings.intervalStages];
    [newStages[stageIndex - 1], newStages[stageIndex]] = [
      newStages[stageIndex],
      newStages[stageIndex - 1],
    ];
    updateSettings({ intervalStages: newStages });
  };

  const moveIntervalStageDown = (id: string) => {
    if (!localSettings.intervalStages) return;
    const stageIndex = localSettings.intervalStages.findIndex(
      (stage) => stage.id === id
    );
    if (
      stageIndex === -1 ||
      stageIndex >= localSettings.intervalStages.length - 1
    )
      return; // Already at the bottom or not found

    const newStages = [...localSettings.intervalStages];
    [newStages[stageIndex], newStages[stageIndex + 1]] = [
      newStages[stageIndex + 1],
      newStages[stageIndex],
    ];
    updateSettings({ intervalStages: newStages });
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

  // Update duration sliders when total duration changes (e.g., from interval stages)
  useEffect(() => {
    const { hours, minutes } = convertMinutesToHoursMinutes(
      localSettings.durationMinutes
    );
    setDurationHours(hours);
    setDurationMinutes(minutes);
  }, [localSettings.durationMinutes]);

  useEffect(() => {
    const total = convertDurationToMinutes(durationHours, durationMinutes);
    if (total !== localSettings.durationMinutes) {
      updateSettings({ durationMinutes: total });
    }
  }, [durationHours, durationMinutes]);

  const sidebarWidthClass = collapsed ? 'w-12' : 'w-full';
  const contentOpacityClass = collapsed ? 'opacity-0' : 'opacity-100';
  const contentVisibilityClass = collapsed ? 'invisible' : 'visible';

  return (
    <div
      className={`bg-app-surface border-l border-app-border flex flex-col h-full transition-all duration-300 ease-in-out ${sidebarWidthClass}`}
    >
      {/* Header */}
      <div
        className={`${
          collapsed ? 'p-2' : 'p-4'
        } border-b border-app-border flex ${
          collapsed ? 'justify-center' : 'justify-between'
        } items-center flex-shrink-0 relative`}
      >
        {!collapsed && (
          <h2
            className={`text-title-2 font-display font-bold text-app-text transition-opacity duration-300 ${contentOpacityClass} ${contentVisibilityClass}`}
          >
            Воркаут
          </h2>
        )}
        <button
          onClick={onToggleCollapse}
          className={`${
            collapsed ? 'p-2 w-full flex justify-center' : 'p-2'
          } hover:bg-app-surface-light rounded-full transition-all duration-300 ease-in-out flex-shrink-0 z-10`}
          title={collapsed ? 'Розгорнути' : 'Згорнути'}
        >
          <svg
            className={`${
              collapsed ? 'w-6 h-6' : 'w-5 h-5'
            } text-app-text-secondary transform transition-transform duration-300 ${
              collapsed ? 'rotate-0' : 'rotate-180'
            }`}
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

      {/* Main Content */}
      <div
        className={`flex-1 overflow-y-auto overflow-x-hidden p-4 space-y-6 transition-opacity duration-300 ${contentOpacityClass} ${contentVisibilityClass}`}
      >
        {/* Intensity */}
        <div>
          <label className='block text-subhead font-semibold text-app-text mb-3'>
            Інтенсивність
          </label>
          <div className='flex gap-2'>
            {INTENSITIES.map((intensity) => (
              <button
                key={intensity.value}
                onClick={() => updateSettings({ intensity: intensity.value })}
                className={`flex-1 px-3 py-2.5 text-subhead rounded-xl border transition-colors ${
                  localSettings.intensity === intensity.value
                    ? 'bg-app-accent text-white border-app-accent'
                    : 'bg-app-surface-light text-app-text border-app-border hover:bg-app-surface'
                }`}
              >
                {intensity.label}
              </button>
            ))}
          </div>
        </div>

        {/* Duration */}
        <div>
          <label className='block text-subhead font-semibold text-app-text mb-3'>
            Тривалість
          </label>
          <div className='space-y-4'>
            <div>
              <label className='text-caption text-app-text-secondary mb-2 block'>
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
              <label className='text-caption text-app-text-secondary mb-2 block'>
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
            <p className='text-subhead text-app-text-secondary'>
              Всього: {convertDurationToMinutes(durationHours, durationMinutes)}{' '}
              хв
            </p>
          </div>
        </div>

        {/* Music Genres */}
        <div>
          <label className='block text-subhead font-semibold text-app-text mb-3'>
            Жанри музики
          </label>
          <div className='flex flex-wrap gap-2'>
            {MUSIC_GENRES.map((genre) => (
              <button
                key={genre}
                onClick={() => toggleGenre(genre)}
                className={`px-3 py-1.5 text-caption rounded-full border transition-colors ${
                  localSettings.genres.includes(genre)
                    ? 'bg-app-accent text-white border-app-accent'
                    : 'bg-app-surface-light text-app-text border-app-border hover:bg-app-surface'
                }`}
              >
                {genre}
              </button>
            ))}
          </div>
        </div>

        {/* Heart Rate Zones */}
        <div>
          <label className='block text-subhead font-semibold text-app-text mb-3'>
            Частота серцебиття
          </label>
          <div className='space-y-4'>
            <div>
              <label className='text-caption text-app-text-secondary mb-2 block'>
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
              <label className='text-caption text-app-text-secondary mb-2 block'>
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
            <p className='text-subhead text-app-text-secondary'>
              Діапазон: {localSettings.hrZones[0]} - {localSettings.hrZones[1]}{' '}
              уд/хв
            </p>
          </div>
        </div>

        {/* Workout Type */}
        <div>
          <label className='block text-subhead font-semibold text-app-text mb-3'>
            Тип тренування
          </label>
          <div className='grid grid-cols-2 gap-2'>
            {WORKOUT_TYPES.map((type) => (
              <button
                key={type.value}
                onClick={() => updateSettings({ type: type.value })}
                className={`px-3 py-2.5 text-subhead rounded-xl border transition-colors ${
                  localSettings.type === type.value
                    ? 'bg-app-accent text-white border-app-accent'
                    : 'bg-app-surface-light text-app-text border-app-border hover:bg-app-surface'
                }`}
              >
                {type.label}
              </button>
            ))}
          </div>
        </div>

        {/* Interval Stages (only for intervals type) */}
        {localSettings.type === 'intervals' && (
          <div>
            <div className='flex justify-between items-center mb-3'>
              <div>
                <label className='block text-subhead font-semibold text-app-text'>
                  Етапи тренування
                </label>
                {localSettings.intervalStages &&
                  localSettings.intervalStages.length > 0 && (
                    <p className='text-caption text-app-text-secondary mt-1'>
                      Загальна тривалість:{' '}
                      {localSettings.intervalStages.reduce(
                        (sum, stage) => sum + stage.durationMinutes,
                        0
                      )}{' '}
                      хв
                    </p>
                  )}
              </div>
              <button
                onClick={addIntervalStage}
                className='text-caption px-3 py-1.5 bg-app-accent text-white rounded-xl hover:bg-app-accent-hover transition-colors'
              >
                + Додати етап
              </button>
            </div>
            <div className='space-y-3'>
              {localSettings.intervalStages?.map((stage, index, array) => (
                <div
                  key={stage.id}
                  className='p-4 bg-app-surface-light rounded-xl border border-app-border'
                >
                  <div className='flex justify-between items-start mb-3'>
                    <input
                      type='text'
                      value={stage.name}
                      onChange={(e) =>
                        updateIntervalStage(stage.id, {
                          name: e.target.value,
                        })
                      }
                      className='flex-1 text-body font-medium bg-transparent border-b border-app-border focus:outline-none focus:border-app-accent text-app-text placeholder-app-text-tertiary'
                      placeholder='Назва етапу'
                    />
                    <div className='flex items-center gap-2'>
                      <button
                        onClick={() => moveIntervalStageUp(stage.id)}
                        disabled={index === 0}
                        className={`transition-colors ${
                          index === 0
                            ? 'text-app-text-tertiary cursor-not-allowed'
                            : 'text-app-text-secondary hover:text-app-accent'
                        }`}
                        title='Перемістити вгору'
                      >
                        <svg
                          className='w-5 h-5'
                          fill='none'
                          stroke='currentColor'
                          viewBox='0 0 24 24'
                        >
                          <path
                            strokeLinecap='round'
                            strokeLinejoin='round'
                            strokeWidth={2}
                            d='M5 15l7-7 7 7'
                          />
                        </svg>
                      </button>
                      <button
                        onClick={() => moveIntervalStageDown(stage.id)}
                        disabled={index === array.length - 1}
                        className={`transition-colors ${
                          index === array.length - 1
                            ? 'text-app-text-tertiary cursor-not-allowed'
                            : 'text-app-text-secondary hover:text-app-accent'
                        }`}
                        title='Перемістити вниз'
                      >
                        <svg
                          className='w-5 h-5'
                          fill='none'
                          stroke='currentColor'
                          viewBox='0 0 24 24'
                        >
                          <path
                            strokeLinecap='round'
                            strokeLinejoin='round'
                            strokeWidth={2}
                            d='M19 9l-7 7-7-7'
                          />
                        </svg>
                      </button>
                      <button
                        onClick={() => duplicateIntervalStage(stage.id)}
                        className='text-app-accent hover:text-app-accent-hover transition-colors'
                        title='Копіювати етап'
                      >
                        <svg
                          className='w-5 h-5'
                          fill='none'
                          stroke='currentColor'
                          viewBox='0 0 24 24'
                        >
                          <path
                            strokeLinecap='round'
                            strokeLinejoin='round'
                            strokeWidth={2}
                            d='M12 4v16m8-8H4'
                          />
                        </svg>
                      </button>
                      <button
                        onClick={() => removeIntervalStage(stage.id)}
                        className='text-red-500 hover:text-red-400 transition-colors'
                        title='Видалити етап'
                      >
                        <svg
                          className='w-5 h-5'
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
                  </div>
                  <div className='space-y-4 text-subhead'>
                    <div>
                      <label className='text-caption text-app-text-secondary mb-2 block'>
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
                      <label className='text-caption text-app-text-secondary mb-2 block'>
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
                      <label className='text-caption text-app-text-secondary mb-2 block'>
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
                <p className='text-body text-app-text-tertiary text-center py-4'>
                  Немає етапів. Додайте етап для інтервального тренування.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Prompt Field */}
        <div>
          <label className='block text-subhead font-semibold text-app-text mb-3'>
            Промпт (опціонально)
          </label>
          <textarea
            value={localSettings.prompt || ''}
            onChange={(e) => updateSettings({ prompt: e.target.value })}
            placeholder='Опиши додаткові побажання до музики, наприклад: "енергійна музика для ранкового бігу", "релаксуючі мелодії", "улюблені треки 2024 року" тощо...'
            className='w-full px-4 py-3 text-body border border-app-border rounded-xl bg-app-surface-light text-app-text placeholder-app-text-tertiary focus:outline-none focus:ring-2 focus:ring-app-accent focus:border-transparent resize-none'
            rows={4}
          />
          <p className='text-caption text-app-text-tertiary mt-2'>
            Цей промпт допоможе уточнити пошук та генерацію варіантів плейлистів
          </p>
        </div>
      </div>

      {/* Save Button */}
      <div
        className={`p-4 border-t border-app-border flex-shrink-0 transition-opacity duration-300 ${contentOpacityClass} ${contentVisibilityClass}`}
      >
        <button
          onClick={handleSave}
          disabled={saving || !userId}
          className='w-full px-4 py-3 bg-app-accent text-white rounded-xl hover:bg-app-accent-hover disabled:bg-app-surface disabled:text-app-text-tertiary disabled:cursor-not-allowed transition-colors font-semibold text-body'
        >
          {saving ? 'Збереження...' : 'Зберегти'}
        </button>
      </div>
    </div>
  );
}
