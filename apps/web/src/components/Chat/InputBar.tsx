import { useState, FormEvent } from 'react';

interface InputBarProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export function InputBar({ onSend, disabled }: InputBarProps) {
  const [input, setInput] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-gray-200 dark:border-gray-700 p-2 md:p-4 bg-white dark:bg-gray-800"
    >
      <div className="flex gap-2 max-w-4xl mx-auto min-w-0">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Наприклад: 'хочу легку пробіжку 30 хв під електронну музику' або 'інтервали 40 хв, рок-музика'..."
          disabled={disabled}
          className="flex-1 min-w-0 px-3 md:px-4 py-2 text-sm md:text-base border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="px-4 md:px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm md:text-base whitespace-nowrap"
        >
          Відправити
        </button>
      </div>
    </form>
  );
}

