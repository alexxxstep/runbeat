/**
 * Spotify authentication hook for RunBeat Mobile App
 */
import { useState, useCallback } from 'react';
import { spotifyAuth } from '../services/spotify';

export function useSpotify() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const authenticate = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await spotifyAuth.authenticate();
      if (result.success) {
        setIsAuthenticated(true);
        return result;
      } else {
        setError(result.error || 'Authentication failed');
        return null;
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Authentication error';
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const checkAuthStatus = useCallback(async (userId: string) => {
    setIsLoading(true);
    try {
      const authenticated = await spotifyAuth.checkAuthStatus(userId);
      setIsAuthenticated(authenticated);
      return authenticated;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check status');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    isAuthenticated,
    isLoading,
    error,
    authenticate,
    checkAuthStatus,
  };
}

