import { useState } from 'react';
import type { Message } from '../../types';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const needsClarification = message.workout?.needs_clarification;
  const [showAllTracks, setShowAllTracks] = useState(false);

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 px-2 md:px-0`}>
      <div
        className={`max-w-[85%] sm:max-w-xs lg:max-w-md px-3 md:px-4 py-2 rounded-lg ${
          isUser
            ? 'bg-blue-600 text-white'
            : needsClarification
            ? 'bg-yellow-100 dark:bg-yellow-900/30 border-2 border-yellow-400 dark:border-yellow-600 text-gray-900 dark:text-gray-100'
            : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
        }`}
      >
        {/* Clarification indicator */}
        {needsClarification && (
          <div className='mb-2 pb-2 border-b border-yellow-400 dark:border-yellow-600'>
            <div className='flex items-start gap-2'>
              <svg
                className='w-4 h-4 mt-0.5 flex-shrink-0'
                fill='currentColor'
                viewBox='0 0 20 20'
              >
                <path
                  fillRule='evenodd'
                  d='M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z'
                  clipRule='evenodd'
                />
              </svg>
              <div className='flex-1'>
                <p className='text-xs font-semibold text-yellow-800 dark:text-yellow-300 mb-1'>
                  Потрібне уточнення
                </p>
                {message.workout?.clarification_question && (
                  <p className='text-xs text-yellow-700 dark:text-yellow-400 italic'>
                    {message.workout.clarification_question}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
        {/* Render workout info if available */}
        {message.workout && (
          <div className='mb-3 pb-3 border-b border-gray-300 dark:border-gray-600'>
            <div className='text-sm space-y-1'>
              <p>
                <strong>Тип тренування:</strong>{' '}
                {message.workout.type === 'steady'
                  ? 'Стабільна'
                  : message.workout.type === 'progressive'
                  ? 'Прогресивна'
                  : message.workout.type === 'intervals'
                  ? 'Інтервальна'
                  : 'Фартлек'}
              </p>
              <p>
                <strong>Тривалість:</strong> {message.workout.duration_minutes}{' '}
                хвилин
              </p>
              <p>
                <strong>Інтенсивність:</strong>{' '}
                {message.workout.intensity === 'low'
                  ? 'Легка'
                  : message.workout.intensity === 'moderate'
                  ? 'Середня'
                  : 'Висока'}
              </p>
              <p>
                <strong>ЧСС:</strong> {message.workout.hr_zones[0]} -{' '}
                {message.workout.hr_zones[1]} уд/хв
              </p>
            </div>
          </div>
        )}
        <p className='text-sm whitespace-pre-line'>{message.content}</p>

        {/* Display playlist info if available */}
        {message.playlist && (
          <div className='mt-3 pt-3 border-t border-gray-300 dark:border-gray-600'>
            <div className='mb-2'>
              <p className='text-sm font-semibold mb-1'>
                🎵 Плейлист готовий!
              </p>
              {message.playlist.total_tracks && (
                <p className='text-xs opacity-75'>
                  {message.playlist.total_tracks} треків •{' '}
                  {Math.round(message.playlist.total_duration / 60)} хв
                </p>
              )}
            </div>

            {/* Show tracks list if available */}
            {message.playlist.tracks && message.playlist.tracks.length > 0 && (
              <div className='mb-2'>
                <div className='max-h-64 overflow-y-auto space-y-1 mb-2'>
                  {(showAllTracks
                    ? message.playlist.tracks
                    : message.playlist.tracks.slice(0, 5)
                  ).map((track, idx) => {
                    // Get phase indicator from track metadata if available
                    const phase = (track as any).phase || 'main';
                    const phaseColors: Record<string, string> = {
                      'warm-up': 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700',
                      'main': 'bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-700',
                      'cool-down': 'bg-purple-100 dark:bg-purple-900/30 border-purple-300 dark:border-purple-700',
                    };
                    const phaseLabels: Record<string, string> = {
                      'warm-up': '🔥 Розминка',
                      'main': '💪 Основна',
                      'cool-down': '🧘 Заминка',
                    };

                    return (
                      <div
                        key={track.id || idx}
                        className={`text-xs py-1.5 px-2 rounded border-l-2 ${
                          phaseColors[phase] || 'bg-gray-100 dark:bg-gray-800'
                        }`}
                      >
                        <div className='flex items-center justify-between'>
                          <div className='flex-1 min-w-0'>
                            <div className='flex items-center gap-1 mb-0.5'>
                              <span className='font-medium truncate'>{track.name}</span>
                              <span className='text-[10px] opacity-60'>
                                {phaseLabels[phase] || phase}
                              </span>
                            </div>
                            <span className='opacity-75 text-[11px] truncate block'>
                              {track.artist}
                            </span>
                          </div>
                          <div className='flex items-center gap-2 ml-2'>
                            {track.bpm && (
                              <span className='text-[10px] opacity-60 whitespace-nowrap'>
                                {Math.round(track.bpm)} BPM
                              </span>
                            )}
                            {track.duration_ms && (
                              <span className='text-[10px] opacity-50 whitespace-nowrap'>
                                {Math.floor(track.duration_ms / 60000)}:
                                {String(
                                  Math.floor((track.duration_ms % 60000) / 1000)
                                ).padStart(2, '0')}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                {message.playlist.tracks.length > 5 && (
                  <button
                    onClick={() => setShowAllTracks(!showAllTracks)}
                    className='text-xs text-blue-600 dark:text-blue-400 hover:underline w-full text-center py-1'
                  >
                    {showAllTracks
                      ? '▲ Показати менше'
                      : `▼ Показати всі ${message.playlist.tracks.length} треків`}
                  </button>
                )}
              </div>
            )}

            {message.playlist.spotify_url ? (
              <a
                href={message.playlist.spotify_url}
                target='_blank'
                rel='noopener noreferrer'
                className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isUser
                    ? 'bg-blue-500 hover:bg-blue-400 text-white'
                    : 'bg-[#1DB954] hover:bg-[#1ed760] text-white'
                }`}
              >
                <svg
                  className='w-4 h-4'
                  fill='currentColor'
                  viewBox='0 0 24 24'
                >
                  <path d='M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.84-.179-.84-.66 0-.359.24-.66.54-.779 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.24 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.239-1.26 11.28-1.02 15.239 1.621.539.3.719 1.02.42 1.56-.299.421-1.02.599-1.559.3z' />
                </svg>
                Відкрити в Spotify
              </a>
            ) : message.playlist.playlist_id ? (
              <a
                href={`/player/${message.playlist.playlist_id}`}
                className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isUser
                    ? 'bg-blue-500 hover:bg-blue-400 text-white'
                    : 'bg-gray-600 hover:bg-gray-500 text-white'
                }`}
              >
                Переглянути плейлист
              </a>
            ) : (
              <p className='text-xs opacity-60 italic'>
                Плейлист згенеровано. Потрібно створити в Spotify для відкриття.
              </p>
            )}
          </div>
        )}

        <p
          className={`text-xs mt-1 ${
            isUser ? 'text-blue-100' : 'text-gray-500'
          }`}
        >
          {message.timestamp.toLocaleTimeString('uk-UA', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  );
}
