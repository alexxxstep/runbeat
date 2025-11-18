import { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';

export function Navbar() {
  const { signOut } = useAuth();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    if (isLoggingOut) return;

    setIsLoggingOut(true);
    try {
      await signOut();
    } catch (error) {
      console.error('Logout error:', error);
      setIsLoggingOut(false);
    }
  };

  return (
    <nav className='bg-app-surface border-b border-app-border'>
      <div className='container mx-auto px-4 py-3 flex justify-between items-center'>
        <div className='flex items-center gap-2'>
          <h1 className='text-title-3 font-display font-bold text-app-text'>
            RunBeat
          </h1>
        </div>
        <button
          onClick={handleLogout}
          disabled={isLoggingOut}
          className='px-4 py-2 text-subhead text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 border border-red-300 dark:border-red-700 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
          title='Вийти з облікового запису'
        >
          {isLoggingOut ? 'Вихід...' : 'Вийти'}
        </button>
      </div>
    </nav>
  );
}

