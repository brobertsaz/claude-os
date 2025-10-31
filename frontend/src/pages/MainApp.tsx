import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Home, Settings, Database, MessageSquare, Plus, Trash2, FolderOpen, Zap, Edit } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import ChatInterface from '../components/ChatInterface';
import KBManagement from '../components/KBManagement';
import ProjectSetup from '../components/ProjectSetup';
import DirectoryPicker from '../components/DirectoryPicker';

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

interface ProjectMCP {
  mcp_type: string;
  kb_id: number;
  kb_name: string;
  kb_slug: string;
}

export default function MainApp() {
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [selectedMCP, setSelectedMCP] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'mcps' | 'chat'>('overview');
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [showProjectSetup, setShowProjectSetup] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectPath, setNewProjectPath] = useState('/Users/iamanmp/Projects');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [showPathPicker, setShowPathPicker] = useState(false);

  // RAG settings
  const [useHybrid, setUseHybrid] = useState(false);
  const [useRerank, setUseRerank] = useState(false);
  const [useAgentic, setUseAgentic] = useState(false);

  const queryClient = useQueryClient();

  // Fetch projects
  const { data: projects = [], isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const response = await axios.get('/api/projects');
      return response.data.projects as Project[];
    },
  });

  // Fetch MCPs for selected project
  const { data: projectMCPsData, isLoading: mcpsLoading } = useQuery({
    queryKey: ['project-mcps', selectedProject?.id],
    queryFn: async () => {
      if (!selectedProject) return [];
      try {
        const response = await axios.get(`/api/projects/${selectedProject.id}/mcps`);
        console.log('[MainApp] Project MCPs response:', response.data);
        return Array.isArray(response.data.mcps) ? response.data.mcps : [];
      } catch (error) {
        console.error('[MainApp] Failed to fetch project MCPs:', error);
        return [];
      }
    },
    enabled: !!selectedProject,
  });

  const projectMCPs = Array.isArray(projectMCPsData) ? projectMCPsData : [];

  // Create project mutation
  const createProjectMutation = useMutation({
    mutationFn: async () => {
      const response = await axios.post('/api/projects', {
        name: newProjectName,
        path: newProjectPath,
        description: newProjectDesc,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setShowCreateProject(false);
      setNewProjectName('');
      setNewProjectPath('/Users/iamanmp/Projects');
      setNewProjectDesc('');
    },
  });

  // Delete project mutation
  const deleteProjectMutation = useMutation({
    mutationFn: async (projectId: number) => {
      await axios.delete(`/api/projects/${projectId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      if (selectedProject) {
        setSelectedProject(null);
      }
    },
  });

  const handleCreateProject = () => {
    if (newProjectName.trim() && newProjectPath.trim()) {
      createProjectMutation.mutate();
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top Navigation */}
      <nav className="bg-deep-night border-b border-electric-teal/30 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <img src="/assets/claude-os-logo.png" alt="Claude OS" className="h-10" />
            <h1 className="text-2xl font-bold gradient-text">CLAUDE OS</h1>
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
        {/* Left Sidebar - Projects */}
        <aside className="w-80 bg-gradient-to-b from-deep-night to-cool-blue/5 border-r border-electric-teal/30 p-6 overflow-y-auto">
          {/* Projects Header */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-electric-teal flex items-center gap-2">
                <FolderOpen className="w-5 h-5" />
                Projects
              </h2>
              <button
                onClick={() => setShowCreateProject(true)}
                className="p-1 rounded hover:bg-electric-teal/20 transition-colors"
                title="Create New Project"
              >
                <Plus className="w-5 h-5 text-electric-teal" />
              </button>
            </div>

            {/* Projects List */}
            <div className="space-y-2">
              {projectsLoading ? (
                <div className="text-light-grey text-sm text-center py-4">Loading...</div>
              ) : projects.length === 0 ? (
                <div className="text-light-grey text-sm text-center py-8">
                  <FolderOpen className="w-12 h-12 mx-auto mb-2 opacity-30" />
                  <p>No projects yet</p>
                  <p className="text-xs mt-1">Click + to create one</p>
                </div>
              ) : (
                projects.map((project: Project) => (
                  <div
                    key={project.id}
                    className={`p-3 rounded-lg border transition-all cursor-pointer ${
                      selectedProject?.id === project.id
                        ? 'bg-electric-teal/20 border-electric-teal'
                        : 'bg-cool-blue/5 border-electric-teal/20 hover:border-electric-teal/50'
                    }`}
                    onClick={() => {
                      setSelectedProject(project);
                      setActiveTab('overview');
                      setSelectedMCP(null);
                    }}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-white truncate">{project.name}</div>
                        <div className="text-xs text-light-grey truncate">{project.path}</div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirm(`Delete project "${project.name}"?`)) {
                            deleteProjectMutation.mutate(project.id);
                          }
                        }}
                        className="p-1 rounded hover:bg-blaze-orange/20 transition-colors flex-shrink-0"
                      >
                        <Trash2 className="w-4 h-4 text-blaze-orange" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Selected Project MCPs */}
          {selectedProject && projectMCPs.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-bold text-electric-teal mb-3 flex items-center gap-2">
                <Zap className="w-4 h-4" />
                Project MCPs
              </h3>
              <div className="space-y-1">
                {projectMCPs.map((mcp: ProjectMCP) => (
                  <div
                    key={mcp.mcp_type}
                    className={`p-2 rounded border text-sm transition-all cursor-pointer ${
                      selectedMCP === mcp.kb_name
                        ? 'bg-cool-blue/30 border-cool-blue'
                        : 'bg-cool-blue/10 border-cool-blue/20 hover:border-cool-blue/50'
                    }`}
                    onClick={() => {
                      setSelectedMCP(mcp.kb_name);
                      setActiveTab('mcps');
                    }}
                  >
                    <div className="font-medium text-white">{mcp.mcp_type}</div>
                    <div className="text-xs text-light-grey truncate">{mcp.kb_name}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* RAG Settings */}
          {selectedProject && (
            <div>
              <h3 className="text-sm font-bold text-electric-teal mb-3 flex items-center gap-2">
                <Settings className="w-4 h-4" />
                RAG Settings
              </h3>
              <div className="space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useHybrid}
                    onChange={(e) => setUseHybrid(e.target.checked)}
                    className="w-4 h-4 accent-electric-teal"
                  />
                  <span className="text-xs text-light-grey">Hybrid Search</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useRerank}
                    onChange={(e) => setUseRerank(e.target.checked)}
                    className="w-4 h-4 accent-electric-teal"
                  />
                  <span className="text-xs text-light-grey">Reranking</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useAgentic}
                    onChange={(e) => setUseAgentic(e.target.checked)}
                    className="w-4 h-4 accent-electric-teal"
                  />
                  <span className="text-xs text-light-grey">Agentic RAG</span>
                </label>
              </div>
            </div>
          )}
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {!selectedProject ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <FolderOpen className="w-24 h-24 mx-auto mb-4 text-electric-teal/30" />
                <h2 className="text-2xl font-bold text-white mb-2">No Project Selected</h2>
                <p className="text-light-grey mb-6">Select a project from the sidebar or create a new one</p>
                <button
                  onClick={() => setShowCreateProject(true)}
                  className="btn-primary"
                >
                  <Plus className="w-4 h-4 inline mr-2" />
                  Create Project
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Tabs */}
              <div className="bg-deep-night border-b border-electric-teal/30 px-6 py-3 flex gap-4">
                <button
                  onClick={() => setActiveTab('overview')}
                  className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                    activeTab === 'overview'
                      ? 'bg-electric-teal text-deep-night'
                      : 'text-light-grey hover:text-white'
                  }`}
                >
                  <FolderOpen className="w-4 h-4 inline mr-2" />
                  Overview
                </button>
                <button
                  onClick={() => setActiveTab('mcps')}
                  className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                    activeTab === 'mcps'
                      ? 'bg-electric-teal text-deep-night'
                      : 'text-light-grey hover:text-white'
                  }`}
                >
                  <Database className="w-4 h-4 inline mr-2" />
                  MCP Management
                </button>
                <button
                  onClick={() => setActiveTab('chat')}
                  className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                    activeTab === 'chat'
                      ? 'bg-electric-teal text-deep-night'
                      : 'text-light-grey hover:text-white'
                  }`}
                  disabled={!selectedMCP}
                >
                  <MessageSquare className="w-4 h-4 inline mr-2" />
                  Chat
                </button>
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-auto p-6">
                {activeTab === 'overview' ? (
                  mcpsLoading ? (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center">
                        <div className="text-light-grey">Loading project details...</div>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div className="max-w-4xl">
                        <div className="flex items-start justify-between mb-6">
                          <div>
                            <h2 className="text-3xl font-bold text-white mb-2">{selectedProject.name}</h2>
                            <p className="text-light-grey">{selectedProject.description || 'No description'}</p>
                          </div>
                          <button
                            onClick={() => setShowProjectSetup(true)}
                            className="btn-secondary flex items-center gap-2"
                          >
                            <Edit className="w-4 h-4" />
                            Configure
                          </button>
                        </div>

                        <div className="grid grid-cols-3 gap-4 mb-6">
                          <div className="bg-cool-blue/10 border border-electric-teal/30 rounded-lg p-4">
                            <div className="text-sm text-light-grey mb-1">Database ID</div>
                            <div className="text-white font-mono text-sm">#{selectedProject.id}</div>
                          </div>
                          <div className="bg-cool-blue/10 border border-electric-teal/30 rounded-lg p-4">
                            <div className="text-sm text-light-grey mb-1">Project Path</div>
                            <div className="text-white font-mono text-sm">{selectedProject.path}</div>
                          </div>
                          <div className="bg-cool-blue/10 border border-electric-teal/30 rounded-lg p-4">
                            <div className="text-sm text-light-grey mb-1">MCPs Configured</div>
                            <div className="text-white text-2xl font-bold">{projectMCPs.length} / 5</div>
                          </div>
                        </div>

                        <div className="bg-cool-blue/10 border border-electric-teal/30 rounded-lg p-6">
                          <h3 className="text-lg font-bold text-electric-teal mb-4">Project MCPs</h3>
                          <div className="grid grid-cols-2 gap-4">
                            {['knowledge_docs', 'project_profile', 'project_index', 'project_memories', 'code_structure'].map((type) => {
                              const mcp = projectMCPs.find((m: ProjectMCP) => m.mcp_type === type);
                              return (
                                <div
                                  key={type}
                                  className={`p-4 rounded-lg border ${
                                    mcp
                                      ? 'bg-electric-teal/10 border-electric-teal/50'
                                      : 'bg-deep-night/50 border-electric-teal/20'
                                  }`}
                                >
                                  <div className="font-semibold text-white mb-1">{type}</div>
                                  {mcp ? (
                                    <div className="text-xs text-light-grey">{mcp.kb_name}</div>
                                  ) : (
                                    <div className="text-xs text-blaze-orange">Not configured</div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                ) : activeTab === 'mcps' ? (
                  selectedMCP ? (
                    <KBManagement
                      kbName={selectedMCP}
                      kbSlug={projectMCPs.find((m: ProjectMCP) => m.kb_name === selectedMCP)?.kb_slug}
                      kbType={projectMCPs.find((m: ProjectMCP) => m.kb_name === selectedMCP)?.mcp_type}
                      projectId={selectedProject?.id}
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center">
                        <Database className="w-16 h-16 text-electric-teal/50 mx-auto mb-4" />
                        <h2 className="text-2xl font-bold text-light-grey mb-2">No MCP Selected</h2>
                        <p className="text-light-grey">Select an MCP from the sidebar to manage it</p>
                      </div>
                    </div>
                  )
                ) : (
                  selectedMCP ? (
                    <ChatInterface
                      kbName={selectedMCP}
                      useHybrid={useHybrid}
                      useRerank={useRerank}
                      useAgentic={useAgentic}
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center">
                        <MessageSquare className="w-16 h-16 text-electric-teal/50 mx-auto mb-4" />
                        <h2 className="text-2xl font-bold text-light-grey mb-2">No MCP Selected</h2>
                        <p className="text-light-grey">Select an MCP from the sidebar to chat with it</p>
                      </div>
                    </div>
                  )
                )}
              </div>
            </>
          )}
        </main>
      </div>

      {/* Create Project Modal */}
      <AnimatePresence>
        {showCreateProject && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
            onClick={() => setShowCreateProject(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-deep-night border border-electric-teal/30 rounded-lg p-6 max-w-md w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="text-2xl font-bold text-white mb-4">Create New Project</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-light-grey mb-2">Project Name</label>
                  <input
                    type="text"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    placeholder="My Awesome Project"
                    className="input w-full"
                    autoFocus
                  />
                </div>

                <div>
                  <label className="block text-sm text-light-grey mb-2">Project Path</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newProjectPath}
                      readOnly
                      className="input flex-1 bg-cool-blue/10 cursor-not-allowed"
                    />
                    <button
                      onClick={() => setShowPathPicker(true)}
                      className="btn-secondary px-4 whitespace-nowrap hover:bg-blaze-orange/80 transition-colors"
                    >
                      Browse
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm text-light-grey mb-2">Description (optional)</label>
                  <textarea
                    value={newProjectDesc}
                    onChange={(e) => setNewProjectDesc(e.target.value)}
                    placeholder="What is this project about?"
                    className="input w-full h-24 resize-none"
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    onClick={() => setShowCreateProject(false)}
                    className="btn-secondary flex-1"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateProject}
                    disabled={!newProjectName.trim() || !newProjectPath.trim() || createProjectMutation.isPending}
                    className="btn-primary flex-1"
                  >
                    {createProjectMutation.isPending ? 'Creating...' : 'Create Project'}
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Directory Picker Modal */}
      <AnimatePresence>
        {showPathPicker && (
          <DirectoryPicker
            initialPath={newProjectPath || ''}
            onSelect={(path) => {
              setNewProjectPath(path);
              setShowPathPicker(false);
            }}
            onClose={() => setShowPathPicker(false)}
          />
        )}
      </AnimatePresence>

      {/* Project Setup Modal */}
      <AnimatePresence>
        {showProjectSetup && selectedProject && (
          <ProjectSetup
            projectId={selectedProject.id}
            onClose={() => {
              setShowProjectSetup(false);
              queryClient.invalidateQueries({ queryKey: ['project-mcps', selectedProject.id] });
            }}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
