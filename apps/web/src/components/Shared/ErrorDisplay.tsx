import { useEffect } from 'react';

interface ErrorDisplayProps {
  error: string | null;
  onDismiss?: () => void;
}

export function ErrorDisplay({ error, onDismiss }: ErrorDisplayProps) {
  useEffect(() => {
    if (error) {
      console.error('Error displayed:', error);
    }
  }, [error]);

  if (!error) return null;

  return (
    <div className="bg-red-900/20 border border-red-800 rounded-xl p-4 mb-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-subhead font-semibold text-red-400">
            Помилка
          </h3>
          <p className="mt-1 text-body text-red-300">
            {error}
          </p>
          <p className="mt-2 text-caption text-red-400">
            Перевірте консоль браузера для деталей (F12)
          </p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="ml-4 text-red-400 hover:text-red-300 transition-colors"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
}

