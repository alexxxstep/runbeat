/**
 * TypeScript types for RunBeat Web App
 */

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  workout?: Workout;
}

export interface Workout {
  type: 'steady' | 'progressive' | 'intervals' | 'fartlek';
  duration_minutes: number;
  intensity: 'low' | 'moderate' | 'high';
  hr_zones: number[];
  confidence?: number;
  needs_clarification?: boolean;
  clarification_question?: string;
}

export interface Track {
  id: string;
  name: string;
  artist: string;
  artist_id: string;
  album?: string;
  duration_ms: number;
  spotify_url: string;
  spotify_uri: string;
  preview_url?: string;
  tempo: number;
  bpm: number;
  energy: number;
  danceability: number;
  valence: number;
  genres: string[];
}

export interface Playlist {
  playlist_id?: string;
  spotify_url?: string;
  tracks: Track[];
  total_duration: number;
  total_tracks: number;
  generation_time_seconds?: number;
}

export interface ChatRequest {
  message: string;
  user_id?: string;
}

export interface ChatResponse {
  message: string;
  workout?: Workout;
  needs_clarification: boolean;
}

export interface PlaylistGenerateRequest {
  workout: Workout;
  user_preferences?: {
    top_genres?: string[];
    top_artists?: string[];
    avg_bpm?: number;
  };
}

export interface PlaylistGenerateResponse {
  playlist_id?: string;
  spotify_url?: string;
  tracks: Track[];
  total_duration: number;
  total_tracks: number;
  generation_time_seconds?: number;
}

export interface UserPreferences {
  top_genres: string[];
  top_artists: string[];
  avg_bpm: number;
}

