import type { Message } from '../../types';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
        }`}
      >
        <p className='text-sm'>{message.content}</p>

        {/* Display playlist link if available */}
        {message.playlist && (
          <div className='mt-3 pt-3 border-t border-gray-300 dark:border-gray-600'>
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
            ) : null}
            {message.playlist.total_tracks && (
              <p className='text-xs mt-2 opacity-75'>
                {message.playlist.total_tracks} треків •{' '}
                {Math.round(message.playlist.total_duration / 60)} хв
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
