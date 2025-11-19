/**
 * Tests for useChat hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useChat } from '../useChat';
import { api } from '../../services/api';
import type { ChatResponse, Workout, PlaylistFromLLM } from '../../types';

// Mock API client
vi.mock('../../services/api', () => ({
  api: {
    sendMessage: vi.fn(),
    generatePlaylist: vi.fn(),
  },
}));

// Mock errorLogger
vi.mock('../../services/errorLogger', () => ({
  errorLogger: {
    logError: vi.fn(),
  },
}));

describe('useChat', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock Date.now() for consistent IDs
    vi.spyOn(Date, 'now').mockReturnValue(1000000);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('sendMessage', () => {
    it('should send message and return result with needs_clarification=true', async () => {
      const mockResponse: ChatResponse = {
        message: 'Яка тривалість тренування?',
        needs_clarification: true,
        is_complete: false,
      };

      vi.mocked(api.sendMessage).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat());

      const sendResult = await result.current.sendMessage('хочу побігати', 'user123');

      expect(sendResult).toEqual({
        workout: null,
        needs_clarification: true,
        is_complete: false,
        _hasPlaylist: false,
      });

      expect(result.current.messages).toHaveLength(2);
      expect(result.current.messages[0].role).toBe('user');
      expect(result.current.messages[0].content).toBe('хочу побігати');
      expect(result.current.messages[1].role).toBe('assistant');
      expect(result.current.messages[1].content).toBe('Яка тривалість тренування?');
      expect(result.current.messages[1]._metadata?.needs_clarification).toBe(true);
      expect(result.current.messages[1]._metadata?.is_complete).toBe(false);
    });

    it('should handle is_complete=true with workout', async () => {
      const mockWorkout: Workout = {
        id: 'workout123',
        type: 'steady',
        duration_minutes: 30,
        intensity: 'moderate',
        hr_zones: [130, 150],
      };

      const mockResponse: ChatResponse = {
        message: '✅ Воркаут успішно створено!',
        workout: mockWorkout,
        needs_clarification: false,
        is_complete: true,
      };

      vi.mocked(api.sendMessage).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat());

      const sendResult = await result.current.sendMessage('так', 'user123');

      expect(sendResult).toEqual({
        workout: mockWorkout,
        needs_clarification: false,
        is_complete: true,
        _hasPlaylist: false,
      });

      expect(result.current.messages[1].workout).toEqual(mockWorkout);
      expect(result.current.messages[1]._metadata?.is_complete).toBe(true);
    });

    it('should handle workout without ID (waiting for confirmation)', async () => {
      const mockWorkout: Workout = {
        type: 'intervals',
        duration_minutes: 45,
        intensity: 'high',
        hr_zones: [160, 180],
      };

      const mockResponse: ChatResponse = {
        message: 'Супер! Створюємо воркаут?',
        workout: mockWorkout,
        needs_clarification: false,
        is_complete: false,
      };

      vi.mocked(api.sendMessage).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat());

      const sendResult = await result.current.sendMessage('інтервальна 45 хвилин', 'user123');

      expect(sendResult).toEqual({
        workout: mockWorkout,
        needs_clarification: false,
        is_complete: false,
        _hasPlaylist: false,
      });

      expect(result.current.messages[1].workout).toEqual(mockWorkout);
      expect(result.current.messages[1]._metadata?.needs_clarification).toBe(false);
      expect(result.current.messages[1]._metadata?.is_complete).toBe(false);
    });

    it('should handle playlist in response', async () => {
      const mockWorkout: Workout = {
        id: 'workout123',
        type: 'steady',
        duration_minutes: 30,
        intensity: 'moderate',
        hr_zones: [130, 150],
      };

      const mockPlaylist: PlaylistFromLLM = {
        playlist_name: 'Running Playlist',
        total_tracks: 10,
        total_duration_minutes: 30,
        bpm_range: [130, 150],
        progression_type: 'steady',
        primary_genres: ['rock', 'pop'],
        tracks: [
          {
            title: 'Song 1',
            artist: 'Artist 1',
            bpm: 140,
            duration_seconds: 180,
            energy_level: 0.8,
            genre: 'rock',
            phase: 'main',
          },
        ],
        spotify_url: 'https://open.spotify.com/playlist/123',
      };

      const mockResponse: ChatResponse = {
        message: 'Плейлист готовий!',
        workout: mockWorkout,
        playlist: mockPlaylist,
        needs_clarification: false,
        is_complete: true,
      };

      vi.mocked(api.sendMessage).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat());

      const sendResult = await result.current.sendMessage('так', 'user123');

      expect(sendResult).toEqual({
        workout: mockWorkout,
        needs_clarification: false,
        is_complete: true,
        _hasPlaylist: true,
      });

      expect(result.current.messages[1].playlist).toBeDefined();
      expect(result.current.messages[1].playlist?.spotify_url).toBe('https://open.spotify.com/playlist/123');
      expect(result.current.messages[1].playlist?.tracks).toHaveLength(1);
      expect(result.current.messages[1].playlist?.tracks[0].name).toBe('Song 1');
    });

    it('should handle error and return error state', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.sendMessage).mockRejectedValue(mockError);

      const { result } = renderHook(() => useChat());

      const sendResult = await result.current.sendMessage('test', 'user123');

      expect(sendResult).toEqual({
        workout: null,
        needs_clarification: false,
        is_complete: false,
      });

      expect(result.current.error).toBe('Network error');
      expect(result.current.messages).toHaveLength(2);
      expect(result.current.messages[1].role).toBe('assistant');
      expect(result.current.messages[1].content).toContain('Помилка');
    });

    it('should update conversation ID when provided', async () => {
      const mockResponse: ChatResponse = {
        message: 'Hello',
        needs_clarification: false,
        is_complete: false,
        conversation_id: 'conv123',
      };

      vi.mocked(api.sendMessage).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat());

      await result.current.sendMessage('hello', 'user123');

      expect(result.current.conversationId).toBe('conv123');
    });

    it('should set loading state correctly', async () => {
      const mockResponse: ChatResponse = {
        message: 'Response',
        needs_clarification: false,
        is_complete: false,
      };

      vi.mocked(api.sendMessage).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockResponse), 100))
      );

      const { result } = renderHook(() => useChat());

      expect(result.current.isLoading).toBe(false);

      const sendPromise = result.current.sendMessage('test', 'user123');

      await waitFor(() => {
        expect(result.current.isLoading).toBe(true);
      });

      await sendPromise;

      expect(result.current.isLoading).toBe(false);
    });

    it('should clear error on new message', async () => {
      // First, set an error
      const mockError = new Error('First error');
      vi.mocked(api.sendMessage).mockRejectedValueOnce(mockError);

      const { result } = renderHook(() => useChat());

      await result.current.sendMessage('test1', 'user123');
      expect(result.current.error).toBe('First error');

      // Then send successful message
      const mockResponse: ChatResponse = {
        message: 'Success',
        needs_clarification: false,
        is_complete: false,
      };
      vi.mocked(api.sendMessage).mockResolvedValue(mockResponse);

      await result.current.sendMessage('test2', 'user123');
      expect(result.current.error).toBeNull();
    });
  });

  describe('generatePlaylist', () => {
    it('should generate playlist successfully', async () => {
      const mockWorkout: Workout = {
        id: 'workout123',
        type: 'steady',
        duration_minutes: 30,
        intensity: 'moderate',
        hr_zones: [130, 150],
      };

      const mockPlaylist = {
        playlist_id: 'playlist123',
        spotify_url: 'https://open.spotify.com/playlist/123',
        playlist_name: 'My Playlist',
        tracks: [],
        total_duration: 1800,
        total_tracks: 10,
      };

      vi.mocked(api.generatePlaylist).mockResolvedValue(mockPlaylist);

      const { result } = renderHook(() => useChat());

      const playlistResult = await result.current.generatePlaylist(mockWorkout, 'user123');

      expect(playlistResult).toEqual(mockPlaylist);
      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0].playlist).toEqual(mockPlaylist);
      expect(result.current.messages[0].content).toContain('успішно створено');
    });

    it('should handle playlist generation error', async () => {
      const mockWorkout: Workout = {
        id: 'workout123',
        type: 'steady',
        duration_minutes: 30,
        intensity: 'moderate',
        hr_zones: [130, 150],
      };

      const mockError = new Error('Generation failed');
      vi.mocked(api.generatePlaylist).mockRejectedValue(mockError);

      const { result } = renderHook(() => useChat());

      const playlistResult = await result.current.generatePlaylist(mockWorkout, 'user123');

      expect(playlistResult).toBeNull();
      expect(result.current.error).toBe('Generation failed');
      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0].content).toContain('Помилка');
    });
  });

  describe('clearMessages', () => {
    it('should clear all messages and reset state', async () => {
      const mockResponse: ChatResponse = {
        message: 'Test',
        needs_clarification: false,
        is_complete: false,
        conversation_id: 'conv123',
      };

      vi.mocked(api.sendMessage).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat());

      await result.current.sendMessage('test', 'user123');
      expect(result.current.messages.length).toBeGreaterThan(0);
      expect(result.current.conversationId).toBe('conv123');

      result.current.clearMessages();

      expect(result.current.messages).toHaveLength(0);
      expect(result.current.conversationId).toBeUndefined();
      expect(result.current.error).toBeNull();
    });
  });

  describe('addWorkoutActivationMessage', () => {
    it('should add workout activation message', () => {
      const mockWorkout: Workout = {
        id: 'workout123',
        type: 'intervals',
        duration_minutes: 45,
        intensity: 'high',
        hr_zones: [160, 180],
      };

      const { result } = renderHook(() => useChat());

      result.current.addWorkoutActivationMessage(mockWorkout);

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0].role).toBe('assistant');
      expect(result.current.messages[0].workout).toEqual(mockWorkout);
      expect(result.current.messages[0].content).toContain('Інтервальна');
      expect(result.current.messages[0].content).toContain('45 хвилин');
      expect(result.current.messages[0].content).toContain('Висока');
    });
  });

  describe('metadata handling', () => {
    it('should include metadata in message when needs_clarification is true', async () => {
      const mockResponse: ChatResponse = {
        message: 'Need more info',
        needs_clarification: true,
        is_complete: false,
      };

      vi.mocked(api.sendMessage).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat());

      await result.current.sendMessage('test', 'user123');

      const aiMessage = result.current.messages[1];
      expect(aiMessage._metadata).toBeDefined();
      expect(aiMessage._metadata?.needs_clarification).toBe(true);
      expect(aiMessage._metadata?.is_complete).toBe(false);
    });

    it('should include metadata when is_complete is true', async () => {
      const mockResponse: ChatResponse = {
        message: 'Complete',
        needs_clarification: false,
        is_complete: true,
      };

      vi.mocked(api.sendMessage).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat());

      await result.current.sendMessage('test', 'user123');

      const aiMessage = result.current.messages[1];
      expect(aiMessage._metadata?.is_complete).toBe(true);
      expect(aiMessage._metadata?.needs_clarification).toBe(false);
    });

    it('should handle undefined is_complete as false', async () => {
      const mockResponse: ChatResponse = {
        message: 'Response',
        needs_clarification: false,
        // is_complete is undefined
      };

      vi.mocked(api.sendMessage).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat());

      const sendResult = await result.current.sendMessage('test', 'user123');

      expect(sendResult.is_complete).toBe(false);
    });
  });
});

