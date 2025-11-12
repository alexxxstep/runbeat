# RunBeat Deployment Guide

Покрокова інструкція з деплою всіх компонентів RunBeat.

---

## 📋 Table of Contents

1. [Backend Deployment (Railway)](#backend-deployment-railway)
2. [Web App Deployment (Railway)](#web-app-deployment-railway)
3. [Mobile App Deployment (Expo EAS)](#mobile-app-deployment-expo-eas)
4. [Database Setup (Supabase)](#database-setup-supabase)
5. [Environment Variables](#environment-variables)
6. [Post-Deployment Checklist](#post-deployment-checklist)

---

## Backend Deployment (Railway)

### Prerequisites

- GitHub account
- Railway account (https://railway.app)
- Railway CLI (optional)

### Steps

1. **Connect Repository to Railway**

   - Go to Railway dashboard
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your RunBeat repository

2. **Configure Service**

   - Railway will auto-detect the project
   - Set **Root Directory** to `apps/backend`
   - Set **Start Command** to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables**

   ```bash
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your_anon_key
   SUPABASE_SERVICE_KEY=your_service_key
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIFY_REDIRECT_URI=https://your-railway-domain.up.railway.app/auth/spotify/callback
   OPENAI_API_KEY=your_openai_key
   OPENAI_MODEL=gpt-4
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   CORS_ORIGINS=["https://your-web-railway-domain.up.railway.app","https://your-mobile-app.expo.dev"]
   ```

4. **Deploy**

   - Railway will automatically deploy on push to main branch
   - Wait for deployment to complete
   - Copy the generated domain URL

5. **Update Spotify Redirect URI**
   - Go to Spotify Developer Dashboard
   - Add Railway domain to Redirect URIs:
     `https://your-railway-domain.up.railway.app/auth/spotify/callback`

**Detailed Guide:** See [apps/backend/RAILWAY_DEPLOYMENT.md](../apps/backend/RAILWAY_DEPLOYMENT.md)

---

## Web App Deployment (Railway)

### Prerequisites

- GitHub account
- Railway account (https://railway.app)
- Backend already deployed on Railway

### Steps

1. **Create New Service in Railway**

   - Go to your Railway project dashboard
   - Click "New" → "GitHub Repo"
   - Select your RunBeat repository
   - Railway will create a new service

2. **Configure Service**

   - Set **Root Directory** to `apps/web`
   - Railway will auto-detect Vite project
   - Set **Start Command** to `npm run serve` (uses serve package)
   - Or use Railway's static file serving

3. **Configure Build Settings**

   - Railway will auto-detect Node.js
   - **Build Command:** `npm install && npm run build`
   - **Output Directory:** `dist`
   - Railway will serve the built files automatically

4. **Set Environment Variables**

   ```bash
   VITE_API_URL=https://your-backend-railway-domain.up.railway.app
   VITE_SUPABASE_URL=https://your-project.supabase.co
   VITE_SUPABASE_ANON_KEY=your_anon_key
   NODE_ENV=production
   ```

5. **Deploy**

   - Railway will automatically deploy on push to main branch
   - Or click "Deploy" manually
   - Wait for build to complete
   - Copy the generated domain URL

6. **Update CORS in Backend**

   - Add Railway Web App domain to `CORS_ORIGINS` in Backend service environment variables:

   ```bash
   CORS_ORIGINS=["https://your-web-railway-domain.up.railway.app","https://your-mobile-app.expo.dev"]
   ```

### Railway Configuration

The project includes `railway.json` in `apps/web` directory with proper configuration for static file serving using the `serve` package.

---

## Mobile App Deployment (Expo EAS)

### Prerequisites

- Expo account (https://expo.dev)
- Expo CLI: `npm install -g eas-cli`
- Apple Developer account (for iOS)
- Google Play Console account (for Android)

### Steps

1. **Install EAS CLI**

   ```bash
   npm install -g eas-cli
   ```

2. **Login to Expo**

   ```bash
   eas login
   ```

3. **Configure Project**

   ```bash
   cd apps/mobile
   eas build:configure
   ```

4. **Set Environment Variables**

   - Create `eas.json` or use environment variables in EAS dashboard

   ```json
   {
     "build": {
       "production": {
         "env": {
           "EXPO_PUBLIC_API_URL": "https://your-railway-domain.up.railway.app",
           "EXPO_PUBLIC_SUPABASE_URL": "https://your-project.supabase.co",
           "EXPO_PUBLIC_SUPABASE_ANON_KEY": "your_anon_key"
         }
       }
     }
   }
   ```

5. **Build for iOS**

   ```bash
   eas build --platform ios --profile production
   ```

6. **Build for Android**

   ```bash
   eas build --platform android --profile production
   ```

7. **Submit to App Stores**

   ```bash
   # iOS
   eas submit --platform ios

   # Android
   eas submit --platform android
   ```

**Note:** First-time setup requires additional configuration for app signing.

---

## Database Setup (Supabase)

### Prerequisites

- Supabase account (https://supabase.com)

### Steps

1. **Create Project**

   - Go to Supabase dashboard
   - Click "New Project"
   - Fill in project details
   - Wait for project to be created

2. **Run Migrations**

   - Go to SQL Editor
   - Copy SQL from [PRD_CURSOR_AI.md](../PRD_CURSOR_AI.md) (Database Schema section)
   - Execute the migration SQL

3. **Configure Row Level Security (RLS)**

   - RLS policies are included in the migration SQL
   - Verify policies are enabled in Authentication > Policies

4. **Get API Keys**
   - Go to Settings > API
   - Copy:
     - Project URL
     - `anon` public key
     - `service_role` secret key

---

## Environment Variables

### Backend (.env)

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=https://your-railway-domain.up.railway.app/auth/spotify/callback
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=["https://your-web-domain.vercel.app"]
```

### Web App (.env)

```env
VITE_API_URL=https://your-railway-domain.up.railway.app
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Mobile App (.env)

```env
EXPO_PUBLIC_API_URL=https://your-railway-domain.up.railway.app
EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Post-Deployment Checklist

### Backend

- [ ] Health endpoint responds: `https://your-railway-domain.up.railway.app/health`
- [ ] API docs accessible: `https://your-railway-domain.up.railway.app/docs` (if enabled)
- [ ] Spotify OAuth callback works
- [ ] Database connection successful
- [ ] All environment variables set correctly

### Web App

- [ ] App loads at Railway domain
- [ ] API connection works
- [ ] Spotify OAuth flow works
- [ ] Chat interface functional
- [ ] Playlist generation works

### Mobile App

- [ ] App builds successfully
- [ ] App installs on test devices
- [ ] API connection works
- [ ] Spotify OAuth flow works
- [ ] All features functional

### Database

- [ ] All tables created
- [ ] RLS policies enabled
- [ ] Indexes created
- [ ] Test data can be inserted

### Integration

- [ ] Backend CORS allows frontend domains
- [ ] Spotify redirect URIs configured
- [ ] All services can communicate
- [ ] Error handling works correctly

---

## Troubleshooting

### Backend Issues

**Problem:** Health check fails

- Check Railway logs
- Verify environment variables
- Check database connection

**Problem:** Spotify OAuth fails

- Verify redirect URI matches exactly
- Check Spotify app settings
- Verify client ID and secret

### Web App Issues

**Problem:** API calls fail

- Check CORS settings in backend
- Verify API URL in environment variables
- Check browser console for errors
- Verify Railway domain is added to CORS_ORIGINS

**Problem:** Build fails on Railway

- Check Railway build logs
- Verify Node.js version compatibility
- Ensure all dependencies are in package.json
- Check that build command completes successfully

### Mobile App Issues

**Problem:** Build fails

- Check EAS build logs
- Verify environment variables
- Check app.json configuration

---

## Monitoring

### Backend Monitoring

- Railway provides built-in logs and metrics
- Set up alerts for errors
- Monitor API response times

### Web App Monitoring

- Railway provides built-in logs and metrics
- Set up error tracking (Sentry recommended)
- Monitor page load times
- Check Railway dashboard for deployment status

### Mobile App Monitoring

- Use Expo's built-in analytics
- Set up crash reporting
- Monitor app performance

---

## Security Checklist

- [ ] All API keys stored as environment variables
- [ ] Service keys never exposed to frontend
- [ ] RLS policies enabled in Supabase
- [ ] HTTPS enabled for all services
- [ ] CORS configured correctly
- [ ] Rate limiting implemented (future)
- [ ] Input validation on all endpoints
- [ ] Error messages don't expose sensitive info

---

## Support

For issues or questions:

- Check [PRD_CURSOR_AI.md](../PRD_CURSOR_AI.md) for architecture details
- Review [API.md](./API.md) for endpoint documentation
- Check individual app README files for specific setup

---

**Last Updated:** 12.11.2025
