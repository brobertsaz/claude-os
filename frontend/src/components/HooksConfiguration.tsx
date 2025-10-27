import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Toggle, RefreshCw, FolderOpen, Check, AlertCircle } from 'lucide-react';
import axios from 'axios';
import DirectoryPicker from './DirectoryPicker';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8051';

interface HooksConfigProps {
  projectId: number;
  onClose: () => void;
}

interface HookStatus {
  enabled: boolean;
  mcp_type: string;
  folder_path: string;
  file_patterns: string[];
  created_at: string;
  last_sync: string | null;
  synced_files: Record<string, string>;
}

interface HooksStatus {
  project_id: number;
  hooks_config_path: string;
  total_hooks: number;
  enabled_hooks: number;
  hooks: Record<string, HookStatus>;
}

export default function HooksConfiguration({ projectId, onClose }: HooksConfigProps) {
  const [selectedMCP, setSelectedMCP] = useState<string | null>(null);
  const [folderPath, setFolderPath] = useState('');
  const [showEnableForm, setShowEnableForm] = useState(false);
  const [showDirectoryPicker, setShowDirectoryPicker] = useState(false);

  const queryClient = useQueryClient();

  // Fetch hooks status
  const { data: hooksStatus } = useQuery({
    queryKey: ['hooks-status', projectId],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/projects/${projectId}/hooks`);
      return response.data.status as HooksStatus;
    },
  });

  // Enable hook mutation
  const enableHookMutation = useMutation({
    mutationFn: async (data: { mcp_type: string; folder_path: string }) => {
      const response = await axios.post(
        `${API_URL}/api/projects/${projectId}/hooks/${data.mcp_type}/enable`,
        { folder_path: data.folder_path }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hooks-status', projectId] });
      setShowEnableForm(false);
      setSelectedMCP(null);
      setFolderPath('');
    },
  });

  // Disable hook mutation
  const disableHookMutation = useMutation({
    mutationFn: async (mcp_type: string) => {
      await axios.post(`${API_URL}/api/projects/${projectId}/hooks/${mcp_type}/disable`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hooks-status', projectId] });
    },
  });

  // Sync hook mutation
  const syncHookMutation = useMutation({
    mutationFn: async (mcp_type?: string) => {
      const response = await axios.post(
        `${API_URL}/api/projects/${projectId}/hooks/sync`,
        { mcp_type }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hooks-status', projectId] });
    },
  });

  const mcp_types = ['knowledge_docs', 'project_profile', 'project_index', 'project_memories'];

  const handleEnableHook = async () => {
    if (!selectedMCP || !folderPath.trim()) {
      alert('Please select an MCP type and folder path');
      return;
    }
    await enableHookMutation.mutateAsync({
      mcp_type: selectedMCP,
      folder_path: folderPath,
    });
  };

  const handleSyncAll = async () => {
    await syncHookMutation.mutateAsync();
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        className="card max-w-3xl w-full mx-4 max-h-[80vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-bold gradient-text">Hooks Configuration</h3>
          <button
            onClick={onClose}
            className="text-light-grey hover:text-electric-teal transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Sync All Button */}
        <button
          onClick={handleSyncAll}
          disabled={syncHookMutation.isPending}
          className="btn-secondary w-full flex items-center justify-center gap-2 mb-6"
        >
          <RefreshCw className={`w-4 h-4 ${syncHookMutation.isPending ? 'animate-spin' : ''}`} />
          {syncHookMutation.isPending ? 'Syncing All...' : 'Sync All Folders'}
        </button>

        {/* Enable Hook Form */}
        {showEnableForm ? (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-cool-blue/20 border border-cool-blue/50 rounded-lg p-4 mb-6"
          >
            <h4 className="font-semibold text-electric-teal mb-4">Enable New Hook</h4>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold mb-2 text-electric-teal">
                  Select MCP Type
                </label>
                <select
                  value={selectedMCP || ''}
                  onChange={(e) => setSelectedMCP(e.target.value)}
                  className="input w-full"
                >
                  <option value="">-- Choose MCP Type --</option>
                  {mcp_types
                    .filter((type) => !hooksStatus?.hooks[type]?.enabled)
                    .map((type) => (
                      <option key={type} value={type}>
                        {type.replace('_', ' ').toUpperCase()}
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2 text-electric-teal">
                  Folder Path
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={folderPath}
                    readOnly
                    placeholder="Click 'Browse' to select a folder"
                    className="input w-full bg-cool-blue/10 cursor-not-allowed"
                  />
                  <button
                    onClick={() => setShowDirectoryPicker(true)}
                    className="btn-secondary px-4 whitespace-nowrap hover:bg-blaze-orange/80 transition-colors"
                  >
                    Browse
                  </button>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setShowEnableForm(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={handleEnableHook}
                  disabled={enableHookMutation.isPending}
                  className="btn-primary flex-1"
                >
                  {enableHookMutation.isPending ? 'Enabling...' : 'Enable Hook'}
                </button>
              </div>
            </div>
          </motion.div>
        ) : (
          <button
            onClick={() => setShowEnableForm(true)}
            className="btn-secondary w-full mb-6"
          >
            + Add New Hook
          </button>
        )}

        {/* Hooks List */}
        <div className="space-y-4">
          {hooksStatus?.hooks && Object.keys(hooksStatus.hooks).length > 0 ? (
            Object.entries(hooksStatus.hooks).map(([mcp_type, hook]) => (
              <HookCard
                key={mcp_type}
                mcp_type={mcp_type}
                hook={hook}
                projectId={projectId}
                onDisable={() => disableHookMutation.mutate(mcp_type)}
                onSync={() => syncHookMutation.mutateAsync(mcp_type)}
                isDisabling={disableHookMutation.isPending}
                isSyncing={syncHookMutation.isPending}
              />
            ))
          ) : (
            <div className="text-center py-8">
              <FolderOpen className="w-12 h-12 text-electric-teal/50 mx-auto mb-2" />
              <p className="text-light-grey">No hooks configured yet</p>
            </div>
          )}
        </div>

        {/* Directory Picker Modal */}
        <AnimatePresence>
          {showDirectoryPicker && (
            <DirectoryPicker
              initialPath={folderPath || ''}
              onSelect={(path) => {
                setFolderPath(path);
                setShowDirectoryPicker(false);
              }}
              onClose={() => setShowDirectoryPicker(false)}
            />
          )}
        </AnimatePresence>
      </motion.div>
    </motion.div>
  );
}

interface HookCardProps {
  mcp_type: string;
  hook: HookStatus;
  projectId: number;
  onDisable: () => void;
  onSync: () => void;
  isDisabling: boolean;
  isSyncing: boolean;
}

function HookCard({
  mcp_type,
  hook,
  projectId,
  onDisable,
  onSync,
  isDisabling,
  isSyncing,
}: HookCardProps) {
  return (
    <motion.div
      layout
      className="bg-deep-night/50 border border-electric-teal/30 rounded-lg p-4 hover:border-electric-teal/60 transition-colors"
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-lg font-bold text-electric-teal">
              {mcp_type.replace('_', ' ').toUpperCase()}
            </h4>
            {hook.enabled ? (
              <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded flex items-center gap-1">
                <Check className="w-3 h-3" />
                Enabled
              </span>
            ) : (
              <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 text-xs rounded flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                Disabled
              </span>
            )}
          </div>
          <p className="text-sm text-light-grey break-all">{hook.folder_path}</p>
        </div>

        <div className="flex gap-2">
          {hook.enabled && (
            <button
              onClick={onSync}
              disabled={isSyncing}
              title="Sync this folder"
              className="p-2 hover:bg-electric-teal/20 rounded transition-colors text-electric-teal"
            >
              <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
            </button>
          )}
          <button
            onClick={() => {
              if (confirm(`${hook.enabled ? 'Disable' : 'Enable'} hook for ${mcp_type}?`)) {
                onDisable();
              }
            }}
            disabled={isDisabling}
            className="px-3 py-2 bg-blaze-orange/20 hover:bg-blaze-orange/30 text-blaze-orange rounded transition-colors text-sm font-semibold"
          >
            {hook.enabled ? 'Disable' : 'Enable'}
          </button>
        </div>
      </div>

      {/* Hook Details */}
      <div className="grid grid-cols-2 gap-2 text-xs text-light-grey">
        <div>
          <span className="text-cool-blue">Files Synced:</span> {Object.keys(hook.synced_files).length}
        </div>
        <div>
          <span className="text-cool-blue">Last Sync:</span> {hook.last_sync ? new Date(hook.last_sync).toLocaleString() : 'Never'}
        </div>
        <div className="col-span-2">
          <span className="text-cool-blue">Patterns:</span> {hook.file_patterns?.join(', ') || 'All files'}
        </div>
      </div>

      {/* Recent Files */}
      {Object.keys(hook.synced_files).length > 0 && (
        <div className="mt-3 pt-3 border-t border-electric-teal/20">
          <p className="text-xs text-cool-blue font-semibold mb-2">Recent Files:</p>
          <div className="space-y-1">
            {Object.keys(hook.synced_files)
              .slice(0, 3)
              .map((filename) => (
                <p key={filename} className="text-xs text-light-grey truncate">
                  ✓ {filename}
                </p>
              ))}
            {Object.keys(hook.synced_files).length > 3 && (
              <p className="text-xs text-cool-blue">
                +{Object.keys(hook.synced_files).length - 3} more files
              </p>
            )}
          </div>
        </div>
      )}
    </motion.div>
  );
}
