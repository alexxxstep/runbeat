import { useState, useCallback } from 'react';
import { api } from '../services/api';
import type { Message, Workout, ChatRequest, Track } from '../types';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | undefined>();

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
        conversation_id: conversationId,
      };
      const response = await api.sendMessage(request);

      // Update conversation ID if provided
      if (response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
        workout: response.workout,
        // Convert LLM playlist to frontend Playlist format if available
        playlist: response.playlist
          ? {
              playlist_id: response.playlist.spotify_playlist_id || undefined,
              spotify_url: response.playlist.spotify_url || undefined,
              tracks: response.playlist.tracks.map((track) => ({
                id: `${track.title}-${track.artist}`, // Temporary ID
                name: track.title,
                artist: track.artist,
                artist_id: '', // Not available from LLM
                album: undefined,
                duration_ms: track.duration_seconds * 1000,
                spotify_url: '',
                spotify_uri: '',
                preview_url: undefined,
                external_urls: {},
                tempo: track.bpm,
                bpm: track.bpm,
                energy: track.energy_level,
                danceability: 0.5, // Default
                valence: 0.5, // Default
                genres: [track.genre],
                phase: track.phase, // Preserve phase info for display
              })),
              total_duration: response.playlist.total_duration_minutes * 60, // Convert to seconds
              total_tracks: response.playlist.total_tracks,
              generation_time_seconds: undefined,
            }
          : undefined,
      };
      setMessages((prev) => [...prev, aiMessage]);

      // Return workout and playlist info if available
      // If playlist is available, it means workout is complete and playlist is generated
      if (response.playlist) {
        // Playlist is already in the message, return workout for compatibility
        // Also return a special marker to indicate playlist is available
        return (response.workout ? { ...response.workout, _hasPlaylist: true } : null) as (Workout & { _hasPlaylist?: boolean }) | null;
      }

      if (response.workout && response.is_complete && !response.needs_clarification) {
        return response.workout;
      }

      // If needs clarification, return null but conversation continues
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
  }, [conversationId]);

  const generatePlaylist = useCallback(
    async (
      workout: Workout,
      userId?: string,
      genres?: string[],
      intervalStages?: Array<{
        id: string;
        name: string;
        durationMinutes: number;
        hrZone: [number, number];
        bpmRange: [number, number];
      }>,
      prompt?: string | null,
      workoutId?: string | null,
      selectedTracks?: Track[] // Tracks from selected variant
    ) => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await api.generatePlaylist({
          workout,
          user_preferences: {
            top_genres: genres || [],
            top_artists: [],
            avg_bpm: 145,
          },
          user_id: userId,
          workout_id: workoutId || undefined,
          interval_stages: intervalStages?.map((stage) => ({
            name: stage.name,
            duration_minutes: stage.durationMinutes,
            hr_zone: stage.hrZone,
            bpm_range: stage.bpmRange,
          })),
          prompt: prompt || null,
          selected_tracks: selectedTracks?.map((track) => ({
            id: track.id,
            name: track.name,
            artist: track.artist,
            artist_id: track.artist_id,
            duration_ms: track.duration_ms,
            spotify_uri: track.spotify_uri,
            spotify_url: track.spotify_url,
            preview_url: track.preview_url,
            external_urls: track.external_urls || { spotify: track.spotify_url },
            album: track.album,
            tempo: track.tempo || track.bpm || 120.0,
            bpm: track.bpm || track.tempo || 120.0,
            energy: track.energy || 0.5,
            danceability: track.danceability || 0.5,
            valence: track.valence || 0.5,
            genres: track.genres || [],
          })),
        });

        // Add playlist message to chat
        if (response) {
          const playlistMessage: Message = {
            id: Date.now().toString(),
            role: 'assistant',
            content: response.spotify_url
              ? response.playlist_name
                ? `✅ Плейлист "${response.playlist_name}" успішно створено в Spotify!`
                : '✅ Плейлист успішно створено в Spotify!'
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

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
    setConversationId(undefined);
  }, []);

  const addWorkoutActivationMessage = useCallback((workout: Workout) => {
    const workoutTypeLabels: Record<string, string> = {
      steady: 'Стабільна',
      progressive: 'Прогресивна',
      intervals: 'Інтервальна',
      fartlek: 'Фартлек',
    };

    const intensityLabels: Record<string, string> = {
      low: 'Легка',
      moderate: 'Середня',
      high: 'Висока',
    };

    const workoutInfo = `**Активований воркаут:**

**Тип тренування:** ${workoutTypeLabels[workout.type] || workout.type}
**Тривалість:** ${workout.duration_minutes} хвилин
**Інтенсивність:** ${intensityLabels[workout.intensity] || workout.intensity}
**Частота серцебиття:** ${workout.hr_zones[0]} - ${workout.hr_zones[1]} уд/хв

Сформувати під цей воркаут плейлист? Да чи Ні`;

    const aiMessage: Message = {
      id: Date.now().toString(),
      role: 'assistant',
      content: workoutInfo,
      timestamp: new Date(),
      workout: workout,
    };
    setMessages((prev) => [...prev, aiMessage]);
  }, []);

  return {
    messages,
    setMessages,
    sendMessage,
    generatePlaylist,
    clearMessages,
    addWorkoutActivationMessage,
    isLoading,
    error,
    conversationId,
  };
}
