import { useEffect, useRef } from 'react';
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
  activeWorkoutId?: string | null; // ID of currently active workout
}

export function PlaylistHistorySidebar({
  userId,
  onPlaylistClick,
  onWorkoutClick,
  refreshTrigger,
  collapsed = false,
  onToggleCollapse,
  activeWorkoutId,
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

  // Use ref to track the last timeout and prevent multiple simultaneous refreshes
  const refreshTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastRefreshTriggerRef = useRef<number>(0);

  // Refresh when trigger changes (e.g., after new playlist generation or workout save)
  // Use debounce to avoid multiple rapid refreshes
  useEffect(() => {
    if (refreshTrigger !== undefined && refreshTrigger > 0 && userId) {
      // Only refresh if trigger actually changed
      if (refreshTrigger === lastRefreshTriggerRef.current) {
        return;
      }

      lastRefreshTriggerRef.current = refreshTrigger;

      // Clear any existing timeout
      if (refreshTimeoutRef.current) {
        clearTimeout(refreshTimeoutRef.current);
      }

      // Debounce: wait a bit before refreshing to avoid rapid successive calls
      refreshTimeoutRef.current = setTimeout(() => {
        refreshPlaylists();
        refreshWorkouts();
        refreshTimeoutRef.current = null;
      }, 500); // Increased delay to 500ms to batch multiple rapid updates

      return () => {
        if (refreshTimeoutRef.current) {
          clearTimeout(refreshTimeoutRef.current);
          refreshTimeoutRef.current = null;
        }
      };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshTrigger, userId]); // Removed refreshPlaylists and refreshWorkouts from dependencies

  const handleDelete = async (e: React.MouseEvent, playlistId: string) => {
    e.stopPropagation();
    try {
      await deletePlaylist(playlistId);
    } catch (err) {
      console.error('Failed to delete playlist:', err);
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
    try {
      await deleteWorkout(workoutId);
    } catch (err) {
      console.error('Failed to delete workout:', err);
    }
  };

  const handleWorkoutClick = (workoutId: string) => {
    if (onWorkoutClick) {
      onWorkoutClick(workoutId);
    }
  };

  const sidebarWidthClass = collapsed ? 'w-12' : 'w-full';
  const contentOpacityClass = collapsed ? 'opacity-0' : 'opacity-100';
  const contentVisibilityClass = collapsed ? 'invisible' : 'visible';

    return (
    <div
      className={`bg-app-surface border-r border-app-border flex flex-col h-full transition-all duration-300 ease-in-out ${sidebarWidthClass} min-w-0`}
    >
      {/* Header */}
      <div className={`${collapsed ? 'p-2' : 'p-4'} border-b border-app-border flex ${collapsed ? 'justify-center' : 'justify-between'} items-center flex-shrink-0 relative`}>
        {!collapsed && (
          <h2
            className={`text-title-2 font-display font-bold text-app-text transition-opacity duration-300 ${contentOpacityClass} ${contentVisibilityClass}`}
          >
            Історія
          </h2>
        )}
        <button
          onClick={onToggleCollapse}
          className={`${collapsed ? 'p-2 w-full flex justify-center' : 'p-2'} hover:bg-app-surface-light rounded-full transition-all duration-300 ease-in-out flex-shrink-0 z-10`}
          title={collapsed ? 'Розгорнути' : 'Згорнути'}
        >
          <svg
            className={`${collapsed ? 'w-6 h-6' : 'w-5 h-5'} text-app-text-secondary transform transition-transform duration-300 ${
              collapsed ? 'rotate-180' : 'rotate-0'
            }`}
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

      {/* Main Content */}
      <div
        className={`flex-1 overflow-y-auto overflow-x-hidden flex flex-col transition-opacity duration-300 ${contentOpacityClass} ${contentVisibilityClass}`}
      >
        {/* Workouts Section - Top Half */}
        <div className='flex-1 overflow-y-auto p-4 border-b border-app-border'>
          <h3 className='text-headline font-semibold text-app-text mb-4'>
            Воркаути
          </h3>
          {workoutsLoading && (
            <div className='flex justify-center py-4'>
              <LoadingSpinner />
            </div>
          )}

          {workoutsError && (
            <div className='text-red-500 text-subhead py-2'>
              Помилка завантаження
            </div>
          )}

          {!workoutsLoading && !workoutsError && workouts.length === 0 && (
            <div className='text-center text-app-text-tertiary text-body py-4'>
              <p>Немає збережених воркаутів</p>
            </div>
          )}

          {!workoutsLoading && !workoutsError && workouts.length > 0 && (
            <div className='space-y-3'>
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
                const isActive = activeWorkoutId === workout.id;

                // Get workout type name with full label
                const workoutType = workoutTypeLabels[workout.type] || workout.type;
                const workoutTypeFullName = workoutType === 'Прогресивна'
                  ? 'Прогресивна пробіжка'
                  : workoutType === 'Стабільна'
                  ? 'Стабільна пробіжка'
                  : workoutType === 'Інтервальна'
                  ? 'Інтервальна пробіжка'
                  : 'Фартлек пробіжка';

                // Format duration
                const hours = Math.floor(workout.duration_minutes / 60);
                const minutes = workout.duration_minutes % 60;
                const durationText = hours > 0
                  ? `${hours} год ${minutes} хв`
                  : `${minutes} хв`;

                // Check if workout has genres
                const hasGenres = workout.genres && workout.genres.length > 0;
                const genresText = hasGenres
                  ? workout.genres!.slice(0, 3).join(', ') + (workout.genres!.length > 3 ? '...' : '')
                  : null;

                // Check if workout has interval stages
                const hasStages = workout.interval_stages && workout.interval_stages.length > 0;
                const stagesCount = hasStages ? workout.interval_stages!.length : 0;

                return (
                  <div
                    key={workout.id}
                    className={`rounded-xl p-4 cursor-pointer transition-all group border ${
                      isActive
                        ? 'bg-app-accent border-app-accent shadow-lg transform scale-[1.01]'
                        : 'bg-app-surface-light border-app-border hover:bg-app-surface hover:border-app-border-light'
                    }`}
                    onClick={() => handleWorkoutClick(workout.id)}
                  >
                    <div className='flex justify-between items-start mb-2'>
                      <div className='flex-1 min-w-0'>
                        <div className='flex items-center gap-2 mb-2'>
                          <p
                            className={`text-headline font-bold truncate ${
                              isActive
                                ? 'text-white'
                                : 'text-app-text'
                            }`}
                          >
                            {workoutTypeFullName}
                          </p>
                          {isActive && (
                            <span className='flex-shrink-0 px-2 py-1 text-caption font-semibold bg-white/20 text-white rounded-full'>
                              ✓ Активний
                            </span>
                          )}
                        </div>
                        <p
                          className={`text-caption mb-3 ${
                            isActive
                              ? 'text-white/80'
                              : 'text-app-text-secondary'
                          }`}
                        >
                          {new Date(workout.created_at).toLocaleDateString(
                            'uk-UA',
                            {
                              day: 'numeric',
                              month: 'short',
                              year: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            }
                          )}
                        </p>
                      </div>
                      <button
                        onClick={(e) => handleWorkoutDelete(e, workout.id)}
                        className={`opacity-0 group-hover:opacity-100 transition-opacity ml-2 p-1 rounded ${
                          isActive
                            ? 'text-white/90 hover:text-white hover:bg-white/20'
                            : 'text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20'
                        }`}
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
                    <div
                      className={`text-subhead space-y-2 ${
                        isActive
                          ? 'text-white/90'
                          : 'text-app-text-secondary'
                      }`}
                    >
                      <div className='flex items-center gap-2 flex-wrap'>
                        <span className='font-semibold flex items-center gap-1'>
                          ⏱️ <span>{durationText}</span>
                        </span>
                        <span className='font-semibold flex items-center gap-1'>
                          💪 <span>{intensityLabels[workout.intensity] || workout.intensity}</span>
                        </span>
                      </div>
                      {workout.hr_zones && workout.hr_zones.length >= 2 && (
                        <p className='flex items-center gap-1'>
                          <span>❤️</span>
                          <span>ЧСС: {workout.hr_zones[0]} - {workout.hr_zones[1]} уд/хв</span>
                        </p>
                      )}
                      {hasGenres && (
                        <p className={`flex items-start gap-1 ${isActive ? 'text-blue-100' : 'text-gray-600 dark:text-gray-400'}`}>
                          <span>🎵</span>
                          <span className='truncate'>{genresText}</span>
                        </p>
                      )}
                      {hasStages && (
                        <p className={`flex items-center gap-1 ${isActive ? 'text-blue-100' : 'text-gray-600 dark:text-gray-400'}`}>
                          <span>📊</span>
                          <span>Інтервали: {stagesCount} етапів</span>
                        </p>
                      )}
                      {workout.prompt && (
                        <p className={`flex items-start gap-1 ${isActive ? 'text-blue-100' : 'text-gray-600 dark:text-gray-400'}`} title={workout.prompt}>
                          <span>💬</span>
                          <span className='truncate italic'>{workout.prompt.length > 50 ? workout.prompt.substring(0, 50) + '...' : workout.prompt}</span>
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Playlists Section - Bottom Half */}
        <div className='flex-1 overflow-y-auto p-4'>
          <h3 className='text-headline font-semibold text-app-text mb-4'>
            Плейлисти
          </h3>
          {playlistsLoading && (
            <div className='flex justify-center py-4'>
              <LoadingSpinner />
            </div>
          )}

          {playlistsError && (
            <div className='text-red-500 text-subhead py-2'>
              Помилка завантаження
            </div>
          )}

          {!playlistsLoading && !playlistsError && playlists.length === 0 && (
            <div className='text-center text-app-text-tertiary text-body py-4'>
              <p>Немає згенерованих плейлистів</p>
            </div>
          )}

          {!playlistsLoading && !playlistsError && playlists.length > 0 && (
            <div className='space-y-3'>
              {playlists.map((playlist) => (
                <div
                  key={playlist.id}
                  className='bg-app-surface-light rounded-xl p-4 cursor-pointer hover:bg-app-surface transition-colors group border border-app-border'
                  onClick={() =>
                    handlePlaylistClick(playlist.id, playlist.spotify_url)
                  }
                >
                  <div className='flex justify-between items-start mb-2'>
                    <div className='flex-1 min-w-0'>
                      <p className='text-caption text-app-text-tertiary truncate'>
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
                      className='opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-400 transition-opacity ml-2'
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
                  <div className='text-subhead text-app-text-secondary'>
                    {playlist.workout ? (
                      <>
                        <p className='font-medium truncate'>
                          {(() => {
                            const workoutTypeLabels: Record<string, string> = {
                              steady: 'Стабільна',
                              progressive: 'Прогресивна',
                              intervals: 'Інтервальна',
                              fartlek: 'Фартлек',
                            };
                            const workoutType = workoutTypeLabels[playlist.workout.type] || playlist.workout.type;
                            const workoutName = workoutType === 'Прогресивна'
                              ? 'Прогресивна пробіжка'
                              : workoutType === 'Стабільна'
                              ? 'Стабільна пробіжка'
                              : workoutType === 'Інтервальна'
                              ? 'Інтервальна пробіжка'
                              : 'Фартлек пробіжка';
                            return `RunBeat: ${workoutName} (${playlist.workout.duration_minutes}хв) - ${playlist.total_tracks} треків ${Math.round(playlist.total_duration_seconds / 60)}хв`;
                          })()}
                        </p>
                      </>
                    ) : (
                      <>
                        <p className='font-medium truncate'>
                          {playlist.total_tracks} треків
                        </p>
                        <p className='text-xs text-gray-500 dark:text-gray-400'>
                          {Math.round(playlist.total_duration_seconds / 60)} хв
                        </p>
                      </>
                    )}
                  </div>
                  {playlist.spotify_url && (
                    <div className='mt-2 flex items-center gap-1 text-caption text-app-accent'>
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
