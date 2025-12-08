import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Activity,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  Loader2,
  FileSearch,
  Database,
  Trash2
} from 'lucide-react';
import axios from 'axios';

interface IndexingJob {
  job_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  progress: number;
  message: string;
  started_at: number | string | null;
  completed_at: number | string | null;
  error: string | null;
  kb_name?: string;
  type?: string;
  project_path?: string;
}

interface JobsResponse {
  jobs: IndexingJob[];
  count: number;
}

const STATUS_CONFIG = {
  queued: {
    bg: 'bg-yellow-500/20',
    border: 'border-yellow-500',
    text: 'text-yellow-400',
    icon: Clock,
    label: 'Queued'
  },
  running: {
    bg: 'bg-electric-teal/20',
    border: 'border-electric-teal',
    text: 'text-electric-teal',
    icon: Loader2,
    label: 'Running'
  },
  completed: {
    bg: 'bg-green-500/20',
    border: 'border-green-500',
    text: 'text-green-400',
    icon: CheckCircle2,
    label: 'Completed'
  },
  failed: {
    bg: 'bg-red-500/20',
    border: 'border-red-500',
    text: 'text-red-400',
    icon: XCircle,
    label: 'Failed'
  }
};

function formatTime(timestamp: number | string | null): string {
  if (!timestamp) return '-';
  try {
    // Handle Unix timestamp (seconds) or ISO string
    const ts = typeof timestamp === 'number' ? timestamp * 1000 : new Date(timestamp).getTime();
    return new Date(ts).toLocaleString();
  } catch {
    return String(timestamp);
  }
}

function formatDuration(startedAt: number | string | null, completedAt: number | string | null): string {
  if (!startedAt) return '-';

  // Handle Unix timestamp (seconds) or ISO string
  const start = typeof startedAt === 'number' ? startedAt * 1000 : new Date(startedAt).getTime();
  const end = completedAt
    ? (typeof completedAt === 'number' ? completedAt * 1000 : new Date(completedAt).getTime())
    : Date.now();
  const durationMs = end - start;

  if (durationMs < 1000) return `${durationMs}ms`;
  if (durationMs < 60000) return `${(durationMs / 1000).toFixed(1)}s`;
  if (durationMs < 3600000) return `${Math.floor(durationMs / 60000)}m ${Math.floor((durationMs % 60000) / 1000)}s`;
  return `${Math.floor(durationMs / 3600000)}h ${Math.floor((durationMs % 3600000) / 60000)}m`;
}

function extractKbName(jobId: string): string {
  // Job IDs are formatted as "semantic-{kb_name}-{uuid}"
  const match = jobId.match(/^semantic-(.+)-[a-f0-9-]+$/);
  return match ? match[1] : jobId;
}

