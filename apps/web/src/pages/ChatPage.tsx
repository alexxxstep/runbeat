import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useChat } from '../hooks/useChat';
import { useAuth } from '../hooks/useAuth';
import { MessageBubble } from '../components/Chat/MessageBubble';
import { InputBar } from '../components/Chat/InputBar';
import { TypingIndicator } from '../components/Chat/TypingIndicator';
import { ErrorDisplay } from '../components/Shared/ErrorDisplay';
import { PlaylistHistorySidebar } from '../components/Chat/PlaylistHistorySidebar';
import { SettingsSidebar } from '../components/Chat/SettingsSidebar';
import type { WorkoutSettings } from '../types/settings';

// Template queries for quick selection
const templateQueries = [
  '30 хв легкий біг',
  '45 хв інтервальне тренування',
  '60 хв велопробіг середньої інтенсивності',
  '20 хв фартлек високий темп',
  '40 хв стабільний біг з рок музикою',
];

export function ChatPage() {
  const navigate = useNavigate();
  const { user, spotifyAuthenticated } = useAuth();
  const {
    messages,
    sendMessage,
    generatePlaylist,
    clearMessages,
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
  });
  const [historyCollapsed, setHistoryCollapsed] = useState(false);
  const [settingsCollapsed, setSettingsCollapsed] = useState(false);

  const handleSend = async (text: string) => {
    const workout = await sendMessage(text);

    // If workout is ready, generate playlist with settings
    if (workout && !workout.needs_clarification) {
      try {
        // Merge workout from chat with settings from sidebar
        const mergedWorkout = {
          ...workout,
          type: workoutSettings.type,
          duration_minutes: workoutSettings.durationMinutes,
          intensity: workoutSettings.intensity,
          hr_zones: workoutSettings.hrZones,
        };

        const playlist = await generatePlaylist(
          mergedWorkout,
          user?.id,
          workoutSettings.genres,
          workoutSettings.intervalStages
        );
        if (playlist?.spotify_url) {
          // Open Spotify playlist URL in new tab
          window.open(playlist.spotify_url, '_blank');
          // Refresh history sidebar
          setRefreshTrigger((prev) => prev + 1);
        } else if (playlist?.playlist_id) {
          navigate(`/player/${playlist.playlist_id}`);
          // Refresh history sidebar
          setRefreshTrigger((prev) => prev + 1);
        }
      } catch (error) {
        console.error('Failed to generate playlist:', error);
      }
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
            <div className='max-w-2xl mx-auto px-4 py-8'>
              <div className='text-center mb-8'>
                <h1 className='text-3xl font-bold text-gray-900 dark:text-white mb-2'>
                  Привіт! Я RunBeat AI 🎵
                </h1>
                <p className='text-lg text-gray-600 dark:text-gray-400'>
                  Опиши своє тренування, і я створю для тебе ідеальний плейлист
                </p>
              </div>

              <div className='bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6'>
                <h2 className='text-xl font-semibold text-gray-900 dark:text-white mb-4'>
                  💡 Для кращого результату вкажи:
                </h2>
                <ul className='space-y-3 text-gray-700 dark:text-gray-300'>
                  <li className='flex items-start gap-3'>
                    <span className='text-green-500 font-bold'>•</span>
                    <div>
                      <strong>Тип тренування:</strong> біг, велосипед, ходьба,
                      інтервали, фартлек
                    </div>
                  </li>
                  <li className='flex items-start gap-3'>
                    <span className='text-green-500 font-bold'>•</span>
                    <div>
                      <strong>Тривалість:</strong> скільки хвилин плануєш
                      тренуватися
                    </div>
                  </li>
                  <li className='flex items-start gap-3'>
                    <span className='text-green-500 font-bold'>•</span>
                    <div>
                      <strong>Інтенсивність:</strong> легка, середня, висока
                    </div>
                  </li>
                  <li className='flex items-start gap-3'>
                    <span className='text-green-500 font-bold'>•</span>
                    <div>
                      <strong>Музичні вподобання:</strong> жанри, виконавці
                      (опціонально)
                    </div>
                  </li>
                  <li className='flex items-start gap-3'>
                    <span className='text-green-500 font-bold'>•</span>
                    <div>
                      <strong>Темп (BPM):</strong> якщо знаєш свій ідеальний
                      темп (опціонально)
                    </div>
                  </li>
                </ul>
              </div>

              <div className='bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6 mb-6'>
                <h3 className='text-lg font-semibold text-blue-900 dark:text-blue-200 mb-3'>
                  📝 Приклади запитів:
                </h3>
                <div className='space-y-3'>
                  <div className='bg-white dark:bg-gray-800 rounded p-3 text-sm'>
                    <p className='text-gray-700 dark:text-gray-300 italic'>
                      "Потрібен плейлист для 30-хвилинного легкого бігу в парку"
                    </p>
                  </div>
                  <div className='bg-white dark:bg-gray-800 rounded p-3 text-sm'>
                    <p className='text-gray-700 dark:text-gray-300 italic'>
                      "Створи плейлист для інтенсивного інтервального тренування
                      45 хвилин, жанр - електронна музика"
                    </p>
                  </div>
                  <div className='bg-white dark:bg-gray-800 rounded p-3 text-sm'>
                    <p className='text-gray-700 dark:text-gray-300 italic'>
                      "Потрібна музика для 60-хвилинного велопробігу середньої
                      інтенсивності, рок та альтернатива"
                    </p>
                  </div>
                  <div className='bg-white dark:bg-gray-800 rounded p-3 text-sm'>
                    <p className='text-gray-700 dark:text-gray-300 italic'>
                      "Фартлек 20 хвилин, високий темп, поп та хіп-хоп"
                    </p>
                  </div>
                </div>
              </div>

              <div className='bg-green-50 dark:bg-green-900/20 rounded-lg p-4'>
                <p className='text-sm text-green-800 dark:text-green-200'>
                  <strong>💚 Порада:</strong> Чим детальніше опишеш своє
                  тренування, тим краще підібрав під тебе музику! Можна вказати
                  навіть конкретних виконавців або жанри.
                </p>
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
          {isLoading && <TypingIndicator />}
        </div>

        {/* Template queries - show only when no messages */}
        {messages.length === 0 && (
          <div className='px-4 pb-4'>
            <div className='max-w-2xl mx-auto'>
              <p className='text-xs text-gray-500 dark:text-gray-400 mb-2 px-2'>
                Швидкі запити:
              </p>
              <div className='flex flex-wrap gap-2'>
                {templateQueries.map((query, index) => (
                  <button
                    key={index}
                    onClick={() => handleSend(query)}
                    disabled={isLoading}
                    className='px-4 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-full hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-gray-700 dark:text-gray-300'
                  >
                    {query}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        <InputBar onSend={handleSend} disabled={isLoading} />
      </div>

      {/* Settings Sidebar - Right */}
      <SettingsSidebar
        settings={workoutSettings}
        onSettingsChange={setWorkoutSettings}
        collapsed={settingsCollapsed}
        onToggleCollapse={() => setSettingsCollapsed(!settingsCollapsed)}
      />
    </div>
  );
}
