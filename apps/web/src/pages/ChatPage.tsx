import { useState } from 'react';
import { useChat } from '../hooks/useChat';
import { useAuth } from '../hooks/useAuth';
import { MessageBubble } from '../components/Chat/MessageBubble';
import { InputBar } from '../components/Chat/InputBar';
import { TypingIndicator } from '../components/Chat/TypingIndicator';
import { ErrorDisplay } from '../components/Shared/ErrorDisplay';
import { PlaylistHistorySidebar } from '../components/Chat/PlaylistHistorySidebar';
import { SettingsSidebar } from '../components/Chat/SettingsSidebar';
import type { WorkoutSettings } from '../types/settings';
import { api } from '../services/api';
import type {
  Workout,
  PlaylistVariantsResponse,
  Track,
  Message,
} from '../types';

export function ChatPage() {
  const { user, spotifyAuthenticated } = useAuth();
  const {
    messages,
    setMessages,
    sendMessage,
    generatePlaylist,
    clearMessages,
    addWorkoutActivationMessage,
    isLoading,
    error,
  } = useChat();
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [workoutSettings, setWorkoutSettings] = useState<WorkoutSettings>({
    type: 'steady',
    durationMinutes: 30,
    intensity: 'moderate',
    hrZones: [110, 180],
    genres: [],
    prompt: '',
  });
  const [historyCollapsed, setHistoryCollapsed] = useState(false);
  const [settingsCollapsed, setSettingsCollapsed] = useState(false);
  const [activeWorkout, setActiveWorkout] = useState<Workout | null>(null);
  const [activeWorkoutId, setActiveWorkoutId] = useState<string | null>(null);
  const [showPlaylistQuestion, setShowPlaylistQuestion] = useState(false);
  const [variants, setVariants] = useState<PlaylistVariantsResponse | null>(
    null
  );
  const [loadingVariants, setLoadingVariants] = useState(false);

  const handleSend = async (text: string) => {
    const workout = await sendMessage(text, user?.id);

    // If workout is ready, show workout info and ask for confirmation
    if (workout && !workout.needs_clarification) {
      // Set active workout and show question
      setActiveWorkout(workout);
      setActiveWorkoutId(null); // New workout from chat, not from history
      addWorkoutActivationMessage(workout);
      setShowPlaylistQuestion(true);
    }
  };

  // This should not be reached if ProtectedRoute is working correctly,
  // but add a safety check just in case
  if (!user || !spotifyAuthenticated) {
    return null;
  }

  return (
    <div className='flex h-screen bg-gray-50 dark:bg-gray-900'>
      {/* History Sidebar - Left */}
      <PlaylistHistorySidebar
        userId={user?.id}
        refreshTrigger={refreshTrigger}
        collapsed={historyCollapsed}
        onToggleCollapse={() => setHistoryCollapsed(!historyCollapsed)}
        onPlaylistClick={(_playlistId, spotifyUrl) => {
          if (spotifyUrl) {
            window.open(spotifyUrl, '_blank');
          }
        }}
        onWorkoutClick={async (workoutId) => {
          try {
            const workout = await api.getWorkout(workoutId, user!.id);
            const workoutData: Workout = {
              type: workout.type as Workout['type'],
              duration_minutes: workout.duration_minutes,
              intensity: workout.intensity as Workout['intensity'],
              hr_zones: workout.hr_zones,
            };
            setActiveWorkout(workoutData);

            // Update workout settings with saved genres and interval_stages
            if (workout.genres && workout.genres.length > 0) {
              setWorkoutSettings((prev) => ({
                ...prev,
                genres: workout.genres || [],
              }));
            }
            if (workout.interval_stages && workout.interval_stages.length > 0) {
              // Convert backend format to frontend format
              const intervalStages = workout.interval_stages.map(
                (stage: any, index: number) => ({
                  id: `stage-${index}`,
                  name: stage.name,
                  durationMinutes: stage.duration_minutes,
                  hrZone: stage.hr_zone,
                  bpmRange: stage.bpm_range,
                })
              );
              setWorkoutSettings((prev) => ({
                ...prev,
                intervalStages: intervalStages,
              }));
            }
            if (workout.prompt) {
              setWorkoutSettings((prev) => ({
                ...prev,
                prompt: workout.prompt || '',
              }));
            } else {
              // Clear prompt if not in saved workout
              setWorkoutSettings((prev) => ({
                ...prev,
                prompt: '',
              }));
            }

            // Add AI message with workout parameters
            addWorkoutActivationMessage(workoutData);
            setShowPlaylistQuestion(true);
          } catch (error) {
            console.error('Failed to load workout:', error);
            alert('Помилка завантаження воркауту');
          }
        }}
      />

      {/* Main Chat Area - Center */}
      <div className='flex-1 flex flex-col bg-white dark:bg-gray-900'>
        {/* Header with Clear Chat button */}
        {messages.length > 0 && (
          <div className='flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'>
            <h1 className='text-xl font-bold text-gray-900 dark:text-white'>
              RunBeat AI
            </h1>
            <button
              onClick={clearMessages}
              className='px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors'
            >
              Очистити чат
            </button>
          </div>
        )}

        <div className='flex-1 overflow-y-auto p-4 space-y-4'>
          {messages.length === 0 && (
            <div className='max-w-3xl mx-auto px-4 py-8'>
              <div className='text-center mb-8'>
                <h1 className='text-3xl font-bold text-gray-900 dark:text-white mb-2'>
                  Привіт! Я RunBeat AI 🎵
                </h1>
                <p className='text-lg text-gray-600 dark:text-gray-400'>
                  Створю ідеальний плейлист для твого тренування
                </p>
              </div>

              <div className='bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg shadow-lg p-6 mb-6 border border-blue-200 dark:border-blue-800'>
                <h2 className='text-2xl font-bold text-gray-900 dark:text-white mb-6 text-center'>
                  📋 Алгоритм роботи
                </h2>

                <div className='space-y-6'>
                  {/* Step 1 */}
                  <div className='bg-white dark:bg-gray-800 rounded-lg p-5 border-l-4 border-blue-500'>
                    <div className='flex items-start gap-4'>
                      <div className='flex-shrink-0 w-10 h-10 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold text-lg'>
                        1
                      </div>
                      <div className='flex-1'>
                        <h3 className='text-lg font-semibold text-gray-900 dark:text-white mb-2'>
                          Створи або вибери воркаут
                        </h3>
                        <p className='text-gray-700 dark:text-gray-300 mb-3'>
                          <strong>Варіант А:</strong> Створи новий воркаут у
                          панелі <strong>WorkoutSettings</strong> (справа):
                        </p>
                        <ul className='list-disc list-inside space-y-1 text-sm text-gray-600 dark:text-gray-400 ml-4 mb-3'>
                          <li>
                            Оберіть тип тренування (стабільна, прогресивна,
                            інтервальна, фартлек)
                          </li>
                          <li>Встановіть тривалість (години та хвилини)</li>
                          <li>
                            Виберіть інтенсивність (легка, середня, висока)
                          </li>
                          <li>
                            Налаштуйте частоту серцебиття (мінімум та максимум)
                          </li>
                          <li>Оберіть жанри музики (опціонально)</li>
                          <li>
                            Натисніть кнопку <strong>"Зберегти"</strong>
                          </li>
                        </ul>
                        <p className='text-gray-700 dark:text-gray-300'>
                          <strong>Варіант Б:</strong> Вибери існуючий воркаут з
                          панелі <strong>Історія</strong> (зліва) - секція
                          "Воркаути"
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Step 2 */}
                  <div className='bg-white dark:bg-gray-800 rounded-lg p-5 border-l-4 border-green-500'>
                    <div className='flex items-start gap-4'>
                      <div className='flex-shrink-0 w-10 h-10 bg-green-500 text-white rounded-full flex items-center justify-center font-bold text-lg'>
                        2
                      </div>
                      <div className='flex-1'>
                        <h3 className='text-lg font-semibold text-gray-900 dark:text-white mb-2'>
                          Активуй воркаут
                        </h3>
                        <p className='text-gray-700 dark:text-gray-300'>
                          Після створення або вибору воркауту, він автоматично
                          активується. У чаті з'явиться картка з параметрами
                          воркауту та питанням:
                          <strong>
                            "Створити під цей воркаут плейлист? Да/Ні"
                          </strong>
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Step 3 */}
                  <div className='bg-white dark:bg-gray-800 rounded-lg p-5 border-l-4 border-purple-500'>
                    <div className='flex items-start gap-4'>
                      <div className='flex-shrink-0 w-10 h-10 bg-purple-500 text-white rounded-full flex items-center justify-center font-bold text-lg'>
                        3
                      </div>
                      <div className='flex-1'>
                        <h3 className='text-lg font-semibold text-gray-900 dark:text-white mb-2'>
                          Переглянь варіанти плейлистів
                        </h3>
                        <p className='text-gray-700 dark:text-gray-300 mb-3'>
                          Після натискання <strong>"Так"</strong> система
                          згенерує 2 варіанти саундтреків:
                        </p>
                        <ul className='list-disc list-inside space-y-1 text-sm text-gray-600 dark:text-gray-400 ml-4'>
                          <li>
                            Кожен варіант містить список треків (№, Назва,
                            Виконавець, Тривалість)
                          </li>
                          <li>Порівняй варіанти та обери найкращий для себе</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* Step 4 */}
                  <div className='bg-white dark:bg-gray-800 rounded-lg p-5 border-l-4 border-orange-500'>
                    <div className='flex items-start gap-4'>
                      <div className='flex-shrink-0 w-10 h-10 bg-orange-500 text-white rounded-full flex items-center justify-center font-bold text-lg'>
                        4
                      </div>
                      <div className='flex-1'>
                        <h3 className='text-lg font-semibold text-gray-900 dark:text-white mb-2'>
                          Згенеруй плейлист
                        </h3>
                        <p className='text-gray-700 dark:text-gray-300'>
                          Натисни кнопку <strong>"Обрати цей варіант"</strong>{' '}
                          під обраним варіантом. Плейлист буде створено та
                          збережено в твоїй історії (панель зліва - секція
                          "Плейлисти").
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className='mt-6 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4 border border-yellow-200 dark:border-yellow-800'>
                  <p className='text-sm text-yellow-800 dark:text-yellow-200'>
                    <strong>💡 Порада:</strong> Всі збережені воркаути та
                    плейлисти доступні в панелі
                    <strong> Історія</strong> (зліва). Ти можеш використовувати
                    їх знову або видаляти непотрібні.
                  </p>
                </div>
              </div>

              {import.meta.env.DEV && (
                <p className='text-xs mt-4 text-center text-gray-400'>
                  API URL:{' '}
                  {import.meta.env.VITE_API_URL || 'http://localhost:8000'}
                </p>
              )}
            </div>
          )}
          {error && (
            <ErrorDisplay
              error={error}
              onDismiss={() => {
                // Error will be cleared on next message
              }}
            />
          )}
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {/* Show buttons for workout activation question */}
          {activeWorkout && showPlaylistQuestion && (
            <div className='max-w-2xl mx-auto flex justify-start mb-4'>
              <div className='flex gap-3'>
                <button
                  onClick={() => {
                    setShowPlaylistQuestion(false);
                    setActiveWorkout(null);
                    setActiveWorkoutId(null);
                    // Add message about clarification needed
                    const clarificationMessage: Message = {
                      id: Date.now().toString(),
                      role: 'assistant',
                      content: 'Уточніть ваш запит щодо тренування.',
                      timestamp: new Date(),
                    };
                    setMessages((prev) => [...prev, clarificationMessage]);
                  }}
                  className='px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors font-medium'
                >
                  Ні
                </button>
                <button
                  onClick={async () => {
                    setShowPlaylistQuestion(false);
                    setLoadingVariants(true);
                    try {
                      // Use saved genres and interval_stages from workout if available
                      let genresToUse = workoutSettings.genres;
                      let intervalStagesToUse =
                        workoutSettings.intervalStages?.map((stage) => ({
                          name: stage.name,
                          duration_minutes: stage.durationMinutes,
                          hr_zone: stage.hrZone,
                          bpm_range: stage.bpmRange,
                        }));

                      // If workout was loaded from history, get saved parameters
                      if (activeWorkoutId) {
                        try {
                          const savedWorkout = await api.getWorkout(
                            activeWorkoutId,
                            user!.id
                          );
                          if (
                            savedWorkout.genres &&
                            savedWorkout.genres.length > 0
                          ) {
                            genresToUse = savedWorkout.genres;
                          }
                          if (
                            savedWorkout.interval_stages &&
                            savedWorkout.interval_stages.length > 0
                          ) {
                            intervalStagesToUse = savedWorkout.interval_stages;
                          }
                          if (savedWorkout.prompt) {
                            setWorkoutSettings((prev) => ({
                              ...prev,
                              prompt: savedWorkout.prompt || '',
                            }));
                          }
                        } catch (error) {
                          console.warn(
                            'Failed to load saved workout parameters, using current settings'
                          );
                        }
                      }

                      // Use prompt from current settings (already loaded if workout from history)
                      const promptToUse = workoutSettings.prompt || null;

                      const request = {
                        workout: activeWorkout!,
                        user_preferences: {
                          top_genres: genresToUse,
                        },
                        user_id: user?.id,
                        interval_stages: intervalStagesToUse,
                        prompt: promptToUse,
                      };
                      const variantsData = await api.previewPlaylistVariants(
                        request
                      );
                      setVariants(variantsData);
                    } catch (error) {
                      console.error('Failed to generate variants:', error);
                      alert('Помилка генерації варіантів');
                    } finally {
                      setLoadingVariants(false);
                    }
                  }}
                  disabled={loadingVariants}
                  className='px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed'
                >
                  {loadingVariants ? 'Генерація...' : 'Так'}
                </button>
                <button
                  onClick={() => {
                    setShowPlaylistQuestion(false);
                    setActiveWorkout(null);
                    setActiveWorkoutId(null);
                  }}
                  className='px-6 py-2 bg-gray-300 dark:bg-gray-600 text-gray-900 dark:text-white rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500 transition-colors font-medium'
                >
                  Ні
                </button>
              </div>
            </div>
          )}

          {/* Show track variants for selection */}
          {variants && (
            <div className='max-w-4xl mx-auto space-y-4'>
              <h3 className='text-lg font-semibold text-gray-900 dark:text-white text-center mb-4'>
                Оберіть варіант плейлисту:
              </h3>
              <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                {/* Variant 1 */}
                <div className='bg-white dark:bg-gray-800 rounded-lg p-4 border-2 border-blue-300 dark:border-blue-700'>
                  <h4 className='text-md font-semibold text-gray-900 dark:text-white mb-3'>
                    Варіант 1
                  </h4>
                  <div className='text-sm text-gray-600 dark:text-gray-400 mb-3'>
                    <p>{variants.variant1.total_tracks} треків</p>
                    <p>
                      {Math.round(variants.variant1.total_duration / 60)} хв
                    </p>
                  </div>
                  <div className='max-h-64 overflow-y-auto mb-3'>
                    <table className='w-full text-xs'>
                      <thead className='bg-gray-100 dark:bg-gray-700'>
                        <tr>
                          <th className='p-2 text-left'>№</th>
                          <th className='p-2 text-left'>Назва</th>
                          <th className='p-2 text-left'>Виконавець</th>
                          <th className='p-2 text-left'>Тривалість</th>
                        </tr>
                      </thead>
                      <tbody>
                        {variants.variant1.tracks.map(
                          (track: Track, index: number) => (
                            <tr
                              key={track.id}
                              className='border-b border-gray-200 dark:border-gray-700'
                            >
                              <td className='p-2'>{index + 1}</td>
                              <td className='p-2'>{track.name}</td>
                              <td className='p-2'>{track.artist}</td>
                              <td className='p-2'>
                                {Math.floor(track.duration_ms / 60000)}:
                                {String(
                                  Math.floor((track.duration_ms % 60000) / 1000)
                                ).padStart(2, '0')}
                              </td>
                            </tr>
                          )
                        )}
                      </tbody>
                    </table>
                  </div>
                  <button
                    onClick={async () => {
                      try {
                        const playlist = await generatePlaylist(
                          activeWorkout!,
                          user?.id,
                          workoutSettings.genres,
                          workoutSettings.intervalStages,
                          workoutSettings.prompt
                        );
                        setVariants(null);
                        setActiveWorkout(null);
                        setActiveWorkoutId(null);
                        // Refresh history after successful generation
                        if (playlist?.spotify_url || playlist?.playlist_id) {
                          // Force refresh by incrementing trigger
                          setRefreshTrigger((prev) => prev + 1);
                          // Also manually refresh after a short delay to ensure data is saved
                          setTimeout(() => {
                            setRefreshTrigger((prev) => prev + 1);
                          }, 1000);
                        }
                      } catch (error) {
                        console.error('Failed to generate playlist:', error);
                      }
                    }}
                    className='w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium'
                  >
                    Обрати цей варіант
                  </button>
                </div>

                {/* Variant 2 */}
                <div className='bg-white dark:bg-gray-800 rounded-lg p-4 border-2 border-green-300 dark:border-green-700'>
                  <h4 className='text-md font-semibold text-gray-900 dark:text-white mb-3'>
                    Варіант 2
                  </h4>
                  <div className='text-sm text-gray-600 dark:text-gray-400 mb-3'>
                    <p>{variants.variant2.total_tracks} треків</p>
                    <p>
                      {Math.round(variants.variant2.total_duration / 60)} хв
                    </p>
                  </div>
                  <div className='max-h-64 overflow-y-auto mb-3'>
                    <table className='w-full text-xs'>
                      <thead className='bg-gray-100 dark:bg-gray-700'>
                        <tr>
                          <th className='p-2 text-left'>№</th>
                          <th className='p-2 text-left'>Назва</th>
                          <th className='p-2 text-left'>Виконавець</th>
                          <th className='p-2 text-left'>Тривалість</th>
                        </tr>
                      </thead>
                      <tbody>
                        {variants.variant2.tracks.map(
                          (track: Track, index: number) => (
                            <tr
                              key={track.id}
                              className='border-b border-gray-200 dark:border-gray-700'
                            >
                              <td className='p-2'>{index + 1}</td>
                              <td className='p-2'>{track.name}</td>
                              <td className='p-2'>{track.artist}</td>
                              <td className='p-2'>
                                {Math.floor(track.duration_ms / 60000)}:
                                {String(
                                  Math.floor((track.duration_ms % 60000) / 1000)
                                ).padStart(2, '0')}
                              </td>
                            </tr>
                          )
                        )}
                      </tbody>
                    </table>
                  </div>
                  <button
                    onClick={async () => {
                      try {
                        const playlist = await generatePlaylist(
                          activeWorkout!,
                          user?.id,
                          workoutSettings.genres,
                          workoutSettings.intervalStages,
                          workoutSettings.prompt
                        );
                        setVariants(null);
                        setActiveWorkout(null);
                        setActiveWorkoutId(null);
                        // Refresh history after successful generation
                        if (playlist?.spotify_url || playlist?.playlist_id) {
                          // Force refresh by incrementing trigger
                          setRefreshTrigger((prev) => prev + 1);
                          // Also manually refresh after a short delay to ensure data is saved
                          setTimeout(() => {
                            setRefreshTrigger((prev) => prev + 1);
                          }, 1000);
                        }
                      } catch (error) {
                        console.error('Failed to generate playlist:', error);
                      }
                    }}
                    className='w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium'
                  >
                    Обрати цей варіант
                  </button>
                </div>
              </div>
            </div>
          )}

          {isLoading && <TypingIndicator />}
        </div>

        <InputBar onSend={handleSend} disabled={isLoading} />
      </div>

      {/* Settings Sidebar - Right */}
      <SettingsSidebar
        settings={workoutSettings}
        onSettingsChange={setWorkoutSettings}
        collapsed={settingsCollapsed}
        onToggleCollapse={() => setSettingsCollapsed(!settingsCollapsed)}
        userId={user?.id}
        onSave={() => {
          // Refresh workout history after save
          setRefreshTrigger((prev) => prev + 1);
          // Also refresh after a short delay to ensure data is saved
          setTimeout(() => {
            setRefreshTrigger((prev) => prev + 1);
          }, 500);
        }}
        onWorkoutActivated={(workout) => {
          const workoutData: Workout = {
            type: workout.type as Workout['type'],
            duration_minutes: workout.duration_minutes,
            intensity: workout.intensity as Workout['intensity'],
            hr_zones: workout.hr_zones,
          };
          setActiveWorkout(workoutData);
          // Set workout ID if available (for newly saved workouts)
          if (workout.id) {
            setActiveWorkoutId(workout.id);
          }
          addWorkoutActivationMessage(workoutData);
          setShowPlaylistQuestion(true);
        }}
      />
    </div>
  );
}
