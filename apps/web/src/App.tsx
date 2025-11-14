import { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from './components/ProtectedRoute';

// --- OPTIMIZATION: Lazy Loading Pages ---
const ChatPage = lazy(() => import('./pages/ChatPage').then(module => ({ default: module.ChatPage })));
const PlayerPage = lazy(() => import('./pages/PlayerPage').then(module => ({ default: module.PlayerPage })));
const LoginPage = lazy(() => import('./pages/LoginPage').then(module => ({ default: module.LoginPage })));
const HistoryPage = lazy(() => import('./pages/HistoryPage').then(module => ({ default: module.HistoryPage })));
const AuthCallbackPage = lazy(() => import('./pages/AuthCallbackPage').then(module => ({ default: module.AuthCallbackPage })));

const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
    <div className="text-gray-500 dark:text-gray-400">Loading...</div>
  </div>
);
// --- END OPTIMIZATION ---

function App() {
  return (
    <div className='min-h-screen bg-gray-50 dark:bg-gray-900'>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route
            path='/'
            element={
              <ProtectedRoute requireSpotify={true}>
                <ChatPage />
              </ProtectedRoute>
            }
          />
          <Route path='/login' element={<LoginPage />} />
          <Route path='/auth/callback' element={<AuthCallbackPage />} />
          <Route
            path='/player/:playlistId?'
            element={
              <ProtectedRoute requireSpotify={true}>
                <PlayerPage />
              </ProtectedRoute>
            }
          />
          <Route
            path='/history'
            element={
              <ProtectedRoute requireSpotify={true}>
                <HistoryPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </Suspense>
    </div>
  );
}

export default App;
