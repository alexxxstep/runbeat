import { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { api } from '../../services/api';
import { Button } from './Button';

export function SpotifyConnectBanner() {
  const { user, signInWithSpotify } = useAuth();
  const [spotifyConnected, setSpotifyConnected] = useState<boolean | null>(
    null
  );
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkSpotifyStatus = async () => {
      if (!user?.id) {
        setLoading(false);
        return;
      }

      try {
        const status = await api.checkSpotifyAuthStatus(user.id);
        setSpotifyConnected(status.authenticated);
      } catch (error) {
        console.error('Failed to check Spotify status:', error);
        setSpotifyConnected(false);
      } finally {
        setLoading(false);
      }
    };

    checkSpotifyStatus();
  }, [user?.id]);

  const handleConnectSpotify = async () => {
    try {
      await signInWithSpotify();
    } catch (error) {
      console.error('Failed to connect Spotify:', error);
    }
  };

  if (loading || spotifyConnected === null || spotifyConnected) {
    return null;
  }

  return (
    <div className='bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-400 p-4 mb-4'>
      <div className='flex items-center justify-between'>
        <div className='flex items-center'>
          <svg
            className='w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-2'
            fill='none'
            stroke='currentColor'
            viewBox='0 0 24 24'
          >
            <path
              strokeLinecap='round'
              strokeLinejoin='round'
              strokeWidth={2}
              d='M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
            />
          </svg>
          <p className='text-sm text-yellow-800 dark:text-yellow-200'>
            Підключіть Spotify, щоб створювати плейлисти в вашому акаунті
          </p>
        </div>
        <Button
          onClick={handleConnectSpotify}
          className='ml-4 bg-[#1DB954] hover:bg-[#1ed760] text-white text-sm px-4 py-2'
        >
          Підключити Spotify
        </Button>
      </div>
    </div>
  );
}
