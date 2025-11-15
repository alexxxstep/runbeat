import { create } from 'zustand';

export interface User {
  id: string;
  email?: string;
  spotify_user_id?: string;
}

interface AuthState {
  user: User | null;
  spotifyAuthenticated: boolean;
  loading: boolean;
  setUser: (user: User | null) => void;
  setSpotifyAuthenticated: (isAuthenticated: boolean) => void;
  setLoading: (isLoading: boolean) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  spotifyAuthenticated: false,
  loading: true,
  setUser: (user) => set({ user }),
  setSpotifyAuthenticated: (isAuthenticated) => set({ spotifyAuthenticated: isAuthenticated }),
  setLoading: (isLoading) => set({ loading: isLoading }),
}));
