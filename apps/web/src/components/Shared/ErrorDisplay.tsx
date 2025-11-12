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
    <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
            Помилка
          </h3>
          <p className="mt-1 text-sm text-red-700 dark:text-red-300">
            {error}
          </p>
          <p className="mt-2 text-xs text-red-600 dark:text-red-400">
            Перевірте консоль браузера для деталей (F12)
          </p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="ml-4 text-red-400 hover:text-red-600"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
}

