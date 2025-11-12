import { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { LoadingSpinner } from './Shared/LoadingSpinner';

interface ProtectedRouteProps {
  children: ReactNode;
  requireSpotify?: boolean;
}

export function ProtectedRoute({
  children,
  requireSpotify = false,
}: ProtectedRouteProps) {
  const { user, loading, spotifyAuthenticated } = useAuth();

  // Show loading spinner while checking auth
  if (loading) {
    return (
      <div className='flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900'>
        <div className='text-center'>
          <LoadingSpinner />
          <p className='mt-4 text-gray-600 dark:text-gray-400'>
            Перевірка авторизації...
          </p>
        </div>
      </div>
    );
  }

  // If no user, redirect to login
  if (!user) {
    return <Navigate to='/login' replace />;
  }

  // If Spotify is required but not authenticated, redirect to login
  if (requireSpotify && !spotifyAuthenticated) {
    return <Navigate to='/login?spotify_required=true' replace />;
  }

  // User is authenticated (and Spotify if required)
  return <>{children}</>;
}
