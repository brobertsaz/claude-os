import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Archive, CheckCircle, Clock, AlertCircle, Play, Square, RotateCcw } from 'lucide-react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8051';

interface Task {
  id: number;
  task_code: string;
  phase: string;
  title: string;
  description: string;
  status: 'todo' | 'in_progress' | 'done' | 'blocked';
  estimated_minutes: number;
  actual_minutes: number | null;
  risk_level: string;
  dependencies: string[];
  started_at: string | null;
  completed_at: string | null;
}

interface TaskGroup {
  todo: Task[];
  in_progress: Task[];
  done: Task[];
  blocked: Task[];
}

interface Spec {
  id: number;
  name: string;
  slug: string;
  folder_name: string;
  path: string;
  total_tasks: number;
  completed_tasks: number;
  status: string;
  progress: number;
  archived: boolean;
  created_at: string;
  updated_at: string;
  tasks: TaskGroup;
  task_count_by_status: {
    todo: number;
    in_progress: number;
    done: number;
    blocked: number;
  };
}

interface KanbanBoardProps {
  projectId: number;
}

export default function KanbanBoard({ projectId }: KanbanBoardProps) {
  const [includeArchived, setIncludeArchived] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [selectedSpec, setSelectedSpec] = useState<Spec | null>(null);
  const queryClient = useQueryClient();

  // Fetch Kanban data
  const { data: kanbanData, isLoading } = useQuery({
    queryKey: ['kanban', projectId, includeArchived],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/projects/${projectId}/kanban`, {
        params: { include_archived: includeArchived },
      });
      return response.data;
    },
    refetchInterval: 3000, // Refetch every 3 seconds for real-time updates
  });

  // Sync specs mutation
  const syncSpecsMutation = useMutation({
    mutationFn: async () => {
      const response = await axios.post(`${API_URL}/api/projects/${projectId}/specs/sync`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kanban', projectId] });
    },
  });

  // Archive spec mutation
  const archiveSpecMutation = useMutation({
    mutationFn: async (specId: number) => {
      const response = await axios.post(`${API_URL}/api/specs/${specId}/archive`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kanban', projectId] });
    },
  });

  // Unarchive spec mutation
  const unarchiveSpecMutation = useMutation({
    mutationFn: async (specId: number) => {
      const response = await axios.post(`${API_URL}/api/specs/${specId}/unarchive`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kanban', projectId] });
    },
  });

  // Update task status mutation
  const updateTaskStatusMutation = useMutation({
    mutationFn: async ({ taskId, status, actualMinutes }: { taskId: number; status: string; actualMinutes?: number }) => {
      const response = await axios.patch(`${API_URL}/api/tasks/${taskId}/status`, {
        status,
        actual_minutes: actualMinutes,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kanban', projectId] });
      setSelectedTask(null);
    },
  });

  const specs: Spec[] = kanbanData?.specs || [];
  const summary = kanbanData?.summary || { total_specs: 0, total_tasks: 0, completed_tasks: 0 };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'planning':
        return 'text-light-grey';
      case 'in_progress':
        return 'text-cool-blue';
      case 'completed':
        return 'text-electric-teal';
      default:
        return 'text-light-grey';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low':
        return 'bg-electric-teal/20 text-electric-teal border-electric-teal/50';
      case 'medium':
        return 'bg-cool-blue/20 text-cool-blue border-cool-blue/50';
      case 'high':
        return 'bg-blaze-orange/20 text-blaze-orange border-blaze-orange/50';
      default:
        return 'bg-light-grey/20 text-light-grey border-light-grey/50';
    }
  };

  const formatTime = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  };

  const TaskCard = ({ task, spec }: { task: Task; spec: Spec }) => (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="bg-cool-blue/10 border border-electric-teal/30 rounded-lg p-3 hover:border-electric-teal/60 transition-all cursor-pointer"
      onClick={() => {
        setSelectedTask(task);
        setSelectedSpec(spec);
      }}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="text-xs font-mono text-electric-teal">{task.task_code}</div>
        <div className={`text-xs px-2 py-0.5 rounded border ${getRiskColor(task.risk_level)}`}>
          {task.risk_level}
        </div>
      </div>
      <div className="text-sm text-white font-medium mb-2 line-clamp-2">{task.title}</div>
      <div className="flex items-center gap-2 text-xs text-light-grey">
        <Clock className="w-3 h-3" />
        {task.actual_minutes ? (
          <span>{formatTime(task.actual_minutes)} actual</span>
        ) : (
          <span>{formatTime(task.estimated_minutes)} est</span>
        )}
      </div>
      {task.dependencies.length > 0 && (
        <div className="mt-2 text-xs text-light-grey">
          Depends on: {task.dependencies.join(', ')}
        </div>
      )}
    </motion.div>
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-light-grey">Loading Kanban board...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-white mb-1">Spec Kanban Board</h2>
            <p className="text-light-grey text-sm">Track your Agent-OS spec implementation progress</p>
          </div>
          <div className="flex gap-2">
            <label className="flex items-center gap-2 px-4 py-2 bg-cool-blue/10 border border-electric-teal/30 rounded-lg cursor-pointer hover:bg-cool-blue/20 transition-colors">
              <input
                type="checkbox"
                checked={includeArchived}
                onChange={(e) => setIncludeArchived(e.target.checked)}
                className="w-4 h-4 accent-electric-teal"
              />
              <span className="text-sm text-white">Show Archived</span>
            </label>
            <button
              onClick={() => syncSpecsMutation.mutate()}
              disabled={syncSpecsMutation.isPending}
              className="btn-secondary flex items-center gap-2"
            >
              <RotateCcw className={`w-4 h-4 ${syncSpecsMutation.isPending ? 'animate-spin' : ''}`} />
              {syncSpecsMutation.isPending ? 'Syncing...' : 'Sync Specs'}
            </button>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-cool-blue/10 border border-electric-teal/30 rounded-lg p-4">
            <div className="text-sm text-light-grey mb-1">Total Specs</div>
            <div className="text-2xl font-bold text-white">{summary.total_specs}</div>
          </div>
          <div className="bg-cool-blue/10 border border-electric-teal/30 rounded-lg p-4">
            <div className="text-sm text-light-grey mb-1">Total Tasks</div>
            <div className="text-2xl font-bold text-white">{summary.total_tasks}</div>
          </div>
          <div className="bg-cool-blue/10 border border-electric-teal/30 rounded-lg p-4">
            <div className="text-sm text-light-grey mb-1">Completed</div>
            <div className="text-2xl font-bold text-electric-teal">
              {summary.completed_tasks} ({summary.total_tasks > 0 ? Math.round((summary.completed_tasks / summary.total_tasks) * 100) : 0}%)
            </div>
          </div>
        </div>
      </div>

      {/* Specs */}
      <div className="flex-1 overflow-y-auto space-y-6">
        {specs.length === 0 ? (
          <div className="text-center py-12">
            <Square className="w-16 h-16 text-electric-teal/30 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">No Specs Found</h3>
            <p className="text-light-grey mb-4">
              Create specs using Agent-OS in your project's agent-os/specs/ folder
            </p>
            <button
              onClick={() => syncSpecsMutation.mutate()}
              className="btn-primary"
            >
              Sync Specs
            </button>
          </div>
        ) : (
          specs.map((spec) => (
            <div key={spec.id} className="bg-deep-night/50 border border-electric-teal/30 rounded-lg p-6">
              {/* Spec Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-bold text-white">{spec.name}</h3>
                    {spec.archived && (
                      <span className="text-xs px-2 py-1 bg-light-grey/20 text-light-grey border border-light-grey/50 rounded">
                        ARCHIVED
                      </span>
                    )}
                    <span className={`text-sm font-semibold ${getStatusColor(spec.status)}`}>
                      {spec.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-light-grey">
                    <span>{spec.folder_name}</span>
                    <span>•</span>
                    <span>{spec.total_tasks} tasks</span>
                    <span>•</span>
                    <span className="text-electric-teal">{spec.progress}% complete</span>
                  </div>
                  {/* Progress Bar */}
                  <div className="mt-3 h-2 bg-cool-blue/20 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-electric-teal to-cool-blue transition-all duration-500"
                      style={{ width: `${spec.progress}%` }}
                    />
                  </div>
                </div>
                <button
                  onClick={() => {
                    if (spec.archived) {
                      unarchiveSpecMutation.mutate(spec.id);
                    } else {
                      if (confirm(`Archive "${spec.name}"?`)) {
                        archiveSpecMutation.mutate(spec.id);
                      }
                    }
                  }}
                  className="btn-secondary flex items-center gap-2 ml-4"
                >
                  <Archive className="w-4 h-4" />
                  {spec.archived ? 'Unarchive' : 'Archive'}
                </button>
              </div>

              {/* Task Counts */}
              <div className="grid grid-cols-4 gap-4 mb-4">
                <div className="bg-cool-blue/10 border border-electric-teal/20 rounded p-3">
                  <div className="text-xs text-light-grey mb-1">Todo</div>
                  <div className="text-xl font-bold text-white">{spec.task_count_by_status.todo}</div>
                </div>
                <div className="bg-cool-blue/20 border border-cool-blue/50 rounded p-3">
                  <div className="text-xs text-light-grey mb-1">In Progress</div>
                  <div className="text-xl font-bold text-cool-blue">{spec.task_count_by_status.in_progress}</div>
                </div>
                <div className="bg-electric-teal/20 border border-electric-teal/50 rounded p-3">
                  <div className="text-xs text-light-grey mb-1">Done</div>
                  <div className="text-xl font-bold text-electric-teal">{spec.task_count_by_status.done}</div>
                </div>
                <div className="bg-blaze-orange/20 border border-blaze-orange/50 rounded p-3">
                  <div className="text-xs text-light-grey mb-1">Blocked</div>
                  <div className="text-xl font-bold text-blaze-orange">{spec.task_count_by_status.blocked}</div>
                </div>
              </div>

              {/* Kanban Columns */}
              <div className="grid grid-cols-4 gap-4">
                {/* Todo Column */}
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-light-grey mb-2">TODO</h4>
                  <AnimatePresence>
                    {spec.tasks.todo.map((task) => (
                      <TaskCard key={task.id} task={task} spec={spec} />
                    ))}
                  </AnimatePresence>
                  {spec.tasks.todo.length === 0 && (
                    <div className="text-xs text-light-grey/50 text-center py-4">No tasks</div>
                  )}
                </div>

                {/* In Progress Column */}
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-cool-blue mb-2">IN PROGRESS</h4>
                  <AnimatePresence>
                    {spec.tasks.in_progress.map((task) => (
                      <TaskCard key={task.id} task={task} spec={spec} />
                    ))}
                  </AnimatePresence>
                  {spec.tasks.in_progress.length === 0 && (
                    <div className="text-xs text-light-grey/50 text-center py-4">No tasks</div>
                  )}
                </div>

                {/* Done Column */}
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-electric-teal mb-2">DONE</h4>
                  <AnimatePresence>
                    {spec.tasks.done.map((task) => (
                      <TaskCard key={task.id} task={task} spec={spec} />
                    ))}
                  </AnimatePresence>
                  {spec.tasks.done.length === 0 && (
                    <div className="text-xs text-light-grey/50 text-center py-4">No tasks</div>
                  )}
                </div>

                {/* Blocked Column */}
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-blaze-orange mb-2">BLOCKED</h4>
                  <AnimatePresence>
                    {spec.tasks.blocked.map((task) => (
                      <TaskCard key={task.id} task={task} spec={spec} />
                    ))}
                  </AnimatePresence>
                  {spec.tasks.blocked.length === 0 && (
                    <div className="text-xs text-light-grey/50 text-center py-4">No tasks</div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Task Detail Modal */}
      <AnimatePresence>
        {selectedTask && selectedSpec && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
            onClick={() => setSelectedTask(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-deep-night border border-electric-teal/30 rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="text-sm font-mono text-electric-teal mb-1">{selectedTask.task_code}</div>
                  <h3 className="text-2xl font-bold text-white">{selectedTask.title}</h3>
                  <div className="text-sm text-light-grey mt-1">{selectedSpec.name}</div>
                </div>
                <div className={`px-3 py-1 rounded border text-sm ${getRiskColor(selectedTask.risk_level)}`}>
                  {selectedTask.risk_level} risk
                </div>
              </div>

              <div className="space-y-4 mb-6">
                <div>
                  <div className="text-sm text-light-grey mb-1">Description</div>
                  <div className="text-white">{selectedTask.description || 'No description'}</div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-light-grey mb-1">Phase</div>
                    <div className="text-white">{selectedTask.phase}</div>
                  </div>
                  <div>
                    <div className="text-sm text-light-grey mb-1">Status</div>
                    <div className="text-white">{selectedTask.status.replace('_', ' ')}</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-light-grey mb-1">Estimated Time</div>
                    <div className="text-white">{formatTime(selectedTask.estimated_minutes)}</div>
                  </div>
                  <div>
                    <div className="text-sm text-light-grey mb-1">Actual Time</div>
                    <div className="text-white">
                      {selectedTask.actual_minutes ? formatTime(selectedTask.actual_minutes) : 'Not tracked'}
                    </div>
                  </div>
                </div>

                {selectedTask.dependencies.length > 0 && (
                  <div>
                    <div className="text-sm text-light-grey mb-1">Dependencies</div>
                    <div className="flex flex-wrap gap-2">
                      {selectedTask.dependencies.map((dep) => (
                        <span key={dep} className="text-xs px-2 py-1 bg-cool-blue/20 text-cool-blue border border-cool-blue/50 rounded">
                          {dep}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {selectedTask.started_at && (
                  <div>
                    <div className="text-sm text-light-grey mb-1">Started At</div>
                    <div className="text-white text-sm">{new Date(selectedTask.started_at).toLocaleString()}</div>
                  </div>
                )}

                {selectedTask.completed_at && (
                  <div>
                    <div className="text-sm text-light-grey mb-1">Completed At</div>
                    <div className="text-white text-sm">{new Date(selectedTask.completed_at).toLocaleString()}</div>
                  </div>
                )}
              </div>

              {/* Status Update Buttons */}
              <div className="border-t border-electric-teal/30 pt-4">
                <div className="text-sm text-light-grey mb-3">Update Status</div>
                <div className="grid grid-cols-4 gap-2">
                  <button
                    onClick={() =>
                      updateTaskStatusMutation.mutate({
                        taskId: selectedTask.id,
                        status: 'todo',
                      })
                    }
                    disabled={selectedTask.status === 'todo' || updateTaskStatusMutation.isPending}
                    className="btn-secondary text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Square className="w-4 h-4 inline mr-1" />
                    Todo
                  </button>
                  <button
                    onClick={() =>
                      updateTaskStatusMutation.mutate({
                        taskId: selectedTask.id,
                        status: 'in_progress',
                      })
                    }
                    disabled={selectedTask.status === 'in_progress' || updateTaskStatusMutation.isPending}
                    className="btn-secondary text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Play className="w-4 h-4 inline mr-1" />
                    In Progress
                  </button>
                  <button
                    onClick={() =>
                      updateTaskStatusMutation.mutate({
                        taskId: selectedTask.id,
                        status: 'done',
                        actualMinutes: selectedTask.estimated_minutes, // Default to estimated
                      })
                    }
                    disabled={selectedTask.status === 'done' || updateTaskStatusMutation.isPending}
                    className="btn-primary text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <CheckCircle className="w-4 h-4 inline mr-1" />
                    Done
                  </button>
                  <button
                    onClick={() =>
                      updateTaskStatusMutation.mutate({
                        taskId: selectedTask.id,
                        status: 'blocked',
                      })
                    }
                    disabled={selectedTask.status === 'blocked' || updateTaskStatusMutation.isPending}
                    className="btn-secondary text-sm disabled:opacity-50 disabled:cursor-not-allowed bg-blaze-orange/20 hover:bg-blaze-orange/30"
                  >
                    <AlertCircle className="w-4 h-4 inline mr-1" />
                    Blocked
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
