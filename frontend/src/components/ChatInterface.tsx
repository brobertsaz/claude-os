import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, Loader2, Copy, CheckCircle } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { chat, type ChatResponse } from '../lib/api';
import ReactMarkdown from 'react-markdown';

interface ChatInterfaceProps {
  kbName: string;
  useHybrid: boolean;
  useRerank: boolean;
  useAgentic: boolean;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
}

export default function ChatInterface({ kbName, useHybrid, useRerank, useAgentic }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [thinkingTime, setThinkingTime] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const thinkingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const chatMutation = useMutation({
    mutationFn: (query: string) => chat(kbName, query, useHybrid, useRerank, useAgentic),
    onSuccess: (data: ChatResponse) => {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer || data.error || 'No response',
          sources: data.sources,
        },
      ]);
    },
  });

  // Timer effect for thinking animation
  useEffect(() => {
    if (chatMutation.isPending) {
      setThinkingTime(0);
      thinkingIntervalRef.current = setInterval(() => {
        setThinkingTime((prev) => prev + 0.1);
      }, 100);
    } else {
      if (thinkingIntervalRef.current) {
        clearInterval(thinkingIntervalRef.current);
        thinkingIntervalRef.current = null;
      }
    }

    return () => {
      if (thinkingIntervalRef.current) {
        clearInterval(thinkingIntervalRef.current);
      }
    };
  }, [chatMutation.isPending]);

  const handleSend = () => {
    if (!input.trim() || chatMutation.isPending) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    chatMutation.mutate(input);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Bot className="w-16 h-16 text-electric-teal/50 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-light-grey mb-2">Start a Conversation</h2>
              <p className="text-light-grey">Ask anything about your knowledge base</p>
              <div className="mt-6 space-y-2">
                <div className="text-sm text-light-grey">
                  <strong className="text-electric-teal">Active Settings:</strong>
                </div>
                <div className="flex gap-2 justify-center flex-wrap">
                  {useHybrid && (
                    <span className="px-3 py-1 bg-electric-teal/20 border border-electric-teal/50 rounded-full text-xs">
                      Hybrid Search
                    </span>
                  )}
                  {useRerank && (
                    <span className="px-3 py-1 bg-cool-blue/20 border border-cool-blue/50 rounded-full text-xs">
                      Reranking
                    </span>
                  )}
                  {useAgentic && (
                    <span className="px-3 py-1 bg-blaze-orange/20 border border-blaze-orange/50 rounded-full text-xs">
                      Agentic RAG
                    </span>
                  )}
                  {!useHybrid && !useRerank && !useAgentic && (
                    <span className="px-3 py-1 bg-light-grey/20 border border-light-grey/50 rounded-full text-xs">
                      Basic Vector Search
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <AnimatePresence>
            {messages.map((message, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role === 'assistant' && (
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-electric-teal/20 flex items-center justify-center">
                    <Bot className="w-6 h-6 text-electric-teal" />
                  </div>
                )}

                <div
                  className={`max-w-3xl rounded-2xl p-4 ${
                    message.role === 'user'
                      ? 'bg-gradient-to-r from-electric-teal to-cool-blue text-deep-night'
                      : 'bg-cool-blue/10 border border-electric-teal/30'
                  }`}
                >
                  <div className="prose prose-invert max-w-none">
                    {message.role === 'assistant' ? (
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    ) : (
                      <p className="m-0">{message.content}</p>
                    )}
                  </div>

                  {message.role === 'assistant' && (
                    <div className="mt-3 flex items-center gap-2">
                      <button
                        onClick={() => copyToClipboard(message.content, index)}
                        className="text-xs px-3 py-1 rounded bg-electric-teal/20 hover:bg-electric-teal/30 transition-colors flex items-center gap-1"
                      >
                        {copiedIndex === index ? (
                          <>
                            <CheckCircle className="w-3 h-3" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" />
                            Copy
                          </>
                        )}
                      </button>
                      {message.sources && message.sources.length > 0 && (
                        <span className="text-xs text-light-grey">
                          {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {message.role === 'user' && (
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blaze-orange/20 flex items-center justify-center">
                    <User className="w-6 h-6 text-blaze-orange" />
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        )}

        {chatMutation.isPending && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-4"
          >
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-electric-teal/20 flex items-center justify-center">
              <Bot className="w-6 h-6 text-electric-teal" />
            </div>
            <div className="bg-cool-blue/10 border border-electric-teal/30 rounded-2xl p-4 min-w-[200px]">
              <div className="flex items-center gap-3">
                <Loader2 className="w-5 h-5 text-electric-teal animate-spin flex-shrink-0" />
                <div className="flex flex-col">
                  <span className="text-sm text-light-grey">Thinking...</span>
                  <span className="text-xs text-electric-teal font-mono">
                    {thinkingTime.toFixed(1)}s
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-electric-teal/30 p-6 bg-deep-night">
        <div className="flex gap-4">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question about your knowledge base..."
            className="input flex-1 resize-none h-12"
            rows={1}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || chatMutation.isPending}
            className="btn-primary px-6 flex items-center gap-2"
          >
            {chatMutation.isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <Send className="w-5 h-5" />
                Send
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
