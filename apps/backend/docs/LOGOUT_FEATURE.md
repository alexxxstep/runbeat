# Logout Feature Documentation

## Overview

The logout feature allows users to securely sign out from the RunBeat application. When a user logs out:

1. **Backend**: Spotify access and refresh tokens are revoked from the database
2. **Frontend**: All local storage and session storage data is cleared
3. **User is redirected** to the login page

This ensures that when the user logs in again through Spotify, they will receive a fresh authentication token.

## Backend Implementation

### Endpoint: `POST /auth/logout`

**Parameters:**
- `user_id` (query parameter, required): The ID of the user to logout

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully",
  "user_id": "user-id-here"
}
```

**Error Responses:**
- `404`: User not found
- `422`: Missing or invalid user_id parameter
- `500`: Internal server error

### Database Changes

When a user logs out, the following fields in the `users` table are set to `NULL`:
- `spotify_access_token`
- `spotify_refresh_token`
- `spotify_token_expires_at`

The `updated_at` field is also updated to the current timestamp.

**Note**: The `spotify_user_id` is NOT cleared, so we can still identify the user if they log in again.

## Frontend Implementation

### useAuth Hook

The `signOut` function in `useAuth` hook:

1. Retrieves the current user ID
2. Calls the backend `/auth/logout` endpoint
3. Clears all localStorage data using `localStorage.clear()`
4. Clears all sessionStorage data using `sessionStorage.clear()`
5. Resets the authentication state (user and spotifyAuthenticated)
6. Navigates to `/login` page

### Navbar Component

The Navbar component displays a "Вийти" (Logout) button that:
- Shows loading state ("Вихід...") while logging out
- Is disabled during the logout process
- Handles errors gracefully

## Security Considerations

1. **Token Revocation**: Tokens are cleared from the database, preventing reuse
2. **Complete Cleanup**: Both localStorage and sessionStorage are cleared
3. **Graceful Degradation**: If backend logout fails, frontend still clears local data
4. **Fresh Authentication**: Next login will generate new tokens from Spotify

## Testing

Run the logout tests:

```bash
cd apps/backend
pytest tests/test_logout.py -v
```

Tests cover:
- Successful logout
- Logout with non-existent user
- Token clearing verification
- Missing user_id parameter

## User Flow

1. User clicks "Вийти" button in Navbar
2. Frontend shows loading state
3. Backend revokes Spotify tokens
4. Frontend clears all local storage
5. User is redirected to login page
6. User can log in again with Spotify to get fresh tokens

## Future Enhancements

Potential improvements:
- Add logout from all devices functionality
- Implement session management with refresh token rotation
- Add logout event logging for security audit
- Implement "Remember me" option that preserves some preferences

