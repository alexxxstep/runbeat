import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../services/supabase';
import { LoadingSpinner } from '../components/Shared/LoadingSpinner';

export function AuthCallbackPage() {
  const navigate = useNavigate();

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // Supabase automatically handles the OAuth callback
        // We just need to wait for the session to be established
        const { data, error } = await supabase.auth.getSession();

        if (error) {
          console.error('Auth callback error:', error);
          navigate('/login?error=auth_failed');
          return;
        }

        if (data.session) {
          // Successfully authenticated
          navigate('/');
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
  }, [navigate]);

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
