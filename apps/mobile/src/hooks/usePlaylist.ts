/**
 * Playlist hook for RunBeat Mobile App
 */
import { useState, useCallback } from 'react';
import { api } from '../services/api';
import { Playlist } from '../types';

export function usePlaylist() {
  const [playlist, setPlaylist] = useState<Playlist | null>(null);
  const [history, setHistory] = useState<Playlist[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadHistory = useCallback(async (userId: string, limit = 10) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.getPlaylistHistory(userId, limit);
      setHistory(response.playlists || []);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load history';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const openInSpotify = useCallback((spotifyUrl: string) => {
    // Open Spotify URL (will open in Spotify app if installed)
    const url = spotifyUrl || playlist?.spotify_url;
    if (url) {
      // Use Linking to open URL
      import('expo-linking').then((Linking) => {
        Linking.openURL(url);
      });
    }
  }, [playlist]);

  return {
    playlist,
    setPlaylist,
    history,
    isLoading,
    error,
    loadHistory,
    openInSpotify,
  };
}

