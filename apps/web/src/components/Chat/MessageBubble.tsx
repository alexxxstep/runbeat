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
        className={`max-w-[85%] sm:max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
          isUser
            ? 'bg-app-accent text-white'
            : needsClarification
            ? 'bg-app-surface border-2 border-app-accent text-app-text'
            : 'bg-app-surface border border-app-border text-app-text'
        }`}
      >
        {/* Clarification indicator */}
        {needsClarification && (
          <div className='mb-3 pb-3 border-b border-app-border'>
            <div className='flex items-start gap-2'>
              <svg
                className='w-5 h-5 mt-0.5 flex-shrink-0 text-app-accent'
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
                <p className='text-subhead font-semibold text-app-text mb-1'>
                  Потрібне уточнення
                </p>
                {message.workout?.clarification_question && (
                  <p className='text-body text-app-text-secondary italic'>
                    {message.workout.clarification_question}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
        {/* Render workout info if available */}
        {message.workout && (
          <div className='mb-3 pb-3 border-b border-app-border'>
            <div className='text-body space-y-2 text-app-text-secondary'>
              <p>
                <strong className='text-app-text'>Тип тренування:</strong>{' '}
                {message.workout.type === 'steady'
                  ? 'Стабільна'
                  : message.workout.type === 'progressive'
                  ? 'Прогресивна'
                  : message.workout.type === 'intervals'
                  ? 'Інтервальна'
                  : 'Фартлек'}
              </p>
              <p>
                <strong className='text-app-text'>Тривалість:</strong> {message.workout.duration_minutes} хв
              </p>
              <p>
                <strong className='text-app-text'>Інтенсивність:</strong>{' '}
                {message.workout.intensity === 'low'
                  ? 'Легка'
                  : message.workout.intensity === 'moderate'
                  ? 'Середня'
                  : 'Висока'}
              </p>
              <p>
                <strong className='text-app-text'>ЧСС:</strong> {message.workout.hr_zones[0]} -{' '}
                {message.workout.hr_zones[1]} уд/хв
              </p>
            </div>
          </div>
        )}
        <p className='text-body whitespace-pre-line text-app-text-secondary'>{message.content}</p>

        {/* Display playlist info if available */}
        {message.playlist && (
          <div className='mt-3 pt-3 border-t border-app-border'>
            <div className='mb-3'>
              <p className='text-headline font-semibold mb-1 text-app-text'>
                🎵 Плейлист готовий!
              </p>
              {message.playlist.total_tracks && (
                <p className='text-subhead text-app-text-secondary'>
                  {message.playlist.total_tracks} треків •{' '}
                  {Math.round(message.playlist.total_duration / 60)} хв
                </p>
              )}
            </div>

            {/* Show tracks list if available */}
            {message.playlist.tracks && message.playlist.tracks.length > 0 && (
              <div className='mb-3'>
                <div className='max-h-64 overflow-y-auto space-y-2 mb-3'>
                  {(showAllTracks
                    ? message.playlist.tracks
                    : message.playlist.tracks.slice(0, 5)
                  ).map((track, idx) => {
                    // Get phase indicator from track metadata if available
                    const phase = (track as any).phase || 'main';
                    const phaseColors: Record<string, string> = {
                      'warm-up': 'bg-app-surface-light border-app-accent/50',
                      'main': 'bg-app-surface-light border-app-accent',
                      'cool-down': 'bg-app-surface-light border-app-accent/30',
                    };
                    const phaseLabels: Record<string, string> = {
                      'warm-up': '🔥 Розминка',
                      'main': '💪 Основна',
                      'cool-down': '🧘 Заминка',
                    };

                    return (
                      <div
                        key={track.id || idx}
                        className={`text-subhead py-2 px-3 rounded-lg border-l-4 ${
                          phaseColors[phase] || 'bg-app-surface-light border-app-border'
                        }`}
                      >
                        <div className='flex items-center justify-between'>
                          <div className='flex-1 min-w-0'>
                            <div className='flex items-center gap-2 mb-1'>
                              <span className='font-medium truncate text-app-text'>{track.name}</span>
                              <span className='text-caption text-app-text-tertiary'>
                                {phaseLabels[phase] || phase}
                              </span>
                            </div>
                            <span className='text-subhead text-app-text-secondary truncate block'>
                              {track.artist}
                            </span>
                          </div>
                          <div className='flex items-center gap-2 ml-2'>
                            {track.bpm && (
                              <span className='text-caption text-app-text-tertiary whitespace-nowrap'>
                                {Math.round(track.bpm)} BPM
                              </span>
                            )}
                            {track.duration_ms && (
                              <span className='text-caption text-app-text-tertiary whitespace-nowrap'>
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
                    className='text-subhead text-app-accent hover:text-app-accent-hover hover:underline w-full text-center py-2'
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
                className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-body font-semibold transition-colors ${
                  isUser
                    ? 'bg-app-accent hover:bg-app-accent-hover text-white'
                    : 'bg-[#1DB954] hover:bg-[#1ed760] text-white'
                }`}
              >
                <svg
                  className='w-5 h-5'
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
                className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-body font-semibold transition-colors ${
                  isUser
                    ? 'bg-app-accent hover:bg-app-accent-hover text-white'
                    : 'bg-app-surface hover:bg-app-surface-light text-app-text border border-app-border'
                }`}
              >
                Переглянути плейлист
              </a>
            ) : (
              <p className='text-subhead text-app-text-tertiary italic'>
                Плейлист згенеровано. Потрібно створити в Spotify для відкриття.
              </p>
            )}
          </div>
        )}

        <p
          className={`text-caption mt-2 ${
            isUser ? 'text-white/70' : 'text-app-text-tertiary'
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
