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

- ✅ Chat interface with AI
- ✅ Playlist generation
- ✅ Spotify integration
- ✅ Workout history
- ✅ User preferences
- ✅ Responsive design with Tailwind CSS

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

This project uses Tailwind CSS for styling. Configuration is in `tailwind.config.js`.

## 📚 Documentation

See [PRD_CURSOR_AI.md](../../PRD_CURSOR_AI.md) for full project documentation.

