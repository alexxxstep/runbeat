# RunBeat Web App

React + Vite web application for RunBeat.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env
# Fill in .env with your configuration

# Start development server
npm run dev
```

The app will be available at `http://localhost:5173`

## 📁 Project Structure

```
src/
├── components/        # Reusable UI components
│   ├── Chat/         # Chat-related components
│   ├── Player/       # Player-related components
│   └── Shared/       # Shared components
├── hooks/            # Custom React hooks
├── pages/            # Page components
├── services/         # API and service integrations
├── stores/           # State management (Zustand)
└── types/            # TypeScript type definitions
```

## 🔧 Configuration

Set the following environment variables in `.env`:

- `VITE_API_URL` - Backend API URL
- `VITE_SUPABASE_URL` - Supabase project URL
- `VITE_SUPABASE_ANON_KEY` - Supabase anonymous key

## 📱 Features

### Core Features
- ✅ **AI Chat Interface** - Natural language workout planning
- ✅ **Dual Playlist Variants** - Choose between 2 generated options
- ✅ **Spotify Integration** - Save playlists directly to Spotify
- ✅ **Workout History Panel** - View and reuse past workouts
- ✅ **Playlist History** - Access all your generated playlists
- ✅ **Track Management** - Exclude unwanted tracks, regenerate variants
- ✅ **Responsive Design** - Works on mobile, tablet, and desktop

### User Experience
- 🎯 **7-Step User Flow**
  1. Describe workout in natural language (via AI chat)
  2. AI asks clarifying questions if needed
  3. AI creates workout & generates 2 playlist variants
  4. **OR** Create custom workout via right panel manually
  5. Choose best variant, exclude unwanted tracks
  6. Use right history panel to navigate workouts/playlists
  7. Generate new playlists for saved workouts

### Technical Features
- ⚡ Real-time chat with streaming responses
- 🎨 Dark/Light theme support
- 📱 Mobile-optimized sidebar navigation
- 🔄 Automatic history refresh on workout/playlist creation
- ❌ Error handling with user-friendly messages

## 🧪 Development

```bash
# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 🎨 Styling

This project uses:
- **Tailwind CSS** - Utility-first CSS framework
- **Custom Design Tokens** - See `tailwind.config.js` for theme
- **Responsive Breakpoints** - Mobile-first approach
- **Dark Mode Support** - Automatic theme switching

## 📚 Documentation

- [Architecture Report](../../docs/ARCHITECTURE_REPORT.md) - Complete system architecture
- [PRD](../../PRD_CURSOR_AI.md) - Product Requirements Document
- [Frontend Section](../../docs/ARCHITECTURE_REPORT.md#frontend-архітектура) - Detailed frontend docs

## 🔧 Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **React Router v6** - Routing
- **Axios** - HTTP client

