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

  const sidebarWidthClass = collapsed ? 'w-12' : 'w-full';
  const contentOpacityClass = collapsed ? 'opacity-0' : 'opacity-100';
  const contentVisibilityClass = collapsed ? 'invisible' : 'visible';

  return (
    <div
      className={`bg-track-dark border-l border-track-line flex flex-col h-full transition-all duration-300 ease-in-out ${sidebarWidthClass}`}
    >
      {/* Header */}
      <div className={`${collapsed ? 'p-2' : 'p-4'} border-b border-track-line flex ${collapsed ? 'justify-center' : 'justify-between'} items-center flex-shrink-0 glow-border-dim`}>
        <h2
          className={`text-lg font-display font-semibold led-text transition-opacity duration-300 ${contentOpacityClass} ${contentVisibilityClass}`}
        >
          ВОРКАУТ
        </h2>
        <button
          onClick={onToggleCollapse}
          className='p-2 hover:bg-track-line rounded-full transition-transform duration-300 ease-in-out flex-shrink-0'
          title={collapsed ? 'Розгорнути' : 'Згорнути'}
        >
          <svg
            className={`w-5 h-5 text-track-accent transform transition-transform duration-300 ${
              collapsed ? '' : 'rotate-180'
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
        {/* Workout Type */}
        <div>
          <label className='block text-xs md:text-sm font-mono font-medium led-text mb-2'>
            ТИП ТРЕНУВАННЯ
          </label>
          <div className='grid grid-cols-2 gap-2'>
            {WORKOUT_TYPES.map((type) => (
              <button
                key={type.value}
                onClick={() => updateSettings({ type: type.value })}
                className={`px-2 md:px-3 py-1.5 md:py-2 text-xs md:text-sm font-mono rounded-lg border transition-colors ${
                  localSettings.type === type.value
                    ? 'bg-track-accent text-track-dark border-track-accent glow-border'
                    : 'bg-track-darker text-track-accent border-track-line hover:bg-track-line glow-border-dim'
                }`}
              >
                {type.label.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Duration */}
        <div>
          <label className='block text-sm font-mono font-medium led-text mb-2'>
            ТРИВАЛІСТЬ
          </label>
          <div className='space-y-3'>
            <div>
              <label className='text-xs led-text-dim mb-1 block font-mono'>
                ГОДИНИ: {durationHours}
              </label>
              <input
                type='range'
                min='0'
                max='3'
                value={durationHours}
                onChange={(e) => setDurationHours(parseInt(e.target.value))}
                className='w-full accent-track-accent'
              />
            </div>
            <div>
              <label className='text-xs led-text-dim mb-1 block font-mono'>
                ХВИЛИНИ: {durationMinutes}
              </label>
              <input
                type='range'
                min='0'
                max='59'
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(parseInt(e.target.value))}
                className='w-full accent-track-accent'
              />
            </div>
            <p className='text-xs led-text-dim font-mono'>
              ВСЬОГО: {convertDurationToMinutes(durationHours, durationMinutes)} ХВ
            </p>
          </div>
        </div>

        {/* Intensity */}
        <div>
          <label className='block text-sm font-mono font-medium led-text mb-2'>
            ІНТЕНСИВНІСТЬ
          </label>
          <div className='flex gap-2'>
            {INTENSITIES.map((intensity) => (
              <button
                key={intensity.value}
                onClick={() => updateSettings({ intensity: intensity.value })}
                className={`flex-1 px-3 py-2 text-sm font-mono rounded-lg border transition-colors ${
                  localSettings.intensity === intensity.value
                    ? 'bg-track-accent text-track-dark border-track-accent glow-border'
                    : 'bg-track-darker text-track-accent border-track-line hover:bg-track-line glow-border-dim'
                }`}
              >
                {intensity.label.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Heart Rate Zones */}
        <div>
          <label className='block text-sm font-mono font-medium led-text mb-2'>
            ЧАСТОТА СЕРЦЕБИТТЯ
          </label>
          <div className='space-y-2'>
            <div>
              <label className='text-xs led-text-dim mb-1 block font-mono'>
                МІНІМУМ: {localSettings.hrZones[0]} УД/ХВ
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
                className='w-full accent-track-accent'
              />
            </div>
            <div>
              <label className='text-xs led-text-dim mb-1 block font-mono'>
                МАКСИМУМ: {localSettings.hrZones[1]} УД/ХВ
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
                className='w-full accent-track-accent'
              />
            </div>
            <p className='text-xs led-text-dim font-mono'>
              ДІАПАЗОН: {localSettings.hrZones[0]} - {localSettings.hrZones[1]} УД/ХВ
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
          <label className='block text-sm font-mono font-medium led-text mb-2'>
            ЖАНРИ МУЗИКИ
          </label>
          <div className='flex flex-wrap gap-2'>
            {MUSIC_GENRES.map((genre) => (
              <button
                key={genre}
                onClick={() => toggleGenre(genre)}
                className={`px-3 py-1 text-xs font-mono rounded-full border transition-colors ${
                  localSettings.genres.includes(genre)
                    ? 'bg-track-accent text-track-dark border-track-accent glow-border'
                    : 'bg-track-darker text-track-accent border-track-line hover:bg-track-line glow-border-dim'
                }`}
              >
                {genre.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Prompt Field */}
        <div>
          <label className='block text-sm font-mono font-medium led-text mb-2'>
            ПРОМПТ (ОПЦІОНАЛЬНО)
          </label>
          <textarea
            value={localSettings.prompt || ''}
            onChange={(e) => updateSettings({ prompt: e.target.value })}
            placeholder='Опиши додаткові побажання до музики, наприклад: "енергійна музика для ранкового бігу", "релаксуючі мелодії", "улюблені треки 2024 року" тощо...'
            className='w-full px-3 py-2 text-sm font-mono border border-track-line rounded-lg bg-track-darker text-track-accent placeholder-track-accent-dim focus:outline-none focus:ring-2 focus:ring-track-accent focus:border-transparent resize-none glow-border-dim'
            rows={4}
          />
          <p className='text-xs led-text-dim mt-1 font-mono'>
            Цей промпт допоможе уточнити пошук та генерацію варіантів плейлистів
          </p>
        </div>
      </div>

      {/* Save Button */}
      <div
        className={`p-4 border-t border-track-line flex-shrink-0 transition-opacity duration-300 ${contentOpacityClass} ${contentVisibilityClass} glow-border-dim`}
      >
        <button
          onClick={handleSave}
          disabled={saving || !userId}
          className='w-full px-3 md:px-4 py-2 bg-track-accent text-track-dark rounded-lg hover:bg-track-accent-bright disabled:bg-track-line disabled:text-track-accent-dim disabled:cursor-not-allowed transition-colors font-mono font-bold text-sm md:text-base glow-border'
        >
          {saving ? 'ЗБЕРЕЖЕННЯ...' : 'ЗБЕРЕГТИ'}
        </button>
      </div>
    </div>
  );
}
