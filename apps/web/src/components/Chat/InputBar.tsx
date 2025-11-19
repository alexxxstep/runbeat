import { useState, useRef, useEffect, FormEvent } from 'react';

interface InputBarProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export function InputBar({ onSend, disabled }: InputBarProps) {
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!disabled) {
      inputRef.current?.focus();
    }
  }, [disabled]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
      inputRef.current?.focus();
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-app-border p-4 md:p-6 bg-app-surface"
    >
      <div className="flex gap-3 max-w-4xl mx-auto">
        <input
          type="text"
          value={input}
          ref={inputRef}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Наприклад: 'хочу легку пробіжку 30 хв під електронну музику' або 'інтервали 40 хв, рок-музика'..."
          disabled={disabled}
          autoFocus
          className="flex-1 px-4 py-3 text-body border border-app-border rounded-xl focus:outline-none focus:ring-2 focus:ring-app-accent bg-app-surface-light text-app-text placeholder-app-text-tertiary"
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="px-6 py-3 bg-app-accent text-white rounded-xl hover:bg-app-accent-hover disabled:opacity-50 disabled:cursor-not-allowed text-body whitespace-nowrap font-semibold"
        >
          Відправити
        </button>
      </div>
    </form>
  );
}

