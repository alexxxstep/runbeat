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
      timeout: 150000, // 150 seconds (2.5 minutes) for playlist generation
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
        if (import.meta.env.DEV) {
          console.log('API Response:', response.status, response.config.url);
        }
        return response;
      },
      async (error) => {
        // Better error handling
        let errorMessage = 'Невідома помилка';
        let statusCode: number | undefined;

        if (error.code === 'ECONNABORTED') {
          errorMessage = 'Час очікування вичерпано. Спробуйте ще раз.';
          console.error('API Request timeout');
        } else if (error.response) {
          // Server responded with error status
          statusCode = error.response.status;
          errorMessage =
            error.response.data?.detail ||
            error.response.data?.message ||
            `Помилка сервера: ${statusCode}`;
          console.error('API Error Response:', statusCode, errorMessage);
        } else if (error.request) {
          // Request was made but no response received
          errorMessage =
            'Не вдалося підключитися до сервера. Перевірте, чи працює backend API.';
          console.error('API No Response:', error.request);
          console.error('API URL was:', API_URL);
        } else {
          // Something else happened
          errorMessage = error.message || 'Невідома помилка';
          console.error('API Error:', errorMessage);
        }

        // Log error to backend (fire and forget)
        try {
          const { errorLogger } = await import('./errorLogger');
          errorLogger.logError(new Error(errorMessage), {
            request_path: error.config?.url,
            request_method: error.config?.method?.toUpperCase(),
            request_body: error.config?.data,
            response_status: statusCode,
            error_details: {
              code: error.code,
              isAxiosError: error.isAxiosError,
            },
          });
        } catch (logError) {
          // Don't fail if error logging fails
          console.debug('Failed to log error to backend:', logError);
        }

        return Promise.reject(new Error(errorMessage));
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
