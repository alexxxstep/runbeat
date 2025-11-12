import { useState, useEffect } from 'react';
import { api } from '../services/api';

interface PlaylistHistoryItem {
  id: string;
  workout_id?: string;
  spotify_playlist_id: string;
  spotify_url: string;
  total_tracks: number;
  total_duration_seconds: number;
  generation_time_seconds?: number;
  shared: boolean;
  share_url?: string;
  created_at: string;
}

export function usePlaylistHistory(userId?: string) {
  const [playlists, setPlaylists] = useState<PlaylistHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) {
      return;
    }

    const fetchHistory = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await api.getPlaylistHistory(userId);
        setPlaylists(response.playlists || []);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : 'Failed to load history'
        );
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [userId]);

  return { playlists, loading, error };
}

