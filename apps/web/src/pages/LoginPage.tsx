import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/Shared/Button';

export function LoginPage() {
  const navigate = useNavigate();
  const { user, signInWithGoogle, signInWithSpotify, loading } = useAuth();

  useEffect(() => {
    if (user) {
      navigate('/');
    }
  }, [user, navigate]);

  const handleGoogleLogin = async () => {
    try {
      await signInWithGoogle();
    } catch (error) {
      console.error('Failed to sign in with Google:', error);
    }
  };

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
          Увійдіть, щоб почати створювати плейлисти для тренувань
        </p>

        <div className='space-y-4'>
          <Button
            onClick={handleGoogleLogin}
            disabled={loading}
            className='w-full bg-white dark:bg-gray-700 text-gray-900 dark:text-white border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 flex items-center justify-center gap-2'
          >
            <svg className='w-5 h-5' viewBox='0 0 24 24'>
              <path
                fill='currentColor'
                d='M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z'
              />
              <path
                fill='currentColor'
                d='M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z'
              />
              <path
                fill='currentColor'
                d='M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z'
              />
              <path
                fill='currentColor'
                d='M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z'
              />
            </svg>
            {loading ? 'Завантаження...' : 'Увійти через Google'}
          </Button>

          <div className='relative'>
            <div className='absolute inset-0 flex items-center'>
              <div className='w-full border-t border-gray-300 dark:border-gray-600'></div>
            </div>
            <div className='relative flex justify-center text-sm'>
              <span className='px-2 bg-white dark:bg-gray-800 text-gray-500'>
                або
              </span>
            </div>
          </div>

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

        <p className='text-xs text-gray-500 dark:text-gray-400 text-center mt-6'>
          Після входу через Google ви зможете підключити Spotify для створення
          плейлистів
        </p>
      </div>
    </div>
  );
}
