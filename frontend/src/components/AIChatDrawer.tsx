'use client';

import React, { useState } from 'react';
import { AgentChatResponse, ToolCallTrace } from '../lib/types';
import { api } from '../lib/api';
import { X, Sparkles, Send, Bot, User, Wrench, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface AIChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onPlanUpdated: () => void;
}

interface Message {
  sender: 'user' | 'agent';
  text: string;
  toolCalls?: ToolCallTrace[];
}

/**
 * Parses markdown text into formatted JSX elements (bold, headers, bullet lists, code blocks).
 * Prevents raw markdown symbols (###, **, -) from showing to the user.
 */
const FormattedMarkdownText: React.FC<{ text: string }> = ({ text }) => {
  if (!text) return null;

  // Split into code blocks and normal blocks
  const parts = text.split(/(```[\s\S]*?```)/g);

  return (
    <div className="space-y-2">
      {parts.map((part, pIdx) => {
        // Code Block
        if (part.startsWith('```') && part.endsWith('```')) {
          const content = part.replace(/^```[a-zA-Z]*\n?/, '').replace(/\n?```$/, '');
          return (
            <pre
              key={pIdx}
              className="bg-surface-card/90 p-3 rounded-xl border border-gray-800 font-mono text-xs text-indigo-300 my-2 overflow-x-auto shadow-inner"
            >
              <code>{content}</code>
            </pre>
          );
        }

        // Paragraphs / lines
        const lines = part.split('\n');
        return (
          <div key={pIdx} className="space-y-1.5">
            {lines.map((line, lIdx) => {
              const trimmed = line.trim();
              if (!trimmed) return null;

              // Headers: ### Header or ## Header
              if (trimmed.startsWith('#')) {
                const headerText = trimmed.replace(/^#+\s*/, '');
                return (
                  <h4 key={lIdx} className="text-base font-bold text-white mt-3 mb-1 tracking-tight">
                    {renderInlineFormatted(headerText)}
                  </h4>
                );
              }

              // Bullet Items: - item or * item
              if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
                const itemText = trimmed.replace(/^[-*]\s+/, '');
                return (
                  <div key={lIdx} className="flex items-start gap-2 text-sm text-gray-200 pl-1 my-0.5">
                    <span className="text-cyan-400 font-bold select-none">•</span>
                    <span>{renderInlineFormatted(itemText)}</span>
                  </div>
                );
              }

              // Normal text line
              return (
                <p key={lIdx} className="text-sm text-gray-200 leading-relaxed">
                  {renderInlineFormatted(line)}
                </p>
              );
            })}
          </div>
        );
      })}
    </div>
  );
};

/**
 * Helper to render inline formatting (**bold**, *italic*) cleanly.
 */
function renderInlineFormatted(text: string): React.ReactNode[] {
  // Regex to split by **bold** or *italic*
  const tokens = text.split(/(\*\*.*?\*\*|\*.*?\*)/g);
  return tokens.map((token, idx) => {
    if (token.startsWith('**') && token.endsWith('**')) {
      return (
        <strong key={idx} className="font-bold text-white">
          {token.slice(2, -2)}
        </strong>
      );
    }
    if (token.startsWith('*') && token.endsWith('*') && token.length > 2) {
      return (
        <em key={idx} className="italic text-gray-300">
          {token.slice(1, -1)}
        </em>
      );
    }
    return <React.Fragment key={idx}>{token}</React.Fragment>;
  });
}

export const AIChatDrawer: React.FC<AIChatDrawerProps> = ({
  isOpen,
  onClose,
  onPlanUpdated,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'agent',
      text: "👋 Hi! I'm your **Personal Planning Agent**. Tell me what tasks you need to get done, or ask me *'What should I work on today?'*",
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const quickPrompts = [
    'What should I work on today?',
    'What tasks are overdue?',
    'I need to prepare PostgreSQL interview questions by tomorrow. Make it high priority.',
    'Break my project documentation task into subtasks',
  ];

  const handleSend = async (messageText?: string) => {
    const textToSend = messageText || input;
    if (!textToSend.trim() || loading) return;

    setMessages((prev) => [...prev, { sender: 'user', text: textToSend }]);
    if (!messageText) setInput('');
    setLoading(true);

    try {
      const res: AgentChatResponse = await api.sendAgentChat(textToSend);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'agent',
          text: res.response,
          toolCalls: res.tool_calls,
        },
      ]);
      onPlanUpdated();
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'agent',
          text: 'Sorry, I encountered an issue communicating with the planning server.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-surface border-l border-gray-800 shadow-2xl flex flex-col"
          >
            {/* Header */}
            <div className="p-4 border-b border-gray-800 flex items-center justify-between bg-surface-card/60">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 to-cyan-400 flex items-center justify-center shadow-md">
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">AI Planning Assistant</h3>
                  <span className="text-[10px] text-cyan-400 font-semibold block">Context-Aware Schedule Reasoning</span>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Quick Prompt Bar */}
            <div className="p-3 border-b border-gray-800/80 bg-surface/50 overflow-x-auto flex gap-2">
              {quickPrompts.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(p)}
                  className="px-2.5 py-1 rounded-full bg-surface-card border border-gray-800 text-[11px] text-gray-300 hover:text-white hover:border-indigo-500 whitespace-nowrap transition"
                >
                  {p.length > 30 ? p.substring(0, 30) + '...' : p}
                </button>
              ))}
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((m, idx) => (
                <div
                  key={idx}
                  className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
                >
                  <div className="flex items-center gap-1.5 mb-1 text-[11px] font-semibold text-gray-400">
                    {m.sender === 'user' ? (
                      <>
                        <span>You</span>
                        <User className="w-3.5 h-3.5 text-indigo-400" />
                      </>
                    ) : (
                      <>
                        <Bot className="w-3.5 h-3.5 text-cyan-400" />
                        <span>AI Agent</span>
                      </>
                    )}
                  </div>

                  {/* Tool Call activity badges */}
                  {m.toolCalls && m.toolCalls.length > 0 && (
                    <div className="mb-2 space-y-1">
                      {m.toolCalls.map((tc, tidx) => (
                        <div
                          key={tidx}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-indigo-950/40 border border-indigo-500/30 text-[10px] font-mono text-indigo-300"
                        >
                          <Wrench className="w-3 h-3 text-cyan-300" />
                          <span>Tool Executed: <strong>{tc.tool_name}()</strong></span>
                        </div>
                      ))}
                    </div>
                  )}

                  <div
                    className={`max-w-[88%] rounded-2xl p-4 text-sm leading-relaxed ${
                      m.sender === 'user'
                        ? 'bg-indigo-600 text-white rounded-br-none shadow-md shadow-indigo-600/20'
                        : 'glass-panel text-gray-200 rounded-bl-none border border-gray-800'
                    }`}
                  >
                    <FormattedMarkdownText text={m.text} />
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex items-center gap-2 text-xs text-gray-400 italic font-mono">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-cyan-400" />
                  <span>Agent analyzing schedule & tool parameters...</span>
                </div>
              )}
            </div>

            {/* Input Box */}
            <div className="p-4 border-t border-gray-800 bg-surface-card/60">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSend();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  placeholder="e.g. Prepare project docs by Friday (4 hrs effort)..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  className="flex-1 px-4 py-2.5 bg-surface border border-gray-800 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                />
                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                  className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold shadow-md transition"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
