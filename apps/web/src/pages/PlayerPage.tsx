import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { usePlaylist } from '../hooks/usePlaylist';
import { TrackCard } from '../components/Player/TrackCard';
import { LoadingSpinner } from '../components/Shared/LoadingSpinner';
import { Button } from '../components/Shared/Button';

export function PlayerPage() {
  const { playlistId } = useParams<{ playlistId?: string }>();
  const navigate = useNavigate();
  const { playlist, loading, error } = usePlaylist(playlistId);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !playlist) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <p className="text-red-500 mb-4">Помилка завантаження плейлисту</p>
        <Button onClick={() => navigate('/')}>Повернутися до чату</Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-6">
        <Button onClick={() => navigate('/')} variant="secondary">
          ← Назад
        </Button>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-2">Ваш плейлист</h1>
          <p className="text-gray-600 dark:text-gray-400">
            {playlist.total_tracks} треків •{' '}
            {Math.round(playlist.total_duration / 60)} хвилин
          </p>
        </div>

        {playlist.spotify_url && (
          <div className="mb-6">
            <a
              href={playlist.spotify_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block"
            >
              <Button>Відкрити в Spotify</Button>
            </a>
          </div>
        )}

        <div className="space-y-2">
          {playlist.tracks.map((track, index) => (
            <TrackCard key={track.id} track={track} index={index + 1} />
          ))}
        </div>
      </div>
    </div>
  );
}

