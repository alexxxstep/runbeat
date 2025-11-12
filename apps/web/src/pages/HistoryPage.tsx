import { useEffect, useState } from 'react';
import { usePlaylistHistory } from '../hooks/usePlaylistHistory';
import { LoadingSpinner } from '../components/Shared/LoadingSpinner';

export function HistoryPage() {
  const { playlists, loading, error } = usePlaylistHistory();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-red-500">Помилка завантаження історії</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">Історія плейлистів</h1>

      {playlists.length === 0 ? (
        <div className="text-center text-gray-500 py-12">
          <p>У вас ще немає створених плейлистів</p>
        </div>
      ) : (
        <div className="space-y-4">
          {playlists.map((playlist) => (
            <div
              key={playlist.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-semibold mb-2">
                    Плейлист від{' '}
                    {new Date(playlist.created_at).toLocaleDateString('uk-UA')}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    {playlist.total_tracks} треків •{' '}
                    {Math.round(playlist.total_duration_seconds / 60)} хвилин
                  </p>
                  {playlist.generation_time_seconds && (
                    <p className="text-sm text-gray-500 mt-1">
                      Згенеровано за {playlist.generation_time_seconds}с
                    </p>
                  )}
                </div>
                {playlist.spotify_url && (
                  <a
                    href={playlist.spotify_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800"
                  >
                    Відкрити в Spotify →
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

