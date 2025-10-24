import { motion } from 'framer-motion';
import { Database, Cpu, Zap, BookOpen, Brain, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Welcome() {
  return (
    <div className="min-h-screen overflow-hidden">
      {/* Animated background */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-electric-teal/20 rounded-full blur-3xl animate-pulse-glow" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blaze-orange/20 rounded-full blur-3xl animate-pulse-glow" style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-cool-blue/10 rounded-full blur-3xl animate-pulse-glow" style={{ animationDelay: '4s' }} />
      </div>

      <div className="container mx-auto px-6 py-12">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          {/* Hero Image */}
          <motion.div
            className="mb-8"
            animate={{ y: [0, -20, 0] }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          >
            <img
              src="/assets/hero.png"
              alt="Code-Forge Hero"
              className="mx-auto max-w-2xl w-full drop-shadow-[0_0_50px_rgba(0,255,255,0.6)]"
            />
          </motion.div>

          {/* Subtitle */}
          <p className="text-2xl text-electric-teal mb-8">
            Production-Grade RAG System with PostgreSQL + pgvector
          </p>

          {/* CTA Button */}
          <Link to="/app">
            <motion.button
              className="btn-primary text-xl px-12 py-4 inline-flex items-center gap-3 font-bold"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Get Started
              <ArrowRight className="w-6 h-6" />
            </motion.button>
          </Link>
        </motion.div>

        {/* Features Grid */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.8 }}
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16"
        >
          <FeatureCard
            icon={<Database className="w-8 h-8" />}
            title="PostgreSQL + pgvector"
            description="ACID-compliant vector database with production-grade reliability"
            delay={0.1}
          />
          <FeatureCard
            icon={<Cpu className="w-8 h-8" />}
            title="Local LLMs"
            description="Powered by Ollama - no API keys, complete privacy"
            delay={0.2}
          />
          <FeatureCard
            icon={<Zap className="w-8 h-8" />}
            title="MCP Integration"
            description="Expose knowledge bases to AI agents via Model Context Protocol"
            delay={0.3}
          />
          <FeatureCard
            icon={<BookOpen className="w-8 h-8" />}
            title="Multi-KB Architecture"
            description="Isolated knowledge bases per project with type-aware organization"
            delay={0.4}
          />
          <FeatureCard
            icon={<Brain className="w-8 h-8" />}
            title="Advanced RAG"
            description="Vector search, hybrid search, reranking, and agentic RAG modes"
            delay={0.5}
          />
          <FeatureCard
            icon={<Zap className="w-8 h-8" />}
            title="High-Tech UI"
            description="Electric teal & blaze orange design that looks fucking amazing"
            delay={0.6}
          />
        </motion.div>

        {/* Quick Start */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.8 }}
          className="max-w-3xl mx-auto"
        >
          <div className="card">
            <h2 className="text-3xl font-bold mb-6 gradient-text">🎯 Quick Start</h2>
            <ol className="space-y-4 text-lg">
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-8 h-8 rounded-full bg-electric-teal text-deep-night flex items-center justify-center font-bold">1</span>
                <span>Click <strong className="text-electric-teal">"Get Started"</strong> to access the main application</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-8 h-8 rounded-full bg-electric-teal text-deep-night flex items-center justify-center font-bold">2</span>
                <span>Create a <strong className="text-cool-blue">Knowledge Base</strong> from the left panel</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-8 h-8 rounded-full bg-electric-teal text-deep-night flex items-center justify-center font-bold">3</span>
                <span>Upload documents or import a directory</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-8 h-8 rounded-full bg-electric-teal text-deep-night flex items-center justify-center font-bold">4</span>
                <span>Start chatting with your knowledge base using <strong className="text-blaze-orange">advanced RAG</strong></span>
              </li>
            </ol>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  delay: number;
}

function FeatureCard({ icon, title, description, delay }: FeatureCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
      whileHover={{ scale: 1.02 }}
      className="card"
    >
      <div className="text-electric-teal mb-4">{icon}</div>
      <h3 className="text-xl font-bold mb-2 text-white">{title}</h3>
      <p className="text-light-grey">{description}</p>
    </motion.div>
  );
}

