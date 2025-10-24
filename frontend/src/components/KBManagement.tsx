import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { FileText, BarChart3, Clock, Database, Upload, CheckCircle, XCircle, Info } from 'lucide-react';
import { getKBStats, listDocuments, uploadDocument, type KBStats } from '../lib/api';

interface KBManagementProps {
  kbName: string;
  kbType?: string;
}

export default function KBManagement({ kbName, kbType }: KBManagementProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState('');
  const [uploadProgress, setUploadProgress] = useState({ current: 0, total: 0 });
  const [isBatchUpload, setIsBatchUpload] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  // Fetch KB stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['kb-stats', kbName],
    queryFn: () => getKBStats(kbName),
    enabled: !!kbName,
  });

  // Fetch documents
  const { data: documents = [], isLoading: docsLoading } = useQuery({
    queryKey: ['kb-documents', kbName],
    queryFn: () => listDocuments(kbName),
    enabled: !!kbName,
  });

  // Upload mutation - only handle individual file callbacks when NOT in batch mode
  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDocument(kbName, file),
    onSuccess: (data) => {
      // Only handle success UI for single file uploads
      if (!isBatchUpload) {
        setUploadStatus('success');
        setUploadMessage(`✅ Uploaded ${data.filename} (${data.chunks} chunks)`);
        queryClient.invalidateQueries({ queryKey: ['kb-stats', kbName] });
        queryClient.invalidateQueries({ queryKey: ['kb-documents', kbName] });
        setTimeout(() => {
          setUploadStatus('idle');
          setSelectedFiles([]);
        }, 3000);
      }
      // For batch uploads, just invalidate queries silently
      else {
        queryClient.invalidateQueries({ queryKey: ['kb-stats', kbName] });
        queryClient.invalidateQueries({ queryKey: ['kb-documents', kbName] });
      }
    },
    onError: (error: any) => {
      setUploadStatus('error');
      setUploadMessage(`❌ Upload failed: ${error.response?.data?.detail || error.message}`);
      setTimeout(() => setUploadStatus('idle'), 5000);
    },
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    // Enable batch mode to prevent individual file callbacks from interfering
    setIsBatchUpload(true);
    setUploadStatus('uploading');
    setUploadProgress({ current: 0, total: selectedFiles.length });

    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      setUploadProgress({ current: i + 1, total: selectedFiles.length });
      setUploadMessage(`📤 Uploading ${file.name} (${i + 1}/${selectedFiles.length})...`);

      try {
        await uploadMutation.mutateAsync(file);
      } catch (error) {
        // Error is handled by mutation's onError
        console.error(`Failed to upload ${file.name}:`, error);
      }
    }

    // Batch upload complete - show final success message
    setIsBatchUpload(false);
    setUploadStatus('success');
    setUploadMessage(`✅ Successfully uploaded ${selectedFiles.length} file(s)!`);
    setTimeout(() => {
      setUploadStatus('idle');
      setSelectedFiles([]);
      setUploadProgress({ current: 0, total: 0 });
    }, 3000);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      setSelectedFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card"
        >
          <div className="flex items-center gap-4">
            <div className="p-3 bg-electric-teal/20 rounded-lg">
              <FileText className="w-8 h-8 text-electric-teal" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">
                {statsLoading ? '...' : stats?.total_documents || 0}
              </div>
              <div className="text-sm text-light-grey">Documents</div>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card"
        >
          <div className="flex items-center gap-4">
            <div className="p-3 bg-cool-blue/20 rounded-lg">
              <Database className="w-8 h-8 text-cool-blue" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">
                {statsLoading ? '...' : stats?.total_chunks || 0}
              </div>
              <div className="text-sm text-light-grey">Chunks</div>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card"
        >
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blaze-orange/20 rounded-lg">
              <Clock className="w-8 h-8 text-blaze-orange" />
            </div>
            <div>
              <div className="text-sm font-semibold text-white">Last Updated</div>
              <div className="text-xs text-light-grey">
                {statsLoading
                  ? '...'
                  : stats?.last_updated
                  ? new Date(stats.last_updated).toLocaleDateString()
                  : 'Never'}
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Document Upload Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card"
      >
        <h2 className="text-xl font-bold text-electric-teal mb-4 flex items-center gap-2">
          <Upload className="w-5 h-5" />
          Upload Documents
        </h2>

        {/* Agent OS Help Text */}
        {kbType === 'AGENT_OS' && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-cool-blue/20 border border-cool-blue/50 rounded-lg"
          >
            <div className="flex gap-3">
              <Info className="w-5 h-5 text-cool-blue flex-shrink-0 mt-0.5" />
              <div className="text-sm text-light-grey">
                <p className="font-semibold text-white mb-2">🤖 Agent OS Knowledge Base</p>
                <p className="mb-3">For best results, upload these file types in order:</p>
                <div className="space-y-2 text-xs">
                  <div className="flex gap-2">
                    <span className="text-electric-teal font-bold">1️⃣ CRITICAL</span>
                    <span>product/mission.md, product/tech-stack.md, standards/global/*</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-electric-teal font-bold">2️⃣ DOMAIN</span>
                    <span>standards/backend/* or standards/frontend/* (based on your needs)</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-electric-teal font-bold">3️⃣ EXAMPLES</span>
                    <span>specs/* files for real implementation examples</span>
                  </div>
                </div>
                <p className="mt-3 text-light-grey/70 italic">
                  See UPLOAD_CHECKLIST.md in your repo for the complete prioritized file list
                </p>
              </div>
            </div>
          </motion.div>
        )}

        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-electric-teal/30 rounded-lg p-12 text-center hover:border-electric-teal/60 transition-colors cursor-pointer"
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFileSelect}
            className="hidden"
            accept=".txt,.md,.pdf,.py,.js,.ts,.tsx,.jsx,.json,.yaml,.yml,.html,.css,.cpp,.c,.h,.java,.go,.rs,.rb,.php,.sh,.sql"
          />

          {selectedFiles.length === 0 ? (
            <>
              <FileText className="w-12 h-12 text-electric-teal/50 mx-auto mb-4" />
              <p className="text-light-grey mb-2">Drag & drop files here, or click to browse</p>
              <p className="text-sm text-light-grey/60">Supports: .txt, .md, .pdf, .py, .js, .ts, and more</p>
            </>
          ) : (
            <>
              <CheckCircle className="w-12 h-12 text-electric-teal mx-auto mb-4" />
              <p className="text-white mb-2">{selectedFiles.length} file(s) selected</p>
              <div className="text-sm text-light-grey space-y-1">
                {selectedFiles.map((file, idx) => (
                  <div key={idx}>{file.name}</div>
                ))}
              </div>
            </>
          )}
        </div>

        {selectedFiles.length > 0 && (
          <div className="mt-4 flex gap-2">
            <button
              onClick={handleUpload}
              disabled={uploadStatus === 'uploading'}
              className="btn-primary flex-1"
            >
              {uploadStatus === 'uploading' ? 'Uploading...' : 'Upload Files'}
            </button>
            <button
              onClick={() => setSelectedFiles([])}
              className="btn-secondary"
            >
              Clear
            </button>
          </div>
        )}

        {uploadStatus !== 'idle' && (
          <div className={`mt-4 p-4 rounded-lg ${
            uploadStatus === 'success' ? 'bg-electric-teal/20 border border-electric-teal/50' :
            uploadStatus === 'error' ? 'bg-blaze-orange/20 border border-blaze-orange/50' :
            'bg-cool-blue/20 border border-cool-blue/50'
          }`}>
            <p className="text-sm mb-2">{uploadMessage || 'Processing...'}</p>

            {uploadStatus === 'uploading' && uploadProgress.total > 0 && (
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-light-grey">
                  <span>Progress: {uploadProgress.current} / {uploadProgress.total}</span>
                  <span>{Math.round((uploadProgress.current / uploadProgress.total) * 100)}%</span>
                </div>
                <div className="w-full bg-deep-night/50 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-full bg-electric-teal transition-all duration-300 ease-out"
                    style={{ width: `${(uploadProgress.current / uploadProgress.total) * 100}%` }}
                  />
                </div>
                <p className="text-xs text-light-grey/70 italic">
                  ⏳ Generating embeddings and storing in database... This may take a while for large files.
                </p>
              </div>
            )}
          </div>
        )}
      </motion.div>

      {/* Documents List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card"
      >
        <h2 className="text-xl font-bold text-electric-teal mb-4 flex items-center gap-2">
          <Database className="w-5 h-5" />
          Documents ({documents.length})
        </h2>

        {docsLoading ? (
          <div className="text-center py-8 text-light-grey">Loading documents...</div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8 text-light-grey">
            No documents yet. Upload some to get started!
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 max-h-96 overflow-y-auto pr-2">
            {documents.map((doc: any, idx: number) => {
              // Icon map based on file type
              const iconMap: Record<string, string> = {
                '.py': '🐍', '.js': '📜', '.jsx': '⚛️',
                '.ts': '📘', '.tsx': '⚛️', '.md': '📄',
                '.pdf': '📕', '.json': '📋', '.yaml': '⚙️',
                '.yml': '⚙️', '.txt': '📝', '.go': '🔷',
                '.rs': '🦀', '.java': '☕', '.cpp': '⚙️',
                '.c': '⚙️', '.h': '📋'
              };
              const icon = iconMap[doc.file_type?.toLowerCase()] || '📄';

              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: idx * 0.05 }}
                  className="p-5 bg-gradient-to-br from-cool-blue/10 to-electric-teal/5 border-2 border-electric-teal/30 rounded-xl hover:border-electric-teal/60 hover:shadow-xl hover:shadow-electric-teal/20 hover:-translate-y-1 transition-all duration-300"
                >
                  <div className="text-center">
                    {/* Large emoji icon */}
                    <div className="text-4xl mb-3">{icon}</div>

                    {/* Filename */}
                    <h3 className="font-bold text-white mb-3 truncate" title={doc.filename}>
                      {doc.filename || `Document ${idx + 1}`}
                    </h3>

                    {/* Tags */}
                    {doc.tags && doc.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 justify-center mb-3">
                        {doc.tags.map((tag: string, tagIdx: number) => (
                          <span
                            key={tagIdx}
                            className="px-2 py-1 bg-electric-teal/20 text-electric-teal border border-electric-teal/40 text-xs font-bold rounded-md"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Date and chunk count */}
                    <div className="text-xs text-light-grey/70 space-y-1">
                      {doc.formatted_date && (
                        <div>{doc.formatted_date}</div>
                      )}
                      <div className="font-bold text-electric-teal text-sm">
                        {doc.chunk_count || 0} chunks
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </motion.div>
    </div>
  );
}
