/**
 * Backend API client for RunBeat Mobile App
 */
import axios, { AxiosInstance } from 'axios';
import {
  ChatRequest,
  ChatResponse,
  PlaylistGenerateRequest,
  PlaylistGenerateResponse,
  UserPreferences,
  Workout,
} from '../types';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

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
  }

  // Chat endpoints
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.client.post<ChatResponse>(
      '/chat/message',
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

  async getPlaylistHistory(userId: string, limit = 10, offset = 0) {
    const response = await this.client.get('/playlists/history', {
      params: { user_id: userId, limit, offset },
    });
    return response.data;
  }

  // Auth endpoints
  async initiateSpotifyAuth() {
    const response = await this.client.get('/auth/spotify');
    return response.data;
  }

  async checkSpotifyAuthStatus(userId: string) {
    const response = await this.client.get('/auth/spotify/status', {
      params: { user_id: userId },
    });
    return response.data;
  }

  async getSpotifyCallbackUrl(): Promise<string> {
    // This will be handled by the OAuth flow
    // The backend redirects to this URL after authentication
    return `${API_URL}/auth/spotify/callback`;
  }

  // Workout endpoints
  async createWorkout(workout: Workout, userId: string) {
    const response = await this.client.post('/workouts', {
      workout,
      user_id: userId,
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

  async updateUserPreferences(
    userId: string,
    preferences: UserPreferences
  ) {
    const response = await this.client.put(`/users/${userId}/preferences`, {
      preferences,
    });
    return response.data;
  }
}

export const api = new ApiClient();

