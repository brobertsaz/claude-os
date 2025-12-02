import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Trash2, Settings, FolderOpen, Zap, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';
import axios from 'axios';
import ProjectSetup from './ProjectSetup';
import DirectoryPicker from './DirectoryPicker';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8051';

interface Project {
  id: number;
  name: string;
  path: string;
  description: string;
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
}

interface ProjectMCPs {
  knowledge_docs: number;
  project_profile: number;
  project_index: number;
  project_memories: number;
}

interface ProjectFolders {
  [key: string]: string;
}

export default function ProjectManagement() {
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [showProjectSetup, setShowProjectSetup] = useState<number | null>(null);
  const [selectedProjectForSetup, setSelectedProjectForSetup] = useState<any>(null);
  const [projectName, setProjectName] = useState('');
  const [projectPath, setProjectPath] = useState('');
  const [projectDesc, setProjectDesc] = useState('');
  const [createError, setCreateError] = useState<string | null>(null);
  const [showPathPicker, setShowPathPicker] = useState(false);

  const queryClient = useQueryClient();

  // Fetch projects
  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/projects`);
      return response.data.projects as Project[];
    },
  });

  // Create project mutation
  const createProjectMutation = useMutation({
    mutationFn: async (data: { name: string; path: string; description: string }) => {
      const response = await axios.post(`${API_URL}/api/projects`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setShowCreateProject(false);
      setProjectName('');
      setProjectPath('');
      setProjectDesc('');
      setCreateError(null);
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to create project';
      setCreateError(errorMessage);
    },
  });

  // Delete project mutation
  const deleteProjectMutation = useMutation({
    mutationFn: async (projectId: number) => {
      await axios.delete(`${API_URL}/api/projects/${projectId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  const handleCreateProject = async () => {
    setCreateError(null);

    if (!projectName.trim() || !projectPath.trim()) {
      setCreateError('Project name and path are required');
      return;
    }

    await createProjectMutation.mutateAsync({
      name: projectName,
      path: projectPath,
      description: projectDesc,
    });
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-3xl font-bold gradient-text mb-2">Projects</h2>
          <p className="text-light-grey">Manage your Claude OS projects with 4-MCP architecture</p>
        </div>
        <button
          onClick={() => setShowCreateProject(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          New Project
        </button>
      </div>

      {/* Create Project Modal */}
      <AnimatePresence>
        {showCreateProject && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowCreateProject(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="card max-w-2xl w-full mx-4"
            >
              <h3 className="text-2xl font-bold mb-6 gradient-text">Create New Project</h3>

              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-semibold mb-2 text-electric-teal">
                    Project Name
                  </label>
                  <input
                    type="text"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    placeholder="e.g., my-awesome-project"
                    className="input w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2 text-electric-teal">
                    Project Path
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={projectPath}
                      readOnly
                      placeholder="e.g., /Users/me/Projects/my-project"
                      className="input flex-1 bg-cool-blue/10 cursor-not-allowed"
                    />
                    <button
                      onClick={() => setShowPathPicker(true)}
                      className="btn-secondary px-4 whitespace-nowrap hover:bg-blaze-orange/80 transition-colors"
                    >
                      Browse
                    </button>
                  </div>
                  <p className="text-xs text-light-grey mt-2">
                    Enter the full path to your project directory
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2 text-electric-teal">
                    Description (Optional)
                  </label>
                  <textarea
                    value={projectDesc}
                    onChange={(e) => setProjectDesc(e.target.value)}
                    placeholder="Describe your project..."
                    className="input w-full h-24 resize-none"
                  />
                </div>
              </div>

              {createError && (
                <div className="bg-rose-500/10 border border-rose-500/50 rounded-lg p-4 mb-6 flex gap-3">
                  <AlertCircle className="w-5 h-5 text-rose-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-semibold text-rose-500">Error</p>
                    <p className="text-sm text-light-grey mt-1">{createError}</p>
                  </div>
                </div>
              )}

              <div className="bg-cool-blue/20 border border-cool-blue/50 rounded-lg p-4 mb-6">
                <p className="text-sm text-light-grey">
                  ✨ This will automatically create 4 required MCPs:
                </p>
                <ul className="text-sm text-light-grey mt-2 space-y-1">
                  <li>📚 knowledge_docs - Documentation KB</li>
                  <li>📋 project_profile - Project analysis</li>
                  <li>🗂️ project_index - Project structure</li>
                  <li>💾 project_memories - Persistent memory</li>
                </ul>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowCreateProject(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateProject}
                  disabled={createProjectMutation.isPending}
                  className="btn-primary flex-1"
                >
                  {createProjectMutation.isPending ? 'Creating...' : 'Create Project'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Directory Picker Modal */}
      <AnimatePresence>
        {showPathPicker && (
          <DirectoryPicker
            initialPath={projectPath || ''}
            onSelect={(path) => {
              setProjectPath(path);
              setShowPathPicker(false);
            }}
            onClose={() => setShowPathPicker(false)}
          />
        )}
      </AnimatePresence>

      {/* Projects List */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin">
            <div className="w-8 h-8 border-4 border-electric-teal/30 border-t-electric-teal rounded-full" />
          </div>
        </div>
      ) : projects.length === 0 ? (
        <div className="card text-center py-12">
          <FolderOpen className="w-12 h-12 text-electric-teal/50 mx-auto mb-4" />
          <p className="text-light-grey mb-4">No projects yet</p>
          <button
            onClick={() => setShowCreateProject(true)}
            className="btn-primary inline-flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Create Your First Project
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onSetup={() => {
                setSelectedProjectForSetup(project);
                setShowProjectSetup(project.id);
              }}
              onDelete={() => deleteProjectMutation.mutate(project.id)}
              isDeleting={deleteProjectMutation.isPending}
            />
          ))}
        </div>
      )}

      {/* Project Setup Modal */}
      <AnimatePresence>
        {showProjectSetup && selectedProjectForSetup && (
          <ProjectSetup
            projectId={selectedProjectForSetup.id}
            projectName={selectedProjectForSetup.name}
            projectPath={selectedProjectForSetup.path}
            onClose={() => setShowProjectSetup(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

interface ProjectCardProps {
  project: Project;
  onSetup: () => void;
  onDelete: () => void;
  isDeleting: boolean;
}

function ProjectCard({
  project,
  onSetup,
  onDelete,
  isDeleting,
}: ProjectCardProps) {
  return (
    <motion.div
      layout
      className="card hover:border-electric-teal/50 transition-colors"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-xl font-bold text-white">{project.name}</h3>
            <span className="text-xs px-2 py-1 bg-electric-teal/20 text-electric-teal rounded">
              {new Date(project.created_at).toLocaleDateString()}
            </span>
          </div>
          <p className="text-sm text-light-grey mb-2">{project.path}</p>
          {project.description && (
            <p className="text-sm text-cool-blue mb-2">{project.description}</p>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSetup();
            }}
            className="p-2 hover:bg-electric-teal/20 rounded transition-colors"
            title="Setup project"
          >
            <Settings className="w-5 h-5 text-electric-teal" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              if (confirm(`Delete project "${project.name}"?`)) {
                onDelete();
              }
            }}
            disabled={isDeleting}
            className="p-2 hover:bg-blaze-orange/20 rounded transition-colors text-blaze-orange"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>
    </motion.div>
  );
}
