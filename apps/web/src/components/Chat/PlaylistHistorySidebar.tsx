import { useEffect } from 'react';
import { usePlaylistHistory } from '../../hooks/usePlaylistHistory';
import { useWorkoutHistory } from '../../hooks/useWorkoutHistory';
import { LoadingSpinner } from '../Shared/LoadingSpinner';

interface PlaylistHistorySidebarProps {
  userId?: string;
  onPlaylistClick?: (playlistId: string, spotifyUrl?: string) => void;
  onWorkoutClick?: (workoutId: string) => void; // Callback when workout is activated
  refreshTrigger?: number; // Trigger refresh when this changes
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function PlaylistHistorySidebar({
  userId,
  onPlaylistClick,
  onWorkoutClick,
  refreshTrigger,
  collapsed = false,
  onToggleCollapse,
}: PlaylistHistorySidebarProps) {
  const {
    playlists,
    loading: playlistsLoading,
    error: playlistsError,
    deletePlaylist,
    refresh: refreshPlaylists,
  } = usePlaylistHistory(userId);
  const {
    workouts,
    loading: workoutsLoading,
    error: workoutsError,
    deleteWorkout,
    refresh: refreshWorkouts,
  } = useWorkoutHistory(userId);

  // Refresh when trigger changes (e.g., after new playlist generation or workout save)
  useEffect(() => {
    if (refreshTrigger && userId) {
      refreshPlaylists();
      refreshWorkouts();
    }
  }, [refreshTrigger, userId, refreshPlaylists, refreshWorkouts]);

  const handleDelete = async (e: React.MouseEvent, playlistId: string) => {
    e.stopPropagation();
    if (
      window.confirm('Ви впевнені, що хочете видалити цей плейлист з історії?')
    ) {
      try {
        await deletePlaylist(playlistId);
      } catch (err) {
        console.error('Failed to delete playlist:', err);
      }
    }
  };

  const handlePlaylistClick = (playlistId: string, spotifyUrl?: string) => {
    if (onPlaylistClick) {
      onPlaylistClick(playlistId, spotifyUrl);
    } else if (spotifyUrl) {
      window.open(spotifyUrl, '_blank');
    }
  };

  const handleWorkoutDelete = async (
    e: React.MouseEvent,
    workoutId: string
  ) => {
    e.stopPropagation();
    if (window.confirm('Ви впевнені, що хочете видалити цей воркаут?')) {
      try {
        await deleteWorkout(workoutId);
      } catch (err) {
        console.error('Failed to delete workout:', err);
      }
    }
  };

  const handleWorkoutClick = (workoutId: string) => {
    if (onWorkoutClick) {
      onWorkoutClick(workoutId);
    }
  };

  if (collapsed) {
    return (
      <div className='w-12 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col h-full items-center py-4'>
        <button
          onClick={onToggleCollapse}
          className='p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors'
          title='Розгорнути історію'
        >
          <svg
            className='w-5 h-5 text-gray-600 dark:text-gray-400'
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
      </div>
    );
  }

  return (
    <div className='w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col h-full transition-all duration-300'>
      <div className='p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center'>
        <h2 className='text-lg font-semibold text-gray-900 dark:text-white'>
          Історія
        </h2>
        {onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            className='p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors'
            title='Згорнути історію'
          >
            <svg
              className='w-5 h-5 text-gray-600 dark:text-gray-400'
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
        )}
      </div>

      <div className='flex-1 overflow-y-auto flex flex-col'>
        {/* Workouts Section - Top Half */}
        <div className='flex-1 overflow-y-auto p-4 border-b border-gray-200 dark:border-gray-700'>
          <h3 className='text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3'>
            Воркаути
          </h3>
          {workoutsLoading && (
            <div className='flex justify-center py-4'>
              <LoadingSpinner />
            </div>
          )}

          {workoutsError && (
            <div className='text-red-500 text-xs py-2'>
              Помилка завантаження
            </div>
          )}

          {!workoutsLoading && !workoutsError && workouts.length === 0 && (
            <div className='text-center text-gray-500 dark:text-gray-400 text-xs py-4'>
              <p>Немає збережених воркаутів</p>
            </div>
          )}

          {!workoutsLoading && !workoutsError && workouts.length > 0 && (
            <div className='space-y-2'>
              {workouts.map((workout) => {
                const workoutTypeLabels: Record<string, string> = {
                  steady: 'Стабільна',
                  progressive: 'Прогресивна',
                  intervals: 'Інтервальна',
                  fartlek: 'Фартлек',
                };
                const intensityLabels: Record<string, string> = {
                  low: 'Легка',
                  moderate: 'Середня',
                  high: 'Висока',
                };

                return (
                  <div
                    key={workout.id}
                    className='bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors group'
                    onClick={() => handleWorkoutClick(workout.id)}
                  >
                    <div className='flex justify-between items-start mb-2'>
                      <div className='flex-1 min-w-0'>
                        <p className='text-xs font-medium text-gray-900 dark:text-white truncate'>
                          {workoutTypeLabels[workout.type] || workout.type}
                        </p>
                        <p className='text-xs text-gray-500 dark:text-gray-400 truncate'>
                          {new Date(workout.created_at).toLocaleDateString(
                            'uk-UA',
                            {
                              day: 'numeric',
                              month: 'short',
                            }
                          )}
                        </p>
                      </div>
                      <button
                        onClick={(e) => handleWorkoutDelete(e, workout.id)}
                        className='opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700 transition-opacity ml-2'
                        title='Видалити'
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
                            d='M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16'
                          />
                        </svg>
                      </button>
                    </div>
                    <div className='text-xs text-gray-700 dark:text-gray-300'>
                      <p>
                        {workout.duration_minutes} хв •{' '}
                        {intensityLabels[workout.intensity] ||
                          workout.intensity}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Playlists Section - Bottom Half */}
        <div className='flex-1 overflow-y-auto p-4'>
          <h3 className='text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3'>
            Плейлисти
          </h3>
          {playlistsLoading && (
            <div className='flex justify-center py-4'>
              <LoadingSpinner />
            </div>
          )}

          {playlistsError && (
            <div className='text-red-500 text-xs py-2'>
              Помилка завантаження
            </div>
          )}

          {!playlistsLoading && !playlistsError && playlists.length === 0 && (
            <div className='text-center text-gray-500 dark:text-gray-400 text-xs py-4'>
              <p>Немає згенерованих плейлистів</p>
            </div>
          )}

          {!playlistsLoading && !playlistsError && playlists.length > 0 && (
            <div className='space-y-2'>
              {playlists.map((playlist) => (
                <div
                  key={playlist.id}
                  className='bg-gray-50 dark:bg-gray-700 rounded-lg p-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors group'
                  onClick={() =>
                    handlePlaylistClick(playlist.id, playlist.spotify_url)
                  }
                >
                  <div className='flex justify-between items-start mb-2'>
                    <div className='flex-1 min-w-0'>
                      <p className='text-xs text-gray-500 dark:text-gray-400 truncate'>
                        {new Date(playlist.created_at).toLocaleDateString(
                          'uk-UA',
                          {
                            day: 'numeric',
                            month: 'short',
                            hour: '2-digit',
                            minute: '2-digit',
                          }
                        )}
                      </p>
                    </div>
                    <button
                      onClick={(e) => handleDelete(e, playlist.id)}
                      className='opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700 transition-opacity ml-2'
                      title='Видалити'
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
                          d='M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16'
                        />
                      </svg>
                    </button>
                  </div>
                  <div className='text-xs text-gray-700 dark:text-gray-300'>
                    <p className='font-medium truncate'>
                      {playlist.total_tracks} треків
                    </p>
                    <p className='text-xs text-gray-500 dark:text-gray-400'>
                      {Math.round(playlist.total_duration_seconds / 60)} хв
                    </p>
                  </div>
                  {playlist.spotify_url && (
                    <div className='mt-2 flex items-center gap-1 text-xs text-green-600 dark:text-green-400'>
                      <svg
                        className='w-3 h-3'
                        fill='currentColor'
                        viewBox='0 0 24 24'
                      >
                        <path d='M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.84-.179-.84-.66 0-.359.24-.66.54-.779 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.24 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.239-1.26 11.28-1.02 15.239 1.621.539.3.719 1.02.42 1.56-.299.421-1.02.599-1.559.3z' />
                      </svg>
                      <span>Spotify</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
