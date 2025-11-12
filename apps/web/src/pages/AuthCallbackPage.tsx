import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { LoadingSpinner } from '../components/Shared/LoadingSpinner';

export function AuthCallbackPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // Check if this is Spotify callback (has user_id and spotify_user_id params)
        const userId = searchParams.get('user_id');
        const spotifyUserId = searchParams.get('spotify_user_id');

        if (userId && spotifyUserId) {
          // This is Spotify OAuth callback
          // Store user_id in localStorage for future checks
          localStorage.setItem('spotify_user_id', userId);

          // Successfully authenticated with Spotify
          navigate('/');
          return;
        }

        // If no params, redirect to login
        navigate('/login?error=no_params');
      } catch (error) {
        console.error('Failed to handle auth callback:', error);
        navigate('/login?error=callback_failed');
      }
    };

    handleAuthCallback();
  }, [navigate, searchParams]);

  return (
    <div className='flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900'>
      <div className='text-center'>
        <LoadingSpinner />
        <p className='mt-4 text-gray-600 dark:text-gray-400'>
          Завершення авторизації...
        </p>
      </div>
    </div>
  );
}
