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
  workout?: {
    id: string;
    type: string;
    duration_minutes: number;
    intensity: string;
    hr_zones: number[];
  } | null;
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
        setError(err instanceof Error ? err.message : 'Failed to load history');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [userId]);

  const deletePlaylist = async (playlistId: string) => {
    if (!userId) {
      return;
    }

    try {
      await api.deletePlaylist(playlistId, userId);
      // Remove from local state
      setPlaylists((prev) => prev.filter((p) => p.id !== playlistId));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to delete playlist'
      );
      throw err;
    }
  };

  const refresh = async () => {
    if (!userId) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.getPlaylistHistory(userId);
      setPlaylists(response.playlists || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  return { playlists, loading, error, deletePlaylist, refresh };
}
