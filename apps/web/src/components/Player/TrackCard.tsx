import type { Track } from '../../types';

interface TrackCardProps {
  track: Track;
  index: number;
}

export function TrackCard({ track, index }: TrackCardProps) {
  const formatDuration = (ms: number) => {
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex items-center gap-4 p-3 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors">
      <span className="text-gray-500 dark:text-gray-400 w-8 text-sm">
        {index}
      </span>
      <div className="flex-1 min-w-0">
        <h3 className="font-medium truncate">{track.name}</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
          {track.artist}
        </p>
      </div>
      <div className="text-sm text-gray-500 dark:text-gray-400">
        {formatDuration(track.duration_ms)}
      </div>
      <div className="text-xs text-gray-400">
        {Math.round(track.bpm)} BPM
      </div>
    </div>
  );
}

