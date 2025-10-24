import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Home, Settings, Database, MessageSquare, Plus, Trash2, HelpCircle } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { listKnowledgeBases, createKnowledgeBase, deleteKnowledgeBase, type KnowledgeBase } from '../lib/api';
import ChatInterface from '../components/ChatInterface';
import KBManagement from '../components/KBManagement';
import HelpDocs from '../components/HelpDocs';

export default function MainApp() {
  const [selectedKB, setSelectedKB] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'kb' | 'chat' | 'help'>('kb');
  const [showCreateKB, setShowCreateKB] = useState(false);
  const [newKBName, setNewKBName] = useState('');
  const [newKBType, setNewKBType] = useState('generic');
  const [newKBDesc, setNewKBDesc] = useState('');

  // RAG settings
  const [useHybrid, setUseHybrid] = useState(false);
  const [useRerank, setUseRerank] = useState(false);
  const [useAgentic, setUseAgentic] = useState(false);

  const queryClient = useQueryClient();

  // Fetch knowledge bases
  const { data: kbs = [], isLoading } = useQuery({
    queryKey: ['knowledge-bases'],
    queryFn: listKnowledgeBases,
  });

  // Create KB mutation
  const createKBMutation = useMutation({
    mutationFn: () => createKnowledgeBase(newKBName, newKBType, newKBDesc),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases'] });
      setShowCreateKB(false);
      setNewKBName('');
      setNewKBType('generic');
      setNewKBDesc('');
    },
  });

  // Delete KB mutation
  const deleteKBMutation = useMutation({
    mutationFn: (kb_name: string) => deleteKnowledgeBase(kb_name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases'] });
    },
  });

  const handleCreateKB = () => {
    if (newKBName.trim()) {
      createKBMutation.mutate();
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top Navigation */}
      <nav className="bg-deep-night border-b border-electric-teal/30 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <img src="/assets/logo.png" alt="Code-Forge" className="h-10" />
            <h1 className="text-2xl font-bold gradient-text">CODE-FORGE</h1>
          </div>
          <div className="flex gap-2">
            <Link to="/">
              <button className="btn-secondary flex items-center gap-2">
                <Home className="w-4 h-4" />
                Welcome
              </button>
            </Link>
          </div>
        </div>
      </nav>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <aside className="w-80 bg-gradient-to-b from-deep-night to-cool-blue/5 border-r border-electric-teal/30 p-6 overflow-y-auto">
          {/* Settings Section */}
          <div className="mb-6">
            <h2 className="text-lg font-bold text-electric-teal mb-3 flex items-center gap-2">
              <Settings className="w-5 h-5" />
              RAG Settings
            </h2>
            <div className="space-y-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useHybrid}
                  onChange={(e) => setUseHybrid(e.target.checked)}
                  className="w-4 h-4 accent-electric-teal"
                />
                <span className="text-sm">Hybrid Search (Vector + BM25)</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useRerank}
                  onChange={(e) => setUseRerank(e.target.checked)}
                  className="w-4 h-4 accent-electric-teal"
                />
                <span className="text-sm">Reranking</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useAgentic}
                  onChange={(e) => setUseAgentic(e.target.checked)}
                  className="w-4 h-4 accent-electric-teal"
                />
                <span className="text-sm">Agentic RAG</span>
              </label>
            </div>
          </div>

          {/* Knowledge Bases List */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-bold text-electric-teal flex items-center gap-2">
                <Database className="w-5 h-5" />
                Knowledge Bases
              </h2>
              <button
                onClick={() => setShowCreateKB(!showCreateKB)}
                className="p-1 rounded hover:bg-electric-teal/20 transition-colors"
              >
                <Plus className="w-5 h-5 text-electric-teal" />
              </button>
            </div>

            {/* Create KB Form */}
            <AnimatePresence>
              {showCreateKB && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mb-4 p-4 bg-cool-blue/10 rounded-lg border border-electric-teal/30"
                >
                  <input
                    type="text"
                    placeholder="KB Name"
                    value={newKBName}
                    onChange={(e) => setNewKBName(e.target.value)}
                    className="input w-full mb-2"
                  />
                  <select
                    value={newKBType}
                    onChange={(e) => setNewKBType(e.target.value)}
                    className="input w-full mb-2"
                  >
                    <option value="generic">Generic</option>
                    <option value="code">Code</option>
                    <option value="documentation">Documentation</option>
                    <option value="agent-os">Agent OS</option>
                  </select>
                  <input
                    type="text"
                    placeholder="Description (optional)"
                    value={newKBDesc}
                    onChange={(e) => setNewKBDesc(e.target.value)}
                    className="input w-full mb-2"
                  />
                  <button
                    onClick={handleCreateKB}
                    disabled={!newKBName.trim() || createKBMutation.isPending}
                    className="btn-primary w-full text-sm"
                  >
                    {createKBMutation.isPending ? 'Creating...' : 'Create KB'}
                  </button>
                </motion.div>
              )}
            </AnimatePresence>

            {/* KB List */}
            <div className="space-y-2">
              {isLoading ? (
                <div className="text-light-grey text-sm">Loading...</div>
              ) : kbs.length === 0 ? (
                <div className="text-light-grey text-sm">No knowledge bases yet</div>
              ) : (
                kbs.map((kb: KnowledgeBase) => (
                  <div
                    key={kb.name}
                    className={`p-3 rounded-lg border transition-all cursor-pointer ${
                      selectedKB === kb.name
                        ? 'bg-electric-teal/20 border-electric-teal'
                        : 'bg-cool-blue/5 border-electric-teal/20 hover:border-electric-teal/50'
                    }`}
                    onClick={() => setSelectedKB(kb.name)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="font-semibold text-white">{kb.name}</div>
                        <div className="text-xs text-light-grey">{kb.kb_type}</div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirm(`Delete "${kb.name}"?`)) {
                            deleteKBMutation.mutate(kb.name);
                          }
                        }}
                        className="p-1 rounded hover:bg-blaze-orange/20 transition-colors"
                      >
                        <Trash2 className="w-4 h-4 text-blaze-orange" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Tabs */}
          <div className="bg-deep-night border-b border-electric-teal/30 px-6 py-3 flex gap-4">
            <button
              onClick={() => setActiveTab('kb')}
              className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                activeTab === 'kb'
                  ? 'bg-electric-teal text-deep-night'
                  : 'text-light-grey hover:text-white'
              }`}
            >
              <Database className="w-4 h-4 inline mr-2" />
              KB Management
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                activeTab === 'chat'
                  ? 'bg-electric-teal text-deep-night'
                  : 'text-light-grey hover:text-white'
              }`}
              disabled={!selectedKB}
            >
              <MessageSquare className="w-4 h-4 inline mr-2" />
              Chat
            </button>
            <button
              onClick={() => setActiveTab('help')}
              className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                activeTab === 'help'
                  ? 'bg-electric-teal text-deep-night'
                  : 'text-light-grey hover:text-white'
              }`}
            >
              <HelpCircle className="w-4 h-4 inline mr-2" />
              Help
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-auto p-6">
            {activeTab === 'help' ? (
              <HelpDocs />
            ) : !selectedKB ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Database className="w-16 h-16 text-electric-teal/50 mx-auto mb-4" />
                  <h2 className="text-2xl font-bold text-light-grey mb-2">No Knowledge Base Selected</h2>
                  <p className="text-light-grey">Create or select a knowledge base to get started</p>
                </div>
              </div>
            ) : activeTab === 'kb' ? (
              <KBManagement
                kbName={selectedKB}
                kbType={kbs.find(kb => kb.name === selectedKB)?.metadata?.kb_type}
              />
            ) : (
              <ChatInterface
                kbName={selectedKB}
                useHybrid={useHybrid}
                useRerank={useRerank}
                useAgentic={useAgentic}
              />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
