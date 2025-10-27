import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FolderOpen, Check, X, ChevronRight } from 'lucide-react';
import { getCommonProjectPaths, formatPathForDisplay } from '../lib/filePicker';

interface DirectoryPickerModalProps {
  isOpen: boolean;
  onSelect: (path: string) => void;
  onCancel: () => void;
}

export default function DirectoryPickerModal({
  isOpen,
  onSelect,
  onCancel,
}: DirectoryPickerModalProps) {
  const [customPath, setCustomPath] = useState('');
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const commonPaths = getCommonProjectPaths();

  useEffect(() => {
    setCustomPath('');
    setSelectedPath(null);
  }, [isOpen]);

  const handleSelectCommonPath = (path: string) => {
    setSelectedPath(path);
    setCustomPath(path);
  };

  const handleConfirm = () => {
    const pathToUse = customPath.trim();
    if (pathToUse) {
      onSelect(pathToUse);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={onCancel}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
            className="card max-w-2xl w-full mx-4"
          >
            <div className="flex items-center gap-2 mb-6">
              <FolderOpen className="w-6 h-6 text-electric-teal" />
              <h3 className="text-2xl font-bold gradient-text">Select Project Directory</h3>
            </div>

            <p className="text-light-grey mb-4">
              Choose a common location or enter a custom path below:
            </p>

            {/* Common Paths */}
            <div className="mb-6 space-y-2">
              {commonPaths.map((path) => (
                <button
                  key={path}
                  onClick={() => handleSelectCommonPath(path)}
                  className={`w-full flex items-center justify-between p-3 rounded-lg border transition-all ${
                    selectedPath === path
                      ? 'bg-electric-teal/20 border-electric-teal/50 text-electric-teal'
                      : 'bg-cool-blue/10 border-cool-blue/30 hover:border-electric-teal/50 text-light-grey'
                  }`}
                >
                  <div className="flex items-center gap-3 flex-1">
                    <FolderOpen className="w-4 h-4" />
                    <div className="text-left">
                      <div className="font-semibold">{path.split('/').pop()}</div>
                      <div className="text-xs opacity-75">{formatPathForDisplay(path)}</div>
                    </div>
                  </div>
                  {selectedPath === path && <Check className="w-5 h-5" />}
                </button>
              ))}
            </div>

            {/* Custom Path Input */}
            <div className="mb-6">
              <label className="block text-sm font-semibold mb-2 text-electric-teal">
                Or enter a custom path:
              </label>
              <input
                type="text"
                value={customPath}
                onChange={(e) => {
                  setCustomPath(e.target.value);
                  setSelectedPath(null);
                }}
                placeholder="/Users/me/projects/my-project"
                className="input w-full"
                autoFocus
              />
              {customPath && (
                <p className="text-xs text-light-grey mt-2">
                  {formatPathForDisplay(customPath)}
                </p>
              )}
            </div>

            {/* Buttons */}
            <div className="flex gap-3">
              <button onClick={onCancel} className="btn-secondary flex-1 flex items-center justify-center gap-2">
                <X className="w-4 h-4" />
                Cancel
              </button>
              <button
                onClick={handleConfirm}
                disabled={!customPath.trim()}
                className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Check className="w-4 h-4" />
                Select Directory
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
