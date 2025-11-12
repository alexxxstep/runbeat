import { useState, useEffect } from 'react';
import { api } from '../services/api';

export interface User {
  id: string;
  email?: string;
  spotify_user_id?: string;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [spotifyAuthenticated, setSpotifyAuthenticated] = useState(false);

  const checkSpotifyAuth = async (userId: string) => {
    try {
      setLoading(true);
      const status = await api.checkSpotifyAuthStatus(userId);
      setSpotifyAuthenticated(status.authenticated);
      if (status.authenticated) {
        setUser({
          id: userId,
          spotify_user_id: status.spotify_user_id,
        });
      }
    } catch (error) {
      console.error('Failed to check Spotify auth status:', error);
      setSpotifyAuthenticated(false);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Check if there's a user_id in localStorage (from Spotify callback)
    const storedUserId = localStorage.getItem('spotify_user_id');
    if (storedUserId) {
      checkSpotifyAuth(storedUserId);
    } else {
      setLoading(false);
    }
  }, []);

  const signInWithSpotify = async () => {
    try {
      const { auth_url } = await api.initiateSpotifyAuth();
      window.location.href = auth_url;
    } catch (error) {
      console.error('Failed to initiate Spotify auth:', error);
      throw error;
    }
  };

  const signOut = async () => {
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
    refreshSpotifyStatus: async () => {
      const storedUserId = localStorage.getItem('spotify_user_id');
      if (storedUserId) {
        await checkSpotifyAuth(storedUserId);
      }
    },
  };
}
