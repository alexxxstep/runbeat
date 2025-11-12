import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { LoadingSpinner } from '../components/Shared/LoadingSpinner';
import { useAuth } from '../hooks/useAuth';

export function AuthCallbackPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { refreshSpotifyStatus } = useAuth();

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // Check for error parameter first
        const error = searchParams.get('error');
        if (error) {
          console.error('Auth error:', error);
          navigate(`/login?error=${encodeURIComponent(error)}`);
          return;
        }

        // Check if this is Spotify callback (has user_id and spotify_user_id params)
        const userId = searchParams.get('user_id');
        const spotifyUserId = searchParams.get('spotify_user_id');

        if (userId && spotifyUserId) {
          // This is Spotify OAuth callback - success
          // Store user_id in localStorage for future checks
          localStorage.setItem('spotify_user_id', userId);

          // Refresh auth status to update user state
          // This will verify the auth status with backend
          await refreshSpotifyStatus();

          // Small delay to ensure state is updated
          setTimeout(() => {
            // Successfully authenticated with Spotify - redirect to chat
            navigate('/', { replace: true });
          }, 200);
          return;
        }

        // If no params, redirect to login
        navigate('/login?error=no_params', { replace: true });
      } catch (error) {
        console.error('Failed to handle auth callback:', error);
        navigate('/login?error=callback_failed', { replace: true });
      }
    };

    handleAuthCallback();
  }, [navigate, searchParams, refreshSpotifyStatus]);

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
