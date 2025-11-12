import { useState, useCallback } from 'react';
import { api } from '../services/api';
import type { Message, Workout, ChatRequest } from '../types';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (text: string, userId?: string) => {
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
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to send message';
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
    },
    []
  );

  const generatePlaylist = useCallback(
    async (workout: Workout, _userId?: string) => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await api.generatePlaylist({
          workout,
          user_preferences: {},
        });
        return response;
      } catch (err) {
        const errorMessage =
          err instanceof Error
            ? err.message
            : 'Failed to generate playlist';
        setError(errorMessage);
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

