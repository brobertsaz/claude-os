import { useState, useEffect } from 'react';
import { ChevronRight, ChevronLeft, FolderOpen, Home } from 'lucide-react';
import axios from 'axios';
import { motion } from 'framer-motion';

interface DirectoryPickerProps {
  onSelect: (path: string) => void;
  onClose: () => void;
  initialPath?: string;
}

interface DirectoryItem {
  name: string;
  path: string;
  is_dir: boolean;
}

interface BrowseResponse {
  current_path: string;
  parent_path: string | null;
  subdirectories: DirectoryItem[];
}

export default function DirectoryPicker({ onSelect, onClose, initialPath }: DirectoryPickerProps) {
  const [currentPath, setCurrentPath] = useState<string>('');
  const [subdirectories, setSubdirectories] = useState<DirectoryItem[]>([]);
  const [parentPath, setParentPath] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pathHistory, setPathHistory] = useState<string[]>([]);

  // Browse directory on mount - start from initialPath or home
  useEffect(() => {
    browseDirectory(initialPath || '');
  }, []);

  const browseDirectory = async (path: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get<BrowseResponse>('/api/browse-directory', {
        params: path && path.trim() ? { path } : {},
        timeout: 10000
      });

      setCurrentPath(response.data.current_path);
      setSubdirectories(response.data.subdirectories);
      setParentPath(response.data.parent_path);
    } catch (err: any) {
      console.error(`[DirectoryPicker] Full error:`, err);
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to browse directory';
      setError(errorMsg);
      setSubdirectories([]);
      console.error(`Directory browse error: ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  const handleNavigate = (path: string) => {
    setPathHistory([...pathHistory, currentPath]);
    browseDirectory(path);
  };

  const handleGoBack = () => {
    if (pathHistory.length > 0) {
      const newHistory = [...pathHistory];
      const previousPath = newHistory.pop();
      setPathHistory(newHistory);
      browseDirectory(previousPath!);
    } else if (parentPath) {
      browseDirectory(parentPath);
    }
  };

  const handleGoHome = () => {
    setPathHistory([]);
    browseDirectory('');
  };

  const handleSelect = () => {
    onSelect(currentPath);
    onClose();
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        className="bg-deep-night border border-electric-teal/30 rounded-lg w-full max-w-2xl max-h-[80vh] flex flex-col"
      >
        {/* Header */}
        <div className="border-b border-electric-teal/20 p-4">
          <h3 className="text-lg font-semibold text-electric-teal mb-2">Select Folder</h3>
          <div className="flex items-center gap-2 text-sm text-light-grey bg-cool-blue/10 p-2 rounded break-all">
            {currentPath}
          </div>
        </div>

        {/* Navigation Bar */}
        <div className="flex gap-2 px-4 pt-4 border-b border-electric-teal/10">
          <button
            onClick={handleGoHome}
            className="flex items-center gap-1 px-3 py-2 rounded bg-electric-teal/20 text-electric-teal hover:bg-electric-teal/30 transition-colors text-sm"
            title="Go to home directory"
          >
            <Home className="w-4 h-4" />
            Home
          </button>

          {pathHistory.length > 0 && (
            <button
              onClick={handleGoBack}
              className="flex items-center gap-1 px-3 py-2 rounded bg-cool-blue/20 text-cool-blue hover:bg-cool-blue/30 transition-colors text-sm"
            >
              <ChevronLeft className="w-4 h-4" />
              Back
            </button>
          )}
        </div>

        {/* Directory List */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading && (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-electric-teal"></div>
            </div>
          )}

          {error && (
            <div className="bg-red-500/20 border border-red-500/50 rounded p-3 text-red-400 text-sm">
              {error}
            </div>
          )}

          {!loading && !error && subdirectories.length === 0 && (
            <div className="text-center py-8 text-light-grey">
              <FolderOpen className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No subdirectories found</p>
            </div>
          )}

          {!loading && !error && subdirectories.length > 0 && (
            <div className="space-y-2">
              {subdirectories.map((dir) => (
                <button
                  key={dir.path}
                  onClick={() => handleNavigate(dir.path)}
                  className="w-full flex items-center gap-3 p-3 rounded bg-cool-blue/10 hover:bg-cool-blue/20 border border-cool-blue/20 hover:border-cool-blue/40 transition-all text-left group"
                >
                  <FolderOpen className="w-5 h-5 text-electric-teal flex-shrink-0" />
                  <span className="flex-1 text-light-grey group-hover:text-electric-teal transition-colors truncate">
                    {dir.name}
                  </span>
                  <ChevronRight className="w-4 h-4 text-cool-blue opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-electric-teal/20 p-4 flex gap-2 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded bg-cool-blue/20 text-cool-blue hover:bg-cool-blue/30 transition-colors text-sm font-medium"
          >
            Cancel
          </button>
          <button
            onClick={handleSelect}
            className="px-4 py-2 rounded bg-electric-teal/20 text-electric-teal hover:bg-electric-teal/30 transition-colors text-sm font-medium"
          >
            Select This Folder
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

