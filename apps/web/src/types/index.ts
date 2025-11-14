/**
 * TypeScript types for RunBeat Web App
 */

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  workout?: Workout;
  playlist?: Playlist;
}

export interface Workout {
  id?: string; // Workout ID from database (if saved)
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
  external_urls?: {
    spotify?: string;
    [key: string]: any;
  };
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
  conversation_id?: string;
}

export interface ChatResponse {
  message: string;
  workout?: Workout;
  playlist?: PlaylistFromLLM;
  needs_clarification: boolean;
  conversation_id?: string;
  is_complete?: boolean;
}

// Playlist response from LLM (conversation flow)
export interface PlaylistFromLLM {
  playlist_name: string;
  total_tracks: number;
  total_duration_minutes: number;
  bpm_range: [number, number];
  progression_type: 'steady' | 'building' | 'wave' | 'pyramid';
  primary_genres: string[];
  tracks: PlaylistTrackFromLLM[];
  curation_notes?: string;
  spotify_playlist_id?: string;
  spotify_url?: string;
}

export interface PlaylistTrackFromLLM {
  title: string;
  artist: string;
  bpm: number;
  duration_seconds: number;
  energy_level: number;
  genre: string;
  phase: 'warm-up' | 'main' | 'cool-down';
}

export interface PlaylistGenerateRequest {
  workout: Workout;
  user_preferences?: {
    top_genres?: string[];
    top_artists?: string[];
    avg_bpm?: number;
  };
  user_id?: string;
  workout_id?: string;
  interval_stages?: Array<{
    name: string;
    duration_minutes: number;
    hr_zone: [number, number];
    bpm_range: [number, number];
  }>;
  prompt?: string | null;
  excluded_track_ids?: string[];
  selected_tracks?: Track[]; // Tracks from selected variant to use directly
}

export interface PlaylistGenerateResponse {
  playlist_id?: string;
  spotify_url?: string;
  playlist_name?: string;
  tracks: Track[];
  total_duration: number;
  total_tracks: number;
  generation_time_seconds?: number;
}

export interface TrackVariant {
  tracks: Track[];
  total_duration: number;
  total_tracks: number;
}

export interface PlaylistVariantsResponse {
  variant1: TrackVariant;
  variant2: TrackVariant;
  generation_time_seconds: number;
}

export interface UserPreferences {
  top_genres: string[];
  top_artists: string[];
  avg_bpm: number;
}
