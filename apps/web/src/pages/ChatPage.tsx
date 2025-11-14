import { useState, useRef, useEffect } from 'react';
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
} from '../types';

export function ChatPage() {
  const { user, spotifyAuthenticated } = useAuth();
  const {
    messages,
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
  // On mobile, sidebars start collapsed; on desktop, they're visible
  const [historyCollapsed, setHistoryCollapsed] = useState(
    typeof window !== 'undefined' && window.innerWidth < 768
  );
  const [settingsCollapsed, setSettingsCollapsed] = useState(
    typeof window !== 'undefined' && window.innerWidth < 768
  );
  const [activeWorkout, setActiveWorkout] = useState<Workout | null>(null);
  const [activeWorkoutId, setActiveWorkoutId] = useState<string | null>(null);
  const [showPlaylistQuestion, setShowPlaylistQuestion] = useState(false);
  const [variants, setVariants] = useState<PlaylistVariantsResponse | null>(
    null
  );
  const [loadingVariants, setLoadingVariants] = useState(false);
  const [excludedTrackIds, setExcludedTrackIds] = useState<Set<string>>(new Set());
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Handle window resize for mobile/desktop sidebar state
  useEffect(() => {
    const handleResize = () => {
      const isMobile = window.innerWidth < 768;
      setHistoryCollapsed(isMobile);
      setSettingsCollapsed(isMobile);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Auto-scroll to bottom when messages or variants change
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, variants, isLoading, loadingVariants]);

  const handleClearChat = () => {
    clearMessages();
    setVariants(null);
    setActiveWorkout(null);
    setActiveWorkoutId(null);
    setShowPlaylistQuestion(false);
    setExcludedTrackIds(new Set()); // Clear excluded tracks
  };

  const handleSend = async (text: string) => {
    const workout = await sendMessage(text, user?.id);

    // Check if playlist was generated in conversation flow
    // The playlist is already added to messages by useChat hook
    // Use useEffect to check after messages update, or check workout marker
    if (workout && (workout as any)._hasPlaylist) {
      // Playlist was generated automatically in conversation flow
      // No need to show playlist question - it's already in the chat
      setActiveWorkout(workout);
      setShowPlaylistQuestion(false);
      return;
    }

    // Check if workout was created (has workout_id) - this happens after user confirms
    if (workout && workout.id) {
      // Workout was created in database, now we can generate playlist
      setActiveWorkout(workout);
      setActiveWorkoutId(workout.id);
      setExcludedTrackIds(new Set()); // Reset excluded tracks for new workout
      // Show question about generating playlist
      setShowPlaylistQuestion(true);
      return;
    }

    // If workout is ready and complete, show workout info and ask for confirmation
    // Note: If needs_clarification is true, the conversation continues automatically
    // The AI message with clarification question is already added to messages
    if (workout && !workout.needs_clarification) {
      // Set active workout and show confirmation question
      // The AI already asked "Створити воркаут? (Да/Ні)" in the message
      setActiveWorkout(workout);
      setActiveWorkoutId(null); // Not created yet, waiting for confirmation
      setExcludedTrackIds(new Set()); // Reset excluded tracks for new workout
      // Show buttons to confirm workout creation
      setShowPlaylistQuestion(true);
    }
    // If needs_clarification, user can continue the conversation naturally
    // The clarification question is already displayed in the chat
  };

  const generateVariants = async () => {
    if (!activeWorkout) return;

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

      // Get excluded track IDs from previous generations
      const excludedIdsArray = Array.from(excludedTrackIds);

      const request = {
        workout: activeWorkout!,
        user_preferences: {
          top_genres: genresToUse,
        },
        user_id: user?.id,
        interval_stages: intervalStagesToUse,
        prompt: promptToUse,
        excluded_track_ids: excludedIdsArray.length > 0 ? excludedIdsArray : undefined,
      };
      const variantsData = await api.previewPlaylistVariants(
        request
      );

      // Validate variants - check if they are empty
      if (
        (!variantsData.variant1.tracks || variantsData.variant1.tracks.length === 0) &&
        (!variantsData.variant2.tracks || variantsData.variant2.tracks.length === 0)
      ) {
        throw new Error(
          'Не вдалося знайти треки для воркауту. Спробуйте змінити параметри або додати жанри музики.'
        );
      }

      // Check if at least one variant has tracks
      if (
        (!variantsData.variant1.tracks || variantsData.variant1.tracks.length === 0) ||
        (!variantsData.variant2.tracks || variantsData.variant2.tracks.length === 0)
      ) {
        console.warn('One of the variants is empty, but continuing with available variant');
      }

      // Update excluded track IDs with tracks from new variants
      const newExcludedIds = new Set(excludedTrackIds);
      if (variantsData.variant1.tracks) {
        variantsData.variant1.tracks.forEach((track: Track) => {
          newExcludedIds.add(track.id);
        });
      }
      if (variantsData.variant2.tracks) {
        variantsData.variant2.tracks.forEach((track: Track) => {
          newExcludedIds.add(track.id);
        });
      }
      setExcludedTrackIds(newExcludedIds);

      setVariants(variantsData);
    } catch (error) {
      console.error('Failed to generate variants:', error);
      // Error logged to console - no alert shown
      setVariants(null);
    } finally {
      setLoadingVariants(false);
    }
  };

  // This should not be reached if ProtectedRoute is working correctly,
  // but add a safety check just in case
  if (!user || !spotifyAuthenticated) {
    return null;
  }

  return (
    <div className='flex flex-col md:flex-row h-screen bg-gray-50 dark:bg-gray-900 relative'>
      {/* History Sidebar - Left - 1.5 units */}
      <div className={`${historyCollapsed ? 'hidden md:flex' : 'flex'} md:flex-[1.5]`}>
        <PlaylistHistorySidebar
          userId={user?.id}
          refreshTrigger={refreshTrigger}
          collapsed={historyCollapsed}
          onToggleCollapse={() => setHistoryCollapsed(!historyCollapsed)}
          activeWorkoutId={activeWorkoutId}
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
            setActiveWorkoutId(workoutId); // Set workout ID to prevent duplicate creation
            setExcludedTrackIds(new Set()); // Reset excluded tracks when selecting workout from history

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
            // Error logged to console - no alert shown
          }
        }}
        />
      </div>

      {/* Mobile menu button */}
      <button
        onClick={() => setHistoryCollapsed(!historyCollapsed)}
        className='md:hidden fixed top-4 left-4 z-50 p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700'
        aria-label='Toggle history'
      >
        <svg
          className='w-6 h-6 text-gray-600 dark:text-gray-400'
          fill='none'
          stroke='currentColor'
          viewBox='0 0 24 24'
        >
          <path
            strokeLinecap='round'
            strokeLinejoin='round'
            strokeWidth={2}
            d='M4 6h16M4 12h16M4 18h16'
          />
        </svg>
      </button>

      {/* Main Chat Area - Center - 3 units */}
      <div className='flex-1 md:flex-[3] flex flex-col bg-white dark:bg-gray-900 min-w-0'>
        {/* Header with Clear Chat button */}
        {messages.length > 0 && (
          <div className='flex justify-between items-center p-2 md:p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'>
            <h1 className='text-lg md:text-xl font-bold text-gray-900 dark:text-white'>
              RunBeat AI
            </h1>
            <button
              onClick={handleClearChat}
              className='px-3 md:px-4 py-1.5 md:py-2 text-xs md:text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors'
            >
              Очистити
            </button>
          </div>
        )}

        <div ref={chatContainerRef} className='flex-1 overflow-y-auto p-2 md:p-4 space-y-4'>
          {messages.length === 0 && (
            <div className='max-w-3xl mx-auto px-2 md:px-4 py-4 md:py-8'>
              <div className='text-center mb-6 md:mb-8'>
                <h1 className='text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-2'>
                  Привіт! Я RunBeat AI 🎵
                </h1>
                <p className='text-base md:text-lg text-gray-600 dark:text-gray-400'>
                  Створю ідеальний плейлист для твого тренування
                </p>
              </div>

              <div className='bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg shadow-lg p-4 md:p-6 mb-4 md:mb-6 border border-blue-200 dark:border-blue-800'>
                <h2 className='text-xl md:text-2xl font-bold text-gray-900 dark:text-white mb-4 md:mb-6 text-center'>
                  📋 Як це працює
                </h2>

                <div className='space-y-4 md:space-y-6'>
                  {/* Step 1 */}
                  <div className='bg-white dark:bg-gray-800 rounded-lg p-3 md:p-5 border-l-4 border-blue-500'>
                    <div className='flex items-start gap-2 md:gap-4'>
                      <div className='flex-shrink-0 w-8 h-8 md:w-10 md:h-10 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold text-sm md:text-lg'>
                        1
                      </div>
                      <div className='flex-1 min-w-0'>
                        <h3 className='text-base md:text-lg font-semibold text-gray-900 dark:text-white mb-2'>
                          Опиши своє тренування
                        </h3>
                        <p className='text-gray-700 dark:text-gray-300 mb-3'>
                          Просто напиши мені, що ти хочеш зробити. Я розумію природну мову! Наприклад:
                        </p>
                        <ul className='list-disc list-inside space-y-1 text-sm text-gray-600 dark:text-gray-400 ml-4 mb-3'>
                          <li>
                            <strong>"хочу легку пробіжку 30 хвилин"</strong>
                          </li>
                          <li>
                            <strong>"інтервали 40 хв, рок-музика"</strong>
                          </li>
                          <li>
                            <strong>"фартлек 55 хв під електронну музику"</strong>
                          </li>
                          <li>
                            <strong>"темповий біг 45 хв, енергійна музика для ранкового бігу"</strong>
                          </li>
                        </ul>
                        <p className='text-gray-700 dark:text-gray-300'>
                          Я можу розпізнати: <strong>тип тренування</strong> (стабільна, інтервальна, фартлек),
                          <strong> тривалість</strong>, <strong>інтенсивність</strong> (легка, середня, висока),
                          та <strong>музичні побажання</strong> (жанри, опис).
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Step 2 */}
                  <div className='bg-white dark:bg-gray-800 rounded-lg p-3 md:p-5 border-l-4 border-yellow-500'>
                    <div className='flex items-start gap-2 md:gap-4'>
                      <div className='flex-shrink-0 w-8 h-8 md:w-10 md:h-10 bg-yellow-500 text-white rounded-full flex items-center justify-center font-bold text-sm md:text-lg'>
                        2
                      </div>
                      <div className='flex-1 min-w-0'>
                        <h3 className='text-base md:text-lg font-semibold text-gray-900 dark:text-white mb-2'>
                          Я задам уточнюючі питання (якщо потрібно)
                        </h3>
                        <p className='text-gray-700 dark:text-gray-300'>
                          Якщо мені потрібна додаткова інформація, я запитаю.
                          Наприклад: <em>"Який інтервал роботи/відпочинку?"</em> або
                          <em>"Яка інтенсивність?"</em> Просто відповідай на мої питання.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Step 3 */}
                  <div className='bg-white dark:bg-gray-800 rounded-lg p-3 md:p-5 border-l-4 border-green-500'>
                    <div className='flex items-start gap-2 md:gap-4'>
                      <div className='flex-shrink-0 w-8 h-8 md:w-10 md:h-10 bg-green-500 text-white rounded-full flex items-center justify-center font-bold text-sm md:text-lg'>
                        3
                      </div>
                      <div className='flex-1 min-w-0'>
                        <h3 className='text-base md:text-lg font-semibold text-gray-900 dark:text-white mb-2'>
                          Підтверди створення воркауту
                        </h3>
                        <p className='text-gray-700 dark:text-gray-300'>
                          Коли я зібрав всю інформацію, я покажу тобі резюме воркауту та запитаю:
                          <strong>"Створити воркаут? (Да/Ні)"</strong>. Натисни <strong>"Так"</strong>,
                          щоб створити воркаут, або <strong>"Ні"</strong>, щоб скасувати.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Step 4 */}
                  <div className='bg-white dark:bg-gray-800 rounded-lg p-3 md:p-5 border-l-4 border-purple-500'>
                    <div className='flex items-start gap-2 md:gap-4'>
                      <div className='flex-shrink-0 w-8 h-8 md:w-10 md:h-10 bg-purple-500 text-white rounded-full flex items-center justify-center font-bold text-sm md:text-lg'>
                        4
                      </div>
                      <div className='flex-1 min-w-0'>
                        <h3 className='text-base md:text-lg font-semibold text-gray-900 dark:text-white mb-2'>
                          Згенеруй плейлист
                        </h3>
                        <p className='text-gray-700 dark:text-gray-300 mb-3'>
                          Після створення воркауту, натисни <strong>"Так, згенерувати плейлист"</strong>.
                          Я створю 2 варіанти плейлистів з урахуванням твоїх побажань:
                        </p>
                        <ul className='list-disc list-inside space-y-1 text-sm text-gray-600 dark:text-gray-400 ml-4'>
                          <li>
                            Кожен варіант містить список треків (№, Назва, Виконавець, Тривалість)
                          </li>
                          <li>Порівняй варіанти та обери найкращий для себе</li>
                          <li>Натисни <strong>"Обрати цей варіант"</strong> під обраним варіантом</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* Step 5 */}
                  <div className='bg-white dark:bg-gray-800 rounded-lg p-3 md:p-5 border-l-4 border-orange-500'>
                    <div className='flex items-start gap-2 md:gap-4'>
                      <div className='flex-shrink-0 w-8 h-8 md:w-10 md:h-10 bg-orange-500 text-white rounded-full flex items-center justify-center font-bold text-sm md:text-lg'>
                        5
                      </div>
                      <div className='flex-1 min-w-0'>
                        <h3 className='text-base md:text-lg font-semibold text-gray-900 dark:text-white mb-2'>
                          Відкрий в Spotify
                        </h3>
                        <p className='text-gray-700 dark:text-gray-300'>
                          Плейлист буде створено та збережено в твоїй історії (панель зліва - секція
                          "Плейлисти"). Натисни <strong>"Відкрити в Spotify"</strong>, щоб відкрити
                          плейлист у додатку Spotify та почати тренування! 🎵
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className='mt-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800'>
                  <p className='text-sm text-blue-800 dark:text-blue-200 mb-2'>
                    <strong>💡 Альтернативний спосіб:</strong> Ти також можеш створити воркаут вручну
                    через панель <strong>Воркаут</strong> (справа) або вибрати існуючий з панелі
                    <strong> Історія</strong> (зліва).
                  </p>
                  <p className='text-sm text-blue-800 dark:text-blue-200'>
                    <strong>🤖 AI-асистент:</strong> Я використовую гібридну систему парсингу (rule-based + AI)
                    для швидкого та точного розуміння твоїх побажань. Якщо щось незрозуміло - просто спитай!
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

          {/* Show buttons for workout confirmation or playlist generation */}
          {activeWorkout && showPlaylistQuestion && (
            <div className='max-w-2xl mx-auto flex justify-start mb-4 px-2 md:px-0'>
              <div className='flex flex-col sm:flex-row gap-2 sm:gap-3 w-full sm:w-auto'>
                {activeWorkoutId ? (
                  // Workout already created - show button to generate playlist
                  <button
                    onClick={generateVariants}
                    disabled={loadingVariants}
                    className='px-4 sm:px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base'
                  >
                    {loadingVariants ? 'Генерація...' : 'Так, згенерувати плейлист'}
                  </button>
                ) : (
                  // Workout not created yet - show buttons to confirm creation
                  <>
                    <button
                      onClick={async () => {
                        // Send "Да" to chat to confirm workout creation
                        const confirmedWorkout = await sendMessage('Да', user?.id);
                        if (confirmedWorkout && confirmedWorkout.id) {
                          // Workout created, now show playlist generation option
                          setActiveWorkoutId(confirmedWorkout.id);
                          setActiveWorkout(confirmedWorkout);
                        }
                      }}
                    disabled={isLoading}
                    className='px-4 sm:px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base'
                  >
                    {isLoading ? 'Створення...' : 'Так'}
                  </button>
                  <button
                    onClick={async () => {
                      // Send "Ні" to chat to decline workout creation
                      await sendMessage('Ні', user?.id);
                      setShowPlaylistQuestion(false);
                      setActiveWorkout(null);
                      setActiveWorkoutId(null);
                    }}
                    disabled={isLoading}
                    className='px-4 sm:px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base'
                  >
                    Ні
                  </button>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Show track variants for selection */}
          {variants && (
            <div className='max-w-4xl mx-auto space-y-4 px-2 md:px-0'>
              {/* Check if both variants are empty */}
              {(!variants.variant1.tracks || variants.variant1.tracks.length === 0) &&
               (!variants.variant2.tracks || variants.variant2.tracks.length === 0) ? (
                <div className='bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 md:p-4'>
                  <p className='text-red-800 dark:text-red-200 font-medium'>
                    ❌ Помилка: Не вдалося згенерувати варіанти плейлистів
                  </p>
                  <p className='text-red-600 dark:text-red-300 text-sm mt-2'>
                    Можливі причини:
                  </p>
                  <ul className='list-disc list-inside text-red-600 dark:text-red-300 text-sm mt-1 space-y-1'>
                    <li>Некоректні параметри воркауту</li>
                    <li>Проблеми з підключенням до Spotify API</li>
                    <li>Відсутність жанрів музики</li>
                    <li>Занадто вузький діапазон BPM</li>
                  </ul>
                  <p className='text-red-600 dark:text-red-300 text-sm mt-2'>
                    Спробуйте змінити параметри воркауту або додати жанри музики.
                  </p>
                </div>
              ) : (
                <>
              <div className='flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 sm:gap-0 mb-4'>
                <h3 className='text-base md:text-lg font-semibold text-gray-900 dark:text-white'>
                  Оберіть варіант плейлисту:
                </h3>
                <button
                  onClick={generateVariants}
                  disabled={loadingVariants}
                  className='px-3 md:px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-xs md:text-sm disabled:opacity-50 disabled:cursor-not-allowed w-full sm:w-auto'
                >
                  {loadingVariants ? 'Генерація...' : 'Згенерувати ще'}
                </button>
              </div>
              <div className='grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4'>
                {/* Variant 1 */}
                <div className='bg-white dark:bg-gray-800 rounded-lg p-3 md:p-4 border-2 border-blue-300 dark:border-blue-700'>
                  <h4 className='text-sm md:text-md font-semibold text-gray-900 dark:text-white mb-2 md:mb-3'>
                    Варіант 1
                  </h4>
                  <div className='text-xs md:text-sm text-gray-600 dark:text-gray-400 mb-2 md:mb-3'>
                    <p>{variants.variant1.total_tracks} треків</p>
                    <p>
                      {Math.round(variants.variant1.total_duration / 60)} хв
                    </p>
                  </div>
                  <div className='max-h-48 md:max-h-64 overflow-y-auto mb-2 md:mb-3'>
                    <div className='hidden md:block'>
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
                        {variants.variant1.tracks && variants.variant1.tracks.length > 0 ? (
                          variants.variant1.tracks.map(
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
                        )
                        ) : (
                          <tr>
                            <td colSpan={4} className='p-4 text-center text-gray-500 dark:text-gray-400'>
                              Немає треків у цьому варіанті
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                    </div>
                    {/* Mobile view - list format */}
                    <div className='md:hidden space-y-2'>
                      {variants.variant1.tracks && variants.variant1.tracks.length > 0 ? (
                        variants.variant1.tracks.map((track: Track, index: number) => (
                          <div
                            key={track.id}
                            className='p-2 bg-gray-50 dark:bg-gray-700 rounded text-xs'
                          >
                            <div className='font-medium truncate'>{index + 1}. {track.name}</div>
                            <div className='text-gray-600 dark:text-gray-400 truncate'>{track.artist}</div>
                            <div className='text-gray-500 dark:text-gray-500 text-[10px]'>
                              {Math.floor(track.duration_ms / 60000)}:
                              {String(Math.floor((track.duration_ms % 60000) / 1000)).padStart(2, '0')}
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className='p-4 text-center text-gray-500 dark:text-gray-400 text-xs'>
                          Немає треків у цьому варіанті
                        </div>
                      )}
                    </div>
                  </div>
                  {variants.variant1.tracks && variants.variant1.tracks.length > 0 ? (
                  <button
                    onClick={async () => {
                      try {
                        const playlist = await generatePlaylist(
                          activeWorkout!,
                          user?.id,
                          workoutSettings.genres,
                          workoutSettings.intervalStages,
                          workoutSettings.prompt,
                          activeWorkoutId,
                          variants.variant1.tracks // Pass selected variant tracks
                        );
                        setVariants(null);
                        setActiveWorkout(null);
                        setActiveWorkoutId(null);
                        // Refresh history after successful generation
                        if (playlist?.spotify_url || playlist?.playlist_id) {
                          // Refresh once after a short delay to ensure data is saved
                          setTimeout(() => {
                            setRefreshTrigger((prev) => prev + 1);
                          }, 500);
                        }
                      } catch (error) {
                        console.error('Failed to generate playlist:', error);
                      }
                    }}
                    className='w-full px-3 md:px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm md:text-base'
                  >
                    Обрати цей варіант
                  </button>
                  ) : (
                    <div className='w-full px-3 md:px-4 py-2 bg-gray-400 text-white rounded-lg text-center font-medium cursor-not-allowed text-sm md:text-base'>
                      Варіант недоступний
                    </div>
                  )}
                </div>

                {/* Variant 2 */}
                <div className='bg-white dark:bg-gray-800 rounded-lg p-3 md:p-4 border-2 border-green-300 dark:border-green-700'>
                  <h4 className='text-sm md:text-md font-semibold text-gray-900 dark:text-white mb-2 md:mb-3'>
                    Варіант 2
                  </h4>
                  <div className='text-xs md:text-sm text-gray-600 dark:text-gray-400 mb-2 md:mb-3'>
                    <p>{variants.variant2.total_tracks} треків</p>
                    <p>
                      {Math.round(variants.variant2.total_duration / 60)} хв
                    </p>
                  </div>
                  <div className='max-h-48 md:max-h-64 overflow-y-auto mb-2 md:mb-3'>
                    <div className='hidden md:block'>
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
                        {variants.variant2.tracks && variants.variant2.tracks.length > 0 ? (
                          variants.variant2.tracks.map(
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
                        )
                        ) : (
                          <tr>
                            <td colSpan={4} className='p-4 text-center text-gray-500 dark:text-gray-400'>
                              Немає треків у цьому варіанті
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                    </div>
                    {/* Mobile view - list format */}
                    <div className='md:hidden space-y-2'>
                      {variants.variant2.tracks && variants.variant2.tracks.length > 0 ? (
                        variants.variant2.tracks.map((track: Track, index: number) => (
                          <div
                            key={track.id}
                            className='p-2 bg-gray-50 dark:bg-gray-700 rounded text-xs'
                          >
                            <div className='font-medium truncate'>{index + 1}. {track.name}</div>
                            <div className='text-gray-600 dark:text-gray-400 truncate'>{track.artist}</div>
                            <div className='text-gray-500 dark:text-gray-500 text-[10px]'>
                              {Math.floor(track.duration_ms / 60000)}:
                              {String(Math.floor((track.duration_ms % 60000) / 1000)).padStart(2, '0')}
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className='p-4 text-center text-gray-500 dark:text-gray-400 text-xs'>
                          Немає треків у цьому варіанті
                        </div>
                      )}
                    </div>
                  </div>
                  {variants.variant2.tracks && variants.variant2.tracks.length > 0 ? (
                  <button
                    onClick={async () => {
                      try {
                        const playlist = await generatePlaylist(
                          activeWorkout!,
                          user?.id,
                          workoutSettings.genres,
                          workoutSettings.intervalStages,
                          workoutSettings.prompt,
                          activeWorkoutId,
                          variants.variant2.tracks // Pass selected variant tracks
                        );
                        setVariants(null);
                        setActiveWorkout(null);
                        setActiveWorkoutId(null);
                        // Refresh history after successful generation
                        if (playlist?.spotify_url || playlist?.playlist_id) {
                          // Refresh once after a short delay to ensure data is saved
                          setTimeout(() => {
                            setRefreshTrigger((prev) => prev + 1);
                          }, 500);
                        }
                      } catch (error) {
                        console.error('Failed to generate playlist:', error);
                      }
                    }}
                    className='w-full px-3 md:px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium text-sm md:text-base'
                  >
                    Обрати цей варіант
                  </button>
                  ) : (
                    <div className='w-full px-3 md:px-4 py-2 bg-gray-400 text-white rounded-lg text-center font-medium cursor-not-allowed text-sm md:text-base'>
                      Варіант недоступний
                    </div>
                  )}
                </div>
              </div>
              </>
              )}
            </div>
          )}

          {(isLoading || loadingVariants) && (
            <TypingIndicator
              message={
                loadingVariants
                  ? 'Генерую варіанти плейлисту...'
                  : isLoading
                  ? 'Обробляю повідомлення...'
                  : undefined
              }
            />
          )}
        </div>

        <InputBar onSend={handleSend} disabled={isLoading || loadingVariants} />
      </div>

      {/* Mobile settings button */}
      <button
        onClick={() => setSettingsCollapsed(!settingsCollapsed)}
        className='md:hidden fixed top-4 right-4 z-50 p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700'
        aria-label='Toggle settings'
      >
        <svg
          className='w-6 h-6 text-gray-600 dark:text-gray-400'
          fill='none'
          stroke='currentColor'
          viewBox='0 0 24 24'
        >
          <path
            strokeLinecap='round'
            strokeLinejoin='round'
            strokeWidth={2}
            d='M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z'
          />
          <path
            strokeLinecap='round'
            strokeLinejoin='round'
            strokeWidth={2}
            d='M15 12a3 3 0 11-6 0 3 3 0 016 0z'
          />
        </svg>
      </button>

      {/* Settings Sidebar - Right - 1.5 units */}
      <div className={`${settingsCollapsed ? 'hidden md:flex' : 'flex'} md:flex-[1.5]`}>
        <SettingsSidebar
        settings={workoutSettings}
        onSettingsChange={setWorkoutSettings}
        collapsed={settingsCollapsed}
        onToggleCollapse={() => setSettingsCollapsed(!settingsCollapsed)}
        userId={user?.id}
        onSave={() => {
          // Refresh workout history after save (with delay to ensure data is saved)
          // Single refresh call - debounce is handled in PlaylistHistorySidebar
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
          setExcludedTrackIds(new Set()); // Reset excluded tracks when activating workout
          // Set workout ID if available (for newly saved workouts)
          if (workout.id) {
            setActiveWorkoutId(workout.id);
          }
          addWorkoutActivationMessage(workoutData);
          setShowPlaylistQuestion(true);
        }}
        />
      </div>
    </div>
  );
}
