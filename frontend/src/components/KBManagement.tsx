import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { FileText, BarChart3, Clock, Database, Upload, CheckCircle, XCircle } from 'lucide-react';
import { getKBStats, listDocuments, uploadDocument, type KBStats } from '../lib/api';

interface KBManagementProps {
  kbName: string;
}

export default function KBManagement({ kbName }: KBManagementProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState('');
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

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDocument(kbName, file),
    onSuccess: (data) => {
      setUploadStatus('success');
      setUploadMessage(`✅ Uploaded ${data.filename} (${data.chunks} chunks)`);
      queryClient.invalidateQueries({ queryKey: ['kb-stats', kbName] });
      queryClient.invalidateQueries({ queryKey: ['kb-documents', kbName] });
      setTimeout(() => {
        setUploadStatus('idle');
        setSelectedFiles([]);
      }, 3000);
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

    setUploadStatus('uploading');
    for (const file of selectedFiles) {
      await uploadMutation.mutateAsync(file);
    }
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
          <div className={`mt-4 p-3 rounded-lg ${
            uploadStatus === 'success' ? 'bg-electric-teal/20 border border-electric-teal/50' :
            uploadStatus === 'error' ? 'bg-blaze-orange/20 border border-blaze-orange/50' :
            'bg-cool-blue/20 border border-cool-blue/50'
          }`}>
            <p className="text-sm">{uploadMessage || 'Processing...'}</p>
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
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {documents.map((doc: any, idx: number) => (
              <div
                key={idx}
                className="p-4 bg-cool-blue/5 border border-electric-teal/20 rounded-lg hover:border-electric-teal/50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="font-semibold text-white mb-1">
                      {doc.metadata?.source || `Document ${idx + 1}`}
                    </div>
                    <div className="text-sm text-light-grey line-clamp-2">
                      {doc.content?.substring(0, 150)}...
                    </div>
                  </div>
                  <FileText className="w-5 h-5 text-electric-teal flex-shrink-0 ml-4" />
                </div>
              </div>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  );
}
