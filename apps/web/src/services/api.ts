/**
 * Backend API client for RunBeat Web App
 */
import axios, { AxiosInstance } from 'axios';
import type {
  ChatRequest,
  ChatResponse,
  PlaylistGenerateRequest,
  PlaylistGenerateResponse,
  PlaylistVariantsResponse,
  UserPreferences,
  Workout,
} from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Log API URL for debugging (only in development)
if (import.meta.env.DEV) {
  console.log('API URL:', API_URL);
}

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        if (import.meta.env.DEV) {
          console.log('API Request:', config.method?.toUpperCase(), config.url);
        }
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        return response;
      },
      (error) => {
        // Better error handling
        if (error.code === 'ECONNABORTED') {
          console.error('API Request timeout');
          return Promise.reject(
            new Error('Час очікування вичерпано. Спробуйте ще раз.')
          );
        }

        if (error.response) {
          // Server responded with error status
          const status = error.response.status;
          const message =
            error.response.data?.detail ||
            error.response.data?.message ||
            `Помилка сервера: ${status}`;
          console.error('API Error Response:', status, message);
          return Promise.reject(new Error(message));
        } else if (error.request) {
          // Request was made but no response received
          console.error('API No Response:', error.request);
          console.error('API URL was:', API_URL);
          return Promise.reject(
            new Error(
              'Не вдалося підключитися до сервера. Перевірте, чи працює backend API.'
            )
          );
        } else {
          // Something else happened
          console.error('API Error:', error.message);
          return Promise.reject(new Error(error.message || 'Невідома помилка'));
        }
      }
    );
  }

  // Chat endpoints
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.client.post<ChatResponse>(
      '/api/v1/chat/message',
      request
    );
    return response.data;
  }

  // Playlist endpoints
  async generatePlaylist(
    request: PlaylistGenerateRequest
  ): Promise<PlaylistGenerateResponse> {
    const response = await this.client.post<PlaylistGenerateResponse>(
      '/playlists/generate',
      request
    );
    return response.data;
  }

  async previewPlaylistVariants(
    request: PlaylistGenerateRequest
  ): Promise<PlaylistVariantsResponse> {
    const response = await this.client.post<PlaylistVariantsResponse>(
      '/playlists/preview-variants',
      request
    );
    return response.data;
  }

  async getPlaylistHistory(userId: string, limit = 10, offset = 0) {
    const response = await this.client.get('/playlists/history', {
      params: { user_id: userId, limit, offset },
    });
    return response.data;
  }

  async deletePlaylist(playlistId: string, userId: string) {
    const response = await this.client.delete(`/playlists/${playlistId}`, {
      params: { user_id: userId },
    });
    return response.data;
  }

  // Auth endpoints
  async initiateSpotifyAuth(userId?: string) {
    const params = userId ? { user_id: userId } : {};
    const response = await this.client.get('/auth/spotify', { params });
    return response.data;
  }

  async checkSpotifyAuthStatus(userId: string) {
    const response = await this.client.get('/auth/spotify/status', {
      params: { user_id: userId },
    });
    return response.data;
  }

  // Workout endpoints
  async createWorkout(
    workout: Workout,
    userId: string,
    genres?: string[],
    intervalStages?: Array<{
      name: string;
      duration_minutes: number;
      hr_zone: [number, number];
      bpm_range: [number, number];
    }>,
    prompt?: string
  ) {
    const response = await this.client.post('/workouts', {
      workout,
      user_id: userId,
      genres: genres || [],
      interval_stages: intervalStages || null,
      prompt: prompt || null,
    });
    return response.data;
  }

  async getWorkouts(userId: string, limit = 10, offset = 0) {
    const response = await this.client.get('/workouts', {
      params: { user_id: userId, limit, offset },
    });
    return response.data;
  }

  async getWorkout(workoutId: string, userId: string) {
    const response = await this.client.get(`/workouts/${workoutId}`, {
      params: { user_id: userId },
    });
    return response.data;
  }

  async deleteWorkout(workoutId: string, userId: string) {
    const response = await this.client.delete(`/workouts/${workoutId}`, {
      params: { user_id: userId },
    });
    return response.status === 204;
  }

  async completeWorkout(workoutId: string, userId: string) {
    const response = await this.client.patch(
      `/workouts/${workoutId}/complete`,
      null,
      {
        params: { user_id: userId },
      }
    );
    return response.data;
  }

  // User endpoints
  async getUserPreferences(userId: string) {
    const response = await this.client.get(`/users/${userId}/preferences`);
    return response.data;
  }

  async updateUserPreferences(userId: string, preferences: UserPreferences) {
    const response = await this.client.put(`/users/${userId}/preferences`, {
      preferences,
    });
    return response.data;
  }
}

export const api = new ApiClient();
