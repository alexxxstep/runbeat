import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { supabase } from '../services/supabase';
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
          // Supabase session should already be established
          const { data, error } = await supabase.auth.getSession();

          if (error || !data.session) {
            console.error('Auth callback error:', error);
            navigate('/login?error=auth_failed');
            return;
          }

          // Successfully authenticated with Spotify
          navigate('/');
          return;
        }

        // This is Google OAuth callback
        // Supabase automatically handles the OAuth callback
        const { data, error } = await supabase.auth.getSession();

        if (error) {
          console.error('Auth callback error:', error);
          navigate('/login?error=auth_failed');
          return;
        }

        if (data.session) {
          // Successfully authenticated with Google
          // Redirect to login to connect Spotify
          navigate('/login');
        } else {
          // No session found
          navigate('/login?error=no_session');
        }
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
