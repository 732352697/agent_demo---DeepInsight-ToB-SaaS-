"use client";

import { useState, KeyboardEvent, FormEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Sparkles, StopCircle, Loader2 } from "lucide-react";

interface ChatInputProps {
  onSubmit: (message: string) => void;
  onStop?: () => void;
  isLoading?: boolean;
  placeholder?: string;
  disabled?: boolean;
}

export default function ChatInput({
  onSubmit,
  onStop,
  isLoading = false,
  placeholder = "输入直播主题，例如：'规划一场关于 Cursor 更新的直播'",
  disabled = false,
}: ChatInputProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || disabled) return;
    onSubmit(input.trim());
    setInput("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="fixed bottom-6 left-1/2 -translate-x-1/2 w-full max-w-3xl px-4"
    >
      <form
        onSubmit={handleSubmit}
        className="relative gradient-border group"
      >
        <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-primary/10 via-accent/10 to-primary/10 opacity-50 group-hover:opacity-100 transition-opacity duration-300" />
        
        <div className="relative flex items-end gap-3 p-3 bg-background/80 backdrop-blur-xl rounded-xl">
          {/* Sparkle decoration */}
          <div className="absolute -top-3 left-4">
            <motion.div
              animate={{ rotate: [0, 180, 360] }}
              transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
              className="w-6 h-6 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center"
            >
              <Sparkles className="w-3 h-3 text-white" />
            </motion.div>
          </div>

          {/* Input */}
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || isLoading}
            rows={1}
            className="
              flex-1 bg-transparent border-none outline-none
              text-sm text-white placeholder-gray-500
              resize-none max-h-32 min-h-[44px]
              disabled:opacity-50
            "
            style={{ fieldSizing: "content" } as React.CSSProperties}
          />

          {/* Submit/Stop Button */}
          <AnimatePresence mode="wait">
            {isLoading ? (
              <motion.button
                key="stop"
                type="button"
                onClick={onStop}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.8, opacity: 0 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="p-3 rounded-xl bg-red-500/20 border border-red-500/50 hover:bg-red-500/30 transition-colors"
              >
                <StopCircle className="w-5 h-5 text-red-400" />
              </motion.button>
            ) : (
              <motion.button
                key="send"
                type="submit"
                disabled={!input.trim() || disabled}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.8, opacity: 0 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="
                  p-3 rounded-xl
                  bg-gradient-to-r from-primary to-accent
                  disabled:from-gray-600 disabled:to-gray-600
                  transition-all duration-200
                  disabled:opacity-50 disabled:cursor-not-allowed
                "
              >
                <Send className="w-5 h-5 text-white" />
              </motion.button>
            )}
          </AnimatePresence>
        </div>

        {/* Loading indicator */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute -top-8 left-4 flex items-center gap-2 text-xs text-gray-400"
          >
            <Loader2 className="w-3 h-3 animate-spin" />
            <span>AI 正在思考中...</span>
          </motion.div>
        )}
      </form>

      {/* Decorative glow */}
      <div className="absolute -inset-4 -z-10 bg-gradient-to-r from-primary/20 via-accent/20 to-primary/20 blur-2xl opacity-30 group-hover:opacity-50 transition-opacity duration-300" />
    </motion.div>
  );
}
