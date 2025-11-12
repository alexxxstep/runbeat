/**
 * Spotify authentication service for RunBeat Mobile App
 */
import * as WebBrowser from 'expo-web-browser';
import * as Linking from 'expo-linking';
import { api } from './api';

WebBrowser.maybeCompleteAuthSession();

export interface SpotifyAuthResult {
  success: boolean;
  userId?: string;
  spotifyUserId?: string;
  error?: string;
}

export class SpotifyAuthService {
  /**
   * Initiate Spotify OAuth flow
   */
  async authenticate(): Promise<SpotifyAuthResult> {
    try {
      // Get auth URL from backend
      const { auth_url } = await api.initiateSpotifyAuth();

      // Open browser for authentication
      const result = await WebBrowser.openAuthSessionAsync(
        auth_url,
        Linking.createURL('/auth/success')
      );

      if (result.type === 'success' && result.url) {
        // Parse callback URL
        const url = new URL(result.url);
        const userId = url.searchParams.get('user_id');
        const spotifyUserId = url.searchParams.get('spotify_user_id');

        if (userId && spotifyUserId) {
          return {
            success: true,
            userId,
            spotifyUserId,
          };
        }
      }

      return {
        success: false,
        error: 'Authentication cancelled or failed',
      };
    } catch (error) {
      console.error('Spotify auth error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Check if user is authenticated with Spotify
   */
  async checkAuthStatus(userId: string): Promise<boolean> {
    try {
      const status = await api.checkSpotifyAuthStatus(userId);
      return status.authenticated === true;
    } catch (error) {
      console.error('Check auth status error:', error);
      return false;
    }
  }
}

export const spotifyAuth = new SpotifyAuthService();

