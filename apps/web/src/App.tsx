import { Routes, Route } from 'react-router-dom';
import { ChatPage } from './pages/ChatPage';
import { PlayerPage } from './pages/PlayerPage';
import { LoginPage } from './pages/LoginPage';
import { HistoryPage } from './pages/HistoryPage';
import { AuthCallbackPage } from './pages/AuthCallbackPage';
import { ProtectedRoute } from './components/ProtectedRoute';

function App() {
  return (
    <div className='min-h-screen bg-gray-50 dark:bg-gray-900'>
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
    </div>
  );
}

export default App;
