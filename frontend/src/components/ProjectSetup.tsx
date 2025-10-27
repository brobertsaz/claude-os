import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Settings,
  FolderOpen,
  Zap,
  BarChart3,
  MessageSquare,
  Copy,
  Check,
  ChevronRight,
  AlertCircle,
  Loader,
} from 'lucide-react';
import axios from 'axios';
import DirectoryPicker from './DirectoryPicker';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8051';

interface ProjectSetupProps {
  projectId: number;
  projectName: string;
  projectPath: string;
  onClose: () => void;
}

interface MCPInfo {
  kb_id: number;
  kb_name: string;
}

interface ProjectMCPs {
  [key: string]: MCPInfo;
}

type TabType = 'mcps' | 'folders' | 'hooks' | 'stats' | 'chat';

export default function ProjectSetup({
  projectId,
  projectName,
  projectPath,
  onClose,
}: ProjectSetupProps) {
  const [activeTab, setActiveTab] = useState<TabType>('mcps');
  const [copiedMcp, setCopiedMcp] = useState<string | null>(null);
  const [selectedFolders, setSelectedFolders] = useState<Record<string, string>>({});
  const [hooksEnabled, setHooksEnabled] = useState<Record<string, boolean>>({});

  const queryClient = useQueryClient();

  // Fetch project MCP details
  const { data: mcpsData, isLoading: mcpsLoading } = useQuery({
    queryKey: ['project-mcps', projectId],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/projects/${projectId}/mcps`);
      return response.data.mcps as ProjectMCPs;
    },
  });

  // Fetch project details
  const { data: projectDetails } = useQuery({
    queryKey: ['project-details', projectId],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/projects/${projectId}`);
      return response.data;
    },
  });

  const handleCopyCommand = (mcp_type: string, kb_name: string) => {
    const command = `--mcps=${mcp_type}:${kb_name}`;
    navigator.clipboard.writeText(command);
    setCopiedMcp(mcp_type);
    setTimeout(() => setCopiedMcp(null), 2000);
  };

  const handleSetFolder = (mcp_type: string, path: string) => {
    setSelectedFolders({
      ...selectedFolders,
      [mcp_type]: path,
    });
  };

  const handleToggleHook = (mcp_type: string) => {
    setHooksEnabled({
      ...hooksEnabled,
      [mcp_type]: !hooksEnabled[mcp_type],
    });
  };

  const tabs: Array<{ id: TabType; label: string; icon: React.ReactNode }> = [
    { id: 'mcps', label: 'MCP Commands', icon: <Zap className="w-4 h-4" /> },
    { id: 'folders', label: 'Folders', icon: <FolderOpen className="w-4 h-4" /> },
    { id: 'hooks', label: 'Auto-Sync', icon: <Settings className="w-4 h-4" /> },
    { id: 'stats', label: 'Statistics', icon: <BarChart3 className="w-4 h-4" /> },
    { id: 'chat', label: 'Chat', icon: <MessageSquare className="w-4 h-4" /> },
  ];

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50 p-4 bg-dark-navy">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="card w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-electric-teal/20">
          <div>
            <h2 className="text-2xl font-bold gradient-text">{projectName}</h2>
            <p className="text-sm text-light-grey mt-1">{projectPath}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-electric-teal/20 rounded transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-6 pt-6 border-b border-electric-teal/10 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-t transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-electric-teal/20 text-electric-teal border-b-2 border-electric-teal'
                  : 'text-light-grey hover:text-electric-teal border-b-2 border-transparent'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <AnimatePresence mode="wait">
            {activeTab === 'mcps' && (
              <MCPsTab mcpsData={mcpsData} mcpsLoading={mcpsLoading} onCopy={handleCopyCommand} copiedMcp={copiedMcp} />
            )}
            {activeTab === 'folders' && (
              <FoldersTab mcpsData={mcpsData} selectedFolders={selectedFolders} onSetFolder={handleSetFolder} />
            )}
            {activeTab === 'hooks' && (
              <HooksTab
                mcpsData={mcpsData}
                hooksEnabled={hooksEnabled}
                onToggle={handleToggleHook}
                selectedFolders={selectedFolders}
              />
            )}
            {activeTab === 'stats' && <StatsTab projectId={projectId} />}
            {activeTab === 'chat' && <ChatTab projectId={projectId} projectName={projectName} mcpsData={mcpsData} />}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}

