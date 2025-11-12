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

- ✅ Chat interface with AI
- ✅ Playlist generation
- ✅ Spotify integration
- ✅ Workout history
- ✅ User preferences

## 🧪 Development

```bash
# Run on iOS
npm run ios

# Run on Android
npm run android

# Run on Web
npm run web
```

## 📚 Documentation

See [PRD_CURSOR_AI.md](../../PRD_CURSOR_AI.md) for full project documentation.

