import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/Shared/Button';

export function LoginPage() {
  const navigate = useNavigate();
  const { user, signInWithSpotify, loading } = useAuth();

  useEffect(() => {
    if (user) {
      navigate('/');
    }
  }, [user, navigate]);

  const handleSpotifyLogin = async () => {
    try {
      await signInWithSpotify();
    } catch (error) {
      console.error('Failed to sign in with Spotify:', error);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 max-w-md w-full">
        <h1 className="text-3xl font-bold text-center mb-6">RunBeat</h1>
        <p className="text-gray-600 dark:text-gray-400 text-center mb-8">
          Увійдіть через Spotify, щоб почати створювати плейлисти для тренувань
        </p>
        <Button
          onClick={handleSpotifyLogin}
          disabled={loading}
          className="w-full"
        >
          {loading ? 'Завантаження...' : 'Увійти через Spotify'}
        </Button>
      </div>
    </div>
  );
}

