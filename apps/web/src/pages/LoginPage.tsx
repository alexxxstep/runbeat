import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/Shared/Button';

export function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, signInWithSpotify, loading, spotifyAuthenticated } = useAuth();
  const error = searchParams.get('error');

  useEffect(() => {
    // If user is authenticated with Spotify, redirect to home
    if (user && spotifyAuthenticated) {
      navigate('/');
    }
  }, [user, spotifyAuthenticated, navigate]);

  const handleSpotifyLogin = async () => {
    try {
      await signInWithSpotify();
    } catch (error) {
      console.error('Failed to sign in with Spotify:', error);
    }
  };

  return (
    <div className='flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900'>
      <div className='bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 max-w-md w-full'>
        <h1 className='text-3xl font-bold text-center mb-6'>RunBeat</h1>
        <p className='text-gray-600 dark:text-gray-400 text-center mb-8'>
          Увійдіть через Spotify, щоб почати створювати плейлисти для тренувань
        </p>

        {error && (
          <div className='mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg'>
            <p className='text-red-800 dark:text-red-200 text-sm font-medium'>
              Помилка авторизації
            </p>
            <p className='text-red-600 dark:text-red-300 text-xs mt-1'>
              {error === 'no_params'
                ? 'Відсутні параметри авторизації'
                : error === 'callback_failed'
                ? 'Не вдалося обробити авторизацію'
                : decodeURIComponent(error)}
            </p>
          </div>
        )}

        <div className='space-y-4'>
          <Button
            onClick={handleSpotifyLogin}
            disabled={loading}
            className='w-full bg-[#1DB954] hover:bg-[#1ed760] text-white flex items-center justify-center gap-2'
          >
            <svg className='w-5 h-5' fill='currentColor' viewBox='0 0 24 24'>
              <path d='M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.84-.179-.84-.66 0-.359.24-.66.54-.779 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.24 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.239-1.26 11.28-1.02 15.239 1.621.539.3.719 1.02.42 1.56-.299.421-1.02.599-1.559.3z' />
            </svg>
            {loading ? 'Завантаження...' : 'Увійти через Spotify'}
          </Button>
        </div>
      </div>
    </div>
  );
}