// MCP Commands Tab
function MCPsTab({ mcpsData, mcpsLoading, onCopy, copiedMcp }: any) {
  if (mcpsLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader className="w-8 h-8 animate-spin text-electric-teal" />
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
      <div className="bg-cool-blue/10 border border-cool-blue/30 rounded-lg p-4 mb-6">
        <p className="text-sm text-light-grey">
          Copy any of these commands to reference a project MCP when working with Claude OS:
        </p>
      </div>

      <div className="space-y-3">
        {mcpsData &&
          Object.entries(mcpsData).map(([mcp_type, mcp_info]: [string, any]) => (
            <motion.div
              key={mcp_type}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-deep-night/50 border border-cool-blue/30 rounded-lg p-4"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-electric-teal uppercase">{mcp_type.replace('_', ' ')}</h4>
                  <p className="text-xs text-light-grey mt-1">KB: {mcp_info.kb_name}</p>
                  <p className="text-xs text-light-grey">ID: {mcp_info.kb_id}</p>
                  <div className="mt-3 bg-dark-navy/50 rounded p-2">
                    <code className="text-xs text-cool-blue font-mono">--mcps={mcp_type}:{mcp_info.kb_name}</code>
                  </div>
                </div>
                <button
                  onClick={() => onCopy(mcp_type, mcp_info.kb_name)}
                  className={`px-3 py-2 rounded text-xs font-medium transition-all ml-4 ${
                    copiedMcp === mcp_type
                      ? 'bg-green-500/20 text-green-400 flex items-center gap-1'
                      : 'bg-electric-teal/20 text-electric-teal hover:bg-electric-teal/30'
                  }`}
                >
                  {copiedMcp === mcp_type ? (
                    <>
                      <Check className="w-4 h-4" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4" />
                      Copy
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          ))}
      </div>
    </motion.div>
  );
}

// Folders Configuration Tab
function FoldersTab({ mcpsData, selectedFolders, onSetFolder }: any) {
  const [pickerOpen, setPickerOpen] = useState<string | null>(null);

  const handlePickerSelect = (mcp_type: string, path: string) => {
    onSetFolder(mcp_type, path);
    setPickerOpen(null);
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
      <div className="bg-cool-blue/10 border border-cool-blue/30 rounded-lg p-4 mb-6">
        <p className="text-sm text-light-grey">
          Select folders for each MCP to automatically sync files into the knowledge base:
        </p>
      </div>

      <div className="space-y-4">
        {mcpsData &&
          Object.entries(mcpsData).map(([mcp_type, mcp_info]: [string, any]) => (
            <div key={mcp_type} className="bg-deep-night/50 border border-cool-blue/30 rounded-lg p-4">
              <label className="block text-sm font-semibold text-electric-teal mb-3">
                {mcp_type.replace('_', ' ')}
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={selectedFolders[mcp_type] || ''}
                  readOnly
                  placeholder="Click 'Browse' to select a folder"
                  className="input flex-1 bg-cool-blue/10 cursor-not-allowed"
                />
                <button
                  onClick={() => setPickerOpen(mcp_type)}
                  className="btn-secondary px-4 whitespace-nowrap hover:bg-blaze-orange/80 transition-colors"
                >
                  Browse
                </button>
              </div>
              {selectedFolders[mcp_type] && (
                <p className="text-xs text-green-400 mt-2">✓ Folder set: {selectedFolders[mcp_type]}</p>
              )}
            </div>
          ))}
      </div>

      {/* Directory Picker Modal */}
      <AnimatePresence>
        {pickerOpen && (
          <DirectoryPicker
            initialPath={selectedFolders[pickerOpen] || ''}
            onSelect={(path) => handlePickerSelect(pickerOpen, path)}
            onClose={() => setPickerOpen(null)}
          />
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// Hooks Configuration Tab
function HooksTab({ mcpsData, hooksEnabled, onToggle, selectedFolders }: any) {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
      <div className="bg-cool-blue/10 border border-cool-blue/30 rounded-lg p-4 mb-6">
        <p className="text-sm text-light-grey">
          Enable auto-sync to automatically index files when they change in the selected folder:
        </p>
      </div>

      <div className="space-y-4">
        {mcpsData &&
          Object.entries(mcpsData).map(([mcp_type, mcp_info]: [string, any]) => {
            const isConfigured = selectedFolders[mcp_type];
            return (
              <div
                key={mcp_type}
                className={`border rounded-lg p-4 transition-all ${
                  isConfigured ? 'bg-deep-night/50 border-cool-blue/30' : 'bg-deep-night/20 border-cool-blue/10'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-semibold text-electric-teal block mb-1">
                      {mcp_type.replace('_', ' ')}
                    </label>
                    {!isConfigured && <p className="text-xs text-cool-blue">Set a folder first</p>}
                    {isConfigured && (
                      <p className="text-xs text-light-grey">Watching: {selectedFolders[mcp_type]}</p>
                    )}
                  </div>
                  <button
                    onClick={() => onToggle(mcp_type)}
                    disabled={!isConfigured}
                    className={`relative w-12 h-6 rounded-full transition-all ${
                      hooksEnabled[mcp_type] ? 'bg-green-500/30' : 'bg-cool-blue/20'
                    } ${!isConfigured && 'opacity-50 cursor-not-allowed'}`}
                  >
                    <motion.div
                      animate={{ x: hooksEnabled[mcp_type] ? 24 : 2 }}
                      className="absolute top-1 left-1 w-4 h-4 bg-white rounded-full"
                    />
                  </button>
                </div>
              </div>
            );
          })}
      </div>
    </motion.div>
  );
}

// Statistics Tab
function StatsTab({ projectId }: any) {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {['Documents', 'Chunks', 'Size', 'Last Updated'].map((stat) => (
          <div key={stat} className="bg-deep-night/50 border border-cool-blue/30 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-electric-teal">-</p>
            <p className="text-xs text-light-grey mt-2">{stat}</p>
          </div>
        ))}
      </div>

      <div className="space-y-4 mt-6">
        <h3 className="text-sm font-semibold text-electric-teal">MCP Statistics</h3>
        {['knowledge_docs', 'project_profile', 'project_index', 'project_memories'].map((mcp) => (
          <div key={mcp} className="bg-deep-night/50 border border-cool-blue/30 rounded-lg p-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-light-grey">{mcp.replace('_', ' ')}</span>
              <span className="text-sm font-semibold text-electric-teal">0 documents</span>
            </div>
            <div className="w-full bg-cool-blue/10 rounded h-2 mt-2">
              <div className="bg-electric-teal h-2 rounded" style={{ width: '0%' }}></div>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

// Chat Tab
function ChatTab({ projectId, projectName, mcpsData }: any) {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([
    { role: 'assistant', content: `Welcome to ${projectName}! Ask me anything about your project.` },
  ]);

  const handleSendMessage = () => {
    if (!message.trim()) return;

    setMessages([...messages, { role: 'user', content: message }]);
    setMessage('');

    // TODO: Connect to actual chat API
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'I understand your question. This feature will soon be connected to your project MCPs!',
        },
      ]);
    }, 500);
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full flex flex-col">
      <div className="flex-1 space-y-4 mb-4 min-h-[300px]">
        {messages.map((msg, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`rounded-lg px-4 py-2 max-w-xs lg:max-w-md ${
                msg.role === 'user'
                  ? 'bg-electric-teal/30 text-electric-teal'
                  : 'bg-cool-blue/30 text-light-grey'
              }`}
            >
              <p className="text-sm">{msg.content}</p>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          placeholder="Ask about your project..."
          className="input flex-1"
        />
        <button onClick={handleSendMessage} className="btn-primary px-6">
          Send
        </button>
      </div>
    </motion.div>
  );
}
