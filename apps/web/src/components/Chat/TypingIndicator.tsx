export function TypingIndicator() {
  return (
    <div className="flex justify-start mb-4 animate-in fade-in duration-200">
      <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl px-4 py-3 shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 dark:text-gray-400 mr-1">
            AI думає
          </span>
          <div className="flex gap-1">
            <div className="w-2 h-2 bg-blue-500 dark:bg-blue-400 rounded-full animate-bounce" />
            <div
              className="w-2 h-2 bg-blue-500 dark:bg-blue-400 rounded-full animate-bounce"
              style={{ animationDelay: '0.1s' }}
            />
            <div
              className="w-2 h-2 bg-blue-500 dark:bg-blue-400 rounded-full animate-bounce"
              style={{ animationDelay: '0.2s' }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

