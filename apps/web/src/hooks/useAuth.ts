import { useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { useAuthStore } from '../stores/authStore';

export function useAuth() {
  const {
    user,
    loading,
    spotifyAuthenticated,
    setUser,
    setLoading,
    setSpotifyAuthenticated,
  } = useAuthStore();

  const refreshSpotifyStatus = useCallback(async () => {
    const storedUserId = localStorage.getItem('spotify_user_id');
    if (storedUserId) {
      try {
        const status = await api.checkSpotifyAuthStatus(storedUserId);
        setSpotifyAuthenticated(status.authenticated);
        if (status.authenticated) {
          setUser({
            id: storedUserId,
            spotify_user_id: status.spotify_user_id,
          });
        }
      } catch (error) {
        console.error('Failed to check Spotify auth status:', error);
        setSpotifyAuthenticated(false);
        setUser(null);
        localStorage.removeItem('spotify_user_id');
      }
    }
    setLoading(false);
  }, [setUser, setLoading, setSpotifyAuthenticated]);

  useEffect(() => {
    // --- START: DEVELOPMENT MOCK ---
    if (import.meta.env.DEV) {
      const devUserId = 'dev_user_id_persistent';
      const devUser = { id: devUserId, spotify_user_id: 'dev_spotify_id' };
      setUser(devUser);
      setSpotifyAuthenticated(true);
      setLoading(false);
      return; // Skip real auth check in dev
    }
    // --- END: DEVELOPMENT MOCK ---

    refreshSpotifyStatus();
  }, [refreshSpotifyStatus]);

  const signInWithSpotify = async () => {
    try {
      if (import.meta.env.DEV) {
        const devUserId = 'dev_user_id_persistent';
        localStorage.setItem('spotify_user_id', devUserId);
        const devUser = { id: devUserId, spotify_user_id: 'dev_spotify_id' };
        setUser(devUser);
        setSpotifyAuthenticated(true);
        setLoading(false);
        // No longer reloading the page
      } else {
        setLoading(true);
        const { auth_url } = await api.initiateSpotifyAuth();
        window.location.href = auth_url;
      }
    } catch (error) {
      console.error('Failed to initiate Spotify auth:', error);
      setLoading(false);
      throw error;
    }
  };

  const signOut = () => {
    localStorage.removeItem('spotify_user_id');
    setUser(null);
    setSpotifyAuthenticated(false);
  };

  return {
    user,
    loading,
    spotifyAuthenticated,
    signInWithSpotify,
    signOut,
    refreshSpotifyStatus,
  };
}
