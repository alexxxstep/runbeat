import { useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { useAuthStore } from '../stores/authStore';

export function useAuth() {
  const navigate = useNavigate();
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
      setLoading(true);
      const { auth_url } = await api.initiateSpotifyAuth();
      window.location.href = auth_url;
    } catch (error) {
      console.error('Failed to initiate Spotify auth:', error);
      setLoading(false);
      throw error;
    }
  };

  const signOut = useCallback(async () => {
    try {
      // Get user ID before clearing state
      const userId = user?.id || localStorage.getItem('spotify_user_id');

      // Call backend logout endpoint to revoke tokens
      if (userId) {
        try {
          await api.logout(userId);
          console.log('Backend logout successful');
        } catch (error) {
          console.error(
            'Backend logout failed, continuing with local cleanup:',
            error
          );
        }
      }

      // Clear all localStorage data
      localStorage.clear();

      // Clear session storage as well
      sessionStorage.clear();

      // Reset auth state
      setUser(null);
      setSpotifyAuthenticated(false);

      // Navigate to login
      navigate('/login', { replace: true });
    } catch (error) {
      console.error('Error during logout:', error);
      // Even if there's an error, clear local data and navigate
      localStorage.clear();
      sessionStorage.clear();
      setUser(null);
      setSpotifyAuthenticated(false);
      navigate('/login', { replace: true });
    }
  }, [user, navigate, setUser, setSpotifyAuthenticated]);

  return {
    user,
    loading,
    spotifyAuthenticated,
    signInWithSpotify,
    signOut,
    refreshSpotifyStatus,
  };
}
