# RunBeat Mobile App

React Native + Expo mobile application for RunBeat.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Expo CLI: `npm install -g expo-cli`
- iOS Simulator (Mac) or Android Emulator

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env
# Fill in .env with your configuration

# Start Expo development server
npm start
# or
npx expo start
```

### Running on Device

- **iOS**: Press `i` in terminal or scan QR code with Camera app
- **Android**: Press `a` in terminal or scan QR code with Expo Go app
- **Web**: Press `w` in terminal

## 📁 Project Structure

```
src/
├── components/        # Reusable UI components
│   ├── Chat/         # Chat-related components
│   ├── Player/       # Player-related components
│   └── Shared/       # Shared components
├── hooks/            # Custom React hooks
├── navigation/       # Navigation setup
├── screens/          # Screen components
├── services/         # API and service integrations
├── store/            # State management (Zustand)
└── types/            # TypeScript type definitions
```

## 🔧 Configuration

Set the following environment variables in `.env`:

- `EXPO_PUBLIC_API_URL` - Backend API URL
- `EXPO_PUBLIC_SUPABASE_URL` - Supabase project URL
- `EXPO_PUBLIC_SUPABASE_ANON_KEY` - Supabase anonymous key

## 📱 Features

### Core Features
- ✅ **AI Chat Interface** - Natural language workout planning
- ✅ **Dual Playlist Variants** - Choose between 2 generated options
- ✅ **Spotify Integration** - Save playlists directly to Spotify
- ✅ **Workout History** - View and reuse past workouts
- ✅ **Playlist History** - Access all your generated playlists
- ✅ **Native Performance** - Smooth animations and gestures

### Mobile-Specific
- 📱 Native navigation with React Navigation v6
- 🎨 Platform-specific UI (iOS/Android)
- ⚡ Optimized for mobile performance
- 🔔 Push notifications (planned)

## 🧪 Development

```bash
# Run on iOS
npm run ios

# Run on Android
npm run android

# Run on Web
npm run web

# Start with tunnel for testing on real device
npx expo start --tunnel
```

## 🔧 Tech Stack

- **React Native 0.73** - Mobile framework
- **Expo SDK 49** - Development platform
- **TypeScript** - Type safety
- **Zustand** - State management
- **React Navigation v6** - Navigation
- **Axios** - HTTP client

## 📚 Documentation

- [Architecture Report](../../docs/ARCHITECTURE_REPORT.md) - Complete system architecture
- [PRD](../../PRD_CURSOR_AI.md) - Product Requirements Document
- [Mobile Section](../../docs/ARCHITECTURE_REPORT.md#mobile-app-архітектура) - Detailed mobile docs