export default function JobsDashboard() {
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch jobs list
  const { data: jobsData, isLoading, refetch } = useQuery<JobsResponse>({
    queryKey: ['indexing-jobs'],
    queryFn: async () => {
      const response = await axios.get('/api/jobs');
      return response.data;
    },
    refetchInterval: autoRefresh ? 2000 : false, // Refresh every 2 seconds when enabled
  });

  const jobs = jobsData?.jobs || [];

  // Count jobs by status
  const runningJobs = jobs.filter(j => j.status === 'running').length;
  const queuedJobs = jobs.filter(j => j.status === 'queued').length;
  const completedJobs = jobs.filter(j => j.status === 'completed').length;
  const failedJobs = jobs.filter(j => j.status === 'failed').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold gradient-text flex items-center gap-2">
            <FileSearch className="w-6 h-6" />
            Indexing Jobs
          </h2>
          <p className="text-light-grey text-sm mt-1">
            Monitor semantic indexing operations in real-time
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Auto-refresh toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
              autoRefresh
                ? 'bg-electric-teal/20 text-electric-teal border border-electric-teal/50'
                : 'bg-cool-blue/10 text-light-grey border border-electric-teal/20'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            <span className="text-sm font-medium">
              {autoRefresh ? 'Live' : 'Paused'}
            </span>
          </button>

          {/* Manual refresh */}
          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-cool-blue/10 border border-electric-teal/30 rounded-lg p-4"
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-light-grey text-sm">Running</div>
              <div className="text-3xl font-bold text-electric-teal mt-1">{runningJobs}</div>
            </div>
            <Loader2 className={`w-8 h-8 text-electric-teal opacity-50 ${runningJobs > 0 ? 'animate-spin' : ''}`} />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-cool-blue/10 border border-electric-teal/30 rounded-lg p-4"
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-light-grey text-sm">Queued</div>
              <div className="text-3xl font-bold text-yellow-400 mt-1">{queuedJobs}</div>
            </div>
            <Clock className="w-8 h-8 text-yellow-400 opacity-50" />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-cool-blue/10 border border-electric-teal/30 rounded-lg p-4"
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-light-grey text-sm">Completed</div>
              <div className="text-3xl font-bold text-green-400 mt-1">{completedJobs}</div>
            </div>
            <CheckCircle2 className="w-8 h-8 text-green-400 opacity-50" />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-cool-blue/10 border border-electric-teal/30 rounded-lg p-4"
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-light-grey text-sm">Failed</div>
              <div className="text-3xl font-bold text-red-400 mt-1">{failedJobs}</div>
            </div>
            <XCircle className="w-8 h-8 text-red-400 opacity-50" />
          </div>
        </motion.div>
      </div>

      {/* Jobs List */}
      <div className="space-y-4">
        {isLoading && jobs.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-electric-teal animate-spin" />
            <span className="ml-3 text-light-grey">Loading jobs...</span>
          </div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-12">
            <Database className="w-16 h-16 text-electric-teal/30 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-light-grey mb-2">No Indexing Jobs</h3>
            <p className="text-light-grey text-sm">
              Jobs will appear here when you run semantic indexing on a knowledge base
            </p>
          </div>
        ) : (
          jobs.map((job, index) => {
            const config = STATUS_CONFIG[job.status] || STATUS_CONFIG.queued;
            const StatusIcon = config.icon;
            const kbName = job.kb_name || extractKbName(job.job_id);

            return (
              <motion.div
                key={job.job_id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`bg-cool-blue/10 border-2 rounded-lg p-5 ${config.border}/30`}
              >
                {/* Job Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${config.bg}`}>
                      <StatusIcon className={`w-5 h-5 ${config.text} ${job.status === 'running' ? 'animate-spin' : ''}`} />
                    </div>
                    <div>
                      <h3 className="font-bold text-white">{kbName}</h3>
                      <p className="text-xs text-light-grey font-mono">{job.job_id}</p>
                    </div>
                  </div>

                  {/* Status Badge */}
                  <div className={`flex items-center gap-1 px-3 py-1 rounded-full ${config.bg} border ${config.border}`}>
                    <StatusIcon className={`w-3 h-3 ${config.text} ${job.status === 'running' ? 'animate-spin' : ''}`} />
                    <span className={`text-sm font-medium ${config.text}`}>
                      {config.label}
                    </span>
                  </div>
                </div>

                {/* Progress Bar (only for running/completed jobs) */}
                {(job.status === 'running' || job.status === 'completed') && (
                  <div className="mb-4">
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-light-grey">Progress</span>
                      <span className={`font-bold ${config.text}`}>{job.progress}%</span>
                    </div>
                    <div className="h-3 bg-deep-night rounded-full overflow-hidden border border-electric-teal/20">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${job.progress}%` }}
                        transition={{ duration: 0.5, ease: 'easeOut' }}
                        className={`h-full ${job.status === 'completed' ? 'bg-green-500' : 'bg-gradient-to-r from-electric-teal to-cool-blue'}`}
                      />
                    </div>
                  </div>
                )}

                {/* Message */}
                {job.message && (
                  <div className="mb-4 p-3 bg-deep-night/50 rounded-lg border border-electric-teal/10">
                    <p className="text-sm text-light-grey">{job.message}</p>
                  </div>
                )}

                {/* Error */}
                {job.error && (
                  <div className="mb-4 p-3 bg-red-500/10 rounded-lg border border-red-500/30">
                    <div className="flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-red-400">{job.error}</p>
                    </div>
                  </div>
                )}

                {/* Timestamps */}
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-light-grey block">Started</span>
                    <span className="text-white font-mono text-xs">{formatTime(job.started_at)}</span>
                  </div>
                  <div>
                    <span className="text-light-grey block">Completed</span>
                    <span className="text-white font-mono text-xs">{formatTime(job.completed_at)}</span>
                  </div>
                  <div>
                    <span className="text-light-grey block">Duration</span>
                    <span className={`font-mono text-xs ${config.text}`}>
                      {formatDuration(job.started_at, job.completed_at)}
                    </span>
                  </div>
                </div>
              </motion.div>
            );
          })
        )}
      </div>

      {/* Help Text */}
      <div className="bg-cool-blue/10 border border-electric-teal/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-electric-teal flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-white mb-1">About Indexing Jobs</h4>
            <p className="text-sm text-light-grey">
              Semantic indexing creates vector embeddings for your documents, enabling AI-powered semantic search.
              Jobs run in the background so the server stays responsive. Progress updates every few seconds.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
