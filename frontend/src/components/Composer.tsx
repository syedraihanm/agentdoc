import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Loader2 } from 'lucide-react';

interface ComposerProps {
  onSend: (question: string) => void;
  disabled?: boolean;
}

export const Composer: React.FC<ComposerProps> = ({ onSend, disabled }) => {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!disabled && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [disabled]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 180)}px`;
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="flex items-end gap-2 p-2 rounded-2xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-sm focus-within:border-primary dark:focus-within:border-primary-dark focus-within:ring-2 focus-within:ring-primary/20 transition-all">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={disabled ? "Agent is reasoning and fetching pages..." : "Ask a question about the document..."}
          rows={1}
          className="flex-1 max-h-40 p-2 bg-transparent text-sm text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-hidden resize-none leading-relaxed"
        />

        <button
          type="submit"
          disabled={disabled || !text.trim()}
          className="p-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white disabled:opacity-30 disabled:pointer-events-none transition-all shadow-xs shrink-0"
        >
          {disabled ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <ArrowUp className="w-4 h-4 stroke-[2.5]" />
          )}
        </button>
      </div>

      <div className="flex items-center justify-between px-2 pt-1.5 text-[11px] text-slate-400 dark:text-slate-500 font-sans">
        <span>Enter to send · Shift+Enter for new line</span>
        <span>Hard tool budget: ≤ 6 calls / question</span>
      </div>
    </form>
  );
};