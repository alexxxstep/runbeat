import { useNavigate } from 'react-router-dom';
import { useChat } from '../hooks/useChat';
import { useAuth } from '../hooks/useAuth';
import { MessageBubble } from '../components/Chat/MessageBubble';
import { InputBar } from '../components/Chat/InputBar';
import { TypingIndicator } from '../components/Chat/TypingIndicator';
import { ErrorDisplay } from '../components/Shared/ErrorDisplay';
import type { Message } from '../types';

export function ChatPage() {
  const navigate = useNavigate();
  const { user, spotifyAuthenticated } = useAuth();
  const { messages, sendMessage, generatePlaylist, isLoading, error } =
    useChat();

  const handleSend = async (text: string) => {
    const workout = await sendMessage(text);

    // If workout is ready, generate playlist
    if (workout && !workout.needs_clarification) {
      try {
        const playlist = await generatePlaylist(workout, user?.id);
        if (playlist?.spotify_url) {
          // Open Spotify playlist URL in new tab
          window.open(playlist.spotify_url, '_blank');
        } else if (playlist?.playlist_id) {
          navigate(`/player/${playlist.playlist_id}`);
        }
      } catch (error) {
        console.error('Failed to generate playlist:', error);
      }
    }
  };

  // This should not be reached if ProtectedRoute is working correctly,
  // but add a safety check just in case
  if (!user || !spotifyAuthenticated) {
    return null;
  }

  return (
    <div className='flex flex-col h-screen bg-gray-50 dark:bg-gray-900'>
      <div className='flex-1 overflow-y-auto p-4 space-y-4'>
        {messages.length === 0 && (
          <div className='text-center text-gray-500 mt-8'>
            <p className='text-lg'>Привіт! Я RunBeat AI</p>
            <p className='text-sm mt-2'>
              Опиши своє тренування, і я створю для тебе плейлист
            </p>
            {import.meta.env.DEV && (
              <p className='text-xs mt-4 text-gray-400'>
                API URL:{' '}
                {import.meta.env.VITE_API_URL || 'http://localhost:8000'}
              </p>
            )}
          </div>
        )}
        {error && (
          <ErrorDisplay
            error={error}
            onDismiss={() => {
              // Error will be cleared on next message
            }}
          />
        )}
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isLoading && <TypingIndicator />}
      </div>
      <InputBar onSend={handleSend} disabled={isLoading} />
    </div>
  );
}
