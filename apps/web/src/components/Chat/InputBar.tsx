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
      className="border-t border-track-line p-2 md:p-4 bg-track-darker glow-border-dim"
    >
      <div className="flex gap-2 max-w-4xl mx-auto">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Наприклад: 'хочу легку пробіжку 30 хв під електронну музику' або 'інтервали 40 хв, рок-музика'..."
          disabled={disabled}
          className="flex-1 px-3 md:px-4 py-2 text-sm md:text-base font-mono border border-track-line rounded-lg focus:outline-none focus:ring-2 focus:ring-track-accent bg-track-dark text-track-accent placeholder-track-accent-dim glow-border-dim"
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="px-4 md:px-6 py-2 bg-track-accent text-track-dark rounded-lg hover:bg-track-accent-bright disabled:opacity-50 disabled:cursor-not-allowed text-sm md:text-base whitespace-nowrap font-mono font-bold glow-border"
        >
          ВІДПРАВИТИ
        </button>
      </div>
    </form>
  );
}

