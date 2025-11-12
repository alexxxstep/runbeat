import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useChat } from '../hooks/useChat';
import { MessageBubble } from '../components/Chat/MessageBubble';
import { InputBar } from '../components/Chat/InputBar';
import { TypingIndicator } from '../components/Chat/TypingIndicator';

export function ChatPage() {
  const navigate = useNavigate();
  const { messages, sendMessage, generatePlaylist, isLoading } = useChat();

  const handleSend = async (text: string) => {
    const workout = await sendMessage(text);

    // If workout is ready, generate playlist
    if (workout && !workout.needs_clarification) {
      try {
        const playlist = await generatePlaylist(workout);
        if (playlist?.playlist_id) {
          navigate(`/player/${playlist.playlist_id}`);
        }
      } catch (error) {
        console.error('Failed to generate playlist:', error);
      }
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg">Привіт! Я RunBeat AI</p>
            <p className="text-sm mt-2">
              Опиши своє тренування, і я створю для тебе плейлист
            </p>
          </div>
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

