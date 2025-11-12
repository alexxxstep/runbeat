import { useState, useCallback } from 'react';
import { api } from '../services/api';
import type { Message, Workout, ChatRequest } from '../types';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (text: string, userId?: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const request: ChatRequest = {
        message: text,
        user_id: userId,
      };
      const response = await api.sendMessage(request);

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
        workout: response.workout,
      };
      setMessages((prev) => [...prev, aiMessage]);

      if (response.workout && !response.needs_clarification) {
        return response.workout;
      }

      return null;
    } catch (err) {
      // Better error handling
      let errorMessage = 'Не вдалося відправити повідомлення';

      if (err instanceof Error) {
        errorMessage = err.message;
        console.error('Chat error:', err);
      } else {
        console.error('Unknown chat error:', err);
      }

      setError(errorMessage);

      const errorMsg: Message = {
        id: (Date.now() + 2).toString(),
        role: 'assistant',
        content: `Помилка: ${errorMessage}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const generatePlaylist = useCallback(
    async (workout: Workout, userId?: string) => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await api.generatePlaylist({
          workout,
          user_preferences: {},
          user_id: userId,
        });

        // Add playlist message to chat
        if (response) {
          const playlistMessage: Message = {
            id: Date.now().toString(),
            role: 'assistant',
            content: response.spotify_url
              ? '✅ Плейлист успішно створено в Spotify!'
              : '✅ Плейлист успішно згенеровано!',
            timestamp: new Date(),
            playlist: response,
          };
          setMessages((prev) => [...prev, playlistMessage]);
        }

        return response;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to generate playlist';
        setError(errorMessage);

        // Add error message to chat
        const errorMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `❌ Помилка: ${errorMessage}`,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMsg]);

        return null;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  return {
    messages,
    sendMessage,
    generatePlaylist,
    isLoading,
    error,
  };
}
