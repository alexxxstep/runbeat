/**
 * Chat hook for RunBeat Mobile App
 */
import { useState, useCallback } from 'react';
import { api } from '../services/api';
import { Message, ChatRequest, PlaylistGenerateRequest } from '../types';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (text: string, userId?: string) => {
      // Add user message
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
        // Send message to backend
        const request: ChatRequest = {
          message: text,
          user_id: userId,
        };
        const response = await api.sendMessage(request);

        // Add AI response
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.message,
          timestamp: new Date(),
          workout: response.workout,
        };
        setMessages((prev) => [...prev, aiMessage]);

        // If workout is ready and no clarification needed, generate playlist
        if (response.workout && !response.needs_clarification) {
          return response.workout;
        }

        return null;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to send message';
        setError(errorMessage);

        // Add error message to chat
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
    async (workout: PlaylistGenerateRequest['workout'], userPreferences?: PlaylistGenerateRequest['user_preferences']) => {
      setIsLoading(true);
      setError(null);

      try {
        const request: PlaylistGenerateRequest = {
          workout,
          user_preferences: userPreferences,
        };
        const response = await api.generatePlaylist(request);
        return response;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to generate playlist';
        setError(errorMessage);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    generatePlaylist,
    clearMessages,
  };
}

