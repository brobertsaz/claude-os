import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  Plus,
  Trash2,
  Eye,
  Download,
  ChevronDown,
  ChevronRight,
  Globe,
  FolderOpen,
  Tag,
  Search,
  X,
  Check,
  ExternalLink,
  Github,
  RefreshCw
} from 'lucide-react';
import axios from 'axios';

interface Skill {
  name: string;
  path: string;
  description: string;
  scope: 'global' | 'project';
  source: string;
  content: string;
  enabled: boolean;
  category: string | null;
  tags: string[];
  created: string;
  modified: string;
}

interface SkillTemplate {
  name: string;
  category: string;
  description: string;
  path: string;
  tags: string[];
  version: string;
}

interface CommunitySkill {
  name: string;
  source: string;
  repo: string;
  path: string;
  description: string;
  readme_url: string;
  raw_url: string;
}

interface CommunitySource {
  repo: string;
  skills_path: string;
  name: string;
  description: string;
}

interface SkillsManagementProps {
  projectPath: string;
}

export default function SkillsManagement({ projectPath }: SkillsManagementProps) {
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);
  const [showTemplates, setShowTemplates] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['general', 'rails', 'react', 'testing']));
  const [searchQuery, setSearchQuery] = useState('');

  // Community skills state
  const [templateTab, setTemplateTab] = useState<'local' | 'community'>('local');
  const [selectedCommunitySource, setSelectedCommunitySource] = useState<string>('all');

  // Create skill form state
  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillDescription, setNewSkillDescription] = useState('');
  const [newSkillContent, setNewSkillContent] = useState('');
  const [newSkillCategory, setNewSkillCategory] = useState('');
  const [newSkillTags, setNewSkillTags] = useState('');

  const queryClient = useQueryClient();

  // Fetch installed skills
  const { data: skillsData, isLoading: skillsLoading } = useQuery({
    queryKey: ['skills', projectPath],
    queryFn: async () => {
      const response = await axios.get('/api/skills', {
        params: { project_path: projectPath, include_content: false }
      });
      return response.data;
    },
  });

  // Fetch skill templates
  const { data: templatesData, isLoading: templatesLoading } = useQuery({
    queryKey: ['skill-templates'],
    queryFn: async () => {
      const response = await axios.get('/api/skills/templates');
      return response.data;
    },
  });

  // Fetch community sources
  const { data: communitySourcesData } = useQuery({
    queryKey: ['community-sources'],
    queryFn: async () => {
      const response = await axios.get('/api/skills/community/sources');
      return response.data;
    },
  });

  // Fetch community skills
  const { data: communitySkillsData, isLoading: communityLoading, refetch: refetchCommunity } = useQuery({
    queryKey: ['community-skills', selectedCommunitySource],
    queryFn: async () => {
      const params: { source?: string } = {};
      if (selectedCommunitySource !== 'all') {
        params.source = selectedCommunitySource;
      }
      const response = await axios.get('/api/skills/community', { params });
      return response.data;
    },
    enabled: showTemplates && templateTab === 'community',
  });

  // Install template mutation
  const installTemplateMutation = useMutation({
    mutationFn: async (templateName: string) => {
      const response = await axios.post('/api/skills/install', {
        template_name: templateName,
      }, {
        params: { project_path: projectPath }
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills', projectPath] });
      setShowTemplates(false);
    },
  });

  // Install community skill mutation
  const installCommunityMutation = useMutation({
    mutationFn: async (skill: CommunitySkill) => {
      const response = await axios.post('/api/skills/community/install', {
        skill_name: skill.name,
        source: skill.source,
      }, {
        params: { project_path: projectPath }
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills', projectPath] });
    },
  });

  // Create skill mutation
  const createSkillMutation = useMutation({
    mutationFn: async () => {
      const response = await axios.post('/api/skills', {
        name: newSkillName,
        description: newSkillDescription,
        content: newSkillContent,
        category: newSkillCategory || null,
        tags: newSkillTags ? newSkillTags.split(',').map(t => t.trim()) : [],
      }, {
        params: { project_path: projectPath }
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills', projectPath] });
      setShowCreateModal(false);
      resetCreateForm();
    },
  });

  // Delete skill mutation
  const deleteSkillMutation = useMutation({
    mutationFn: async (skillName: string) => {
      await axios.delete(`/api/skills/${skillName}`, {
        params: { project_path: projectPath }
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills', projectPath] });
      setSelectedSkill(null);
    },
  });

  // Get skill details
  const { data: skillDetails, isLoading: detailsLoading } = useQuery({
    queryKey: ['skill-details', selectedSkill?.name, selectedSkill?.scope],
    queryFn: async () => {
      if (!selectedSkill) return null;
      const response = await axios.get(`/api/skills/${selectedSkill.scope}/${selectedSkill.name}`, {
        params: { project_path: projectPath }
      });
      return response.data;
    },
    enabled: !!selectedSkill,
  });

  const resetCreateForm = () => {
    setNewSkillName('');
    setNewSkillDescription('');
    setNewSkillContent('');
    setNewSkillCategory('');
    setNewSkillTags('');
  };

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const globalSkills: Skill[] = skillsData?.global || [];
  const projectSkills: Skill[] = skillsData?.project || [];
  const templates: SkillTemplate[] = templatesData?.templates || [];
  const categories: string[] = templatesData?.categories || [];
  const communitySources: Record<string, CommunitySource> = communitySourcesData?.sources || {};
  const communitySkills: CommunitySkill[] = communitySkillsData?.skills || [];

  // Filter templates by search
  const filteredTemplates = templates.filter(t =>
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  // Group templates by category
  const templatesByCategory = categories.reduce((acc, cat) => {
    acc[cat] = filteredTemplates.filter(t => t.category === cat);
    return acc;
  }, {} as Record<string, SkillTemplate[]>);

  // Filter community skills by search
  const filteredCommunitySkills = communitySkills.filter(s =>
    s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Group community skills by source
  const communityBySource = filteredCommunitySkills.reduce((acc, skill) => {
    if (!acc[skill.source]) {
      acc[skill.source] = [];
    }
    acc[skill.source].push(skill);
    return acc;
  }, {} as Record<string, CommunitySkill[]>);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-electric-teal" />
            Skills Management
          </h2>
          <p className="text-light-grey text-sm mt-1">
            Manage Claude Code skills for this project
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowTemplates(true)}
            className="btn-secondary flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Install Template
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Create Skill
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex gap-6 min-h-0">
        {/* Skills List */}
        <div className="w-80 flex flex-col">
          {/* Global Skills */}
          <div className="mb-4">
            <h3 className="text-sm font-bold text-electric-teal mb-2 flex items-center gap-2">
              <Globe className="w-4 h-4" />
              Global Skills ({globalSkills.length})
            </h3>
            <div className="space-y-1">
              {skillsLoading ? (
                <div className="text-light-grey text-sm py-2">Loading...</div>
              ) : globalSkills.length === 0 ? (
                <div className="text-light-grey text-sm py-2">No global skills</div>
              ) : (
                globalSkills.map((skill) => (
                  <div
                    key={`global-${skill.name}`}
                    onClick={() => setSelectedSkill(skill)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedSkill?.name === skill.name && selectedSkill?.scope === 'global'
                        ? 'bg-electric-teal/20 border-electric-teal'
                        : 'bg-cool-blue/10 border-electric-teal/20 hover:border-electric-teal/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-medium text-white">{skill.name}</div>
                      <span className="text-xs bg-cool-blue/30 text-light-grey px-2 py-0.5 rounded">
                        {skill.source}
                      </span>
                    </div>
                    {skill.description && (
                      <div className="text-xs text-light-grey mt-1 line-clamp-2">
                        {skill.description}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Project Skills */}
          <div className="flex-1 min-h-0">
            <h3 className="text-sm font-bold text-electric-teal mb-2 flex items-center gap-2">
              <FolderOpen className="w-4 h-4" />
              Project Skills ({projectSkills.length})
            </h3>
            <div className="space-y-1 overflow-y-auto max-h-[400px]">
              {skillsLoading ? (
                <div className="text-light-grey text-sm py-2">Loading...</div>
              ) : projectSkills.length === 0 ? (
                <div className="text-center py-8">
                  <Sparkles className="w-12 h-12 mx-auto mb-2 text-electric-teal/30" />
                  <p className="text-light-grey text-sm">No project skills yet</p>
                  <p className="text-light-grey text-xs mt-1">
                    Install a template or create a custom skill
                  </p>
                </div>
              ) : (
                projectSkills.map((skill) => (
                  <div
                    key={`project-${skill.name}`}
                    onClick={() => setSelectedSkill(skill)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedSkill?.name === skill.name && selectedSkill?.scope === 'project'
                        ? 'bg-electric-teal/20 border-electric-teal'
                        : 'bg-cool-blue/10 border-electric-teal/20 hover:border-electric-teal/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-medium text-white">{skill.name}</div>
                      <span className="text-xs bg-blaze-orange/20 text-blaze-orange px-2 py-0.5 rounded">
                        {skill.source}
                      </span>
                    </div>
                    {skill.description && (
                      <div className="text-xs text-light-grey mt-1 line-clamp-2">
                        {skill.description}
                      </div>
                    )}
                    {skill.tags && skill.tags.length > 0 && (
                      <div className="flex gap-1 mt-2 flex-wrap">
                        {skill.tags.slice(0, 3).map(tag => (
                          <span key={tag} className="text-xs bg-cool-blue/20 text-light-grey px-1.5 py-0.5 rounded">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Skill Details */}
        <div className="flex-1 bg-cool-blue/10 border border-electric-teal/30 rounded-lg p-6 overflow-auto">
          {selectedSkill ? (
            detailsLoading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-light-grey">Loading skill details...</div>
              </div>
            ) : skillDetails ? (
              <div>
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-white">{skillDetails.name}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        skillDetails.scope === 'global'
                          ? 'bg-cool-blue/30 text-light-grey'
                          : 'bg-blaze-orange/20 text-blaze-orange'
                      }`}>
                        {skillDetails.scope}
                      </span>
                      <span className="text-xs bg-electric-teal/20 text-electric-teal px-2 py-0.5 rounded">
                        {skillDetails.source}
                      </span>
                      {skillDetails.category && (
                        <span className="text-xs bg-cool-blue/20 text-light-grey px-2 py-0.5 rounded">
                          {skillDetails.category}
                        </span>
                      )}
                    </div>
                  </div>
                  {skillDetails.scope === 'project' && (
                    <button
                      onClick={() => {
                        if (confirm(`Delete skill "${skillDetails.name}"?`)) {
                          deleteSkillMutation.mutate(skillDetails.name);
                        }
                      }}
                      className="p-2 rounded hover:bg-blaze-orange/20 transition-colors"
                      title="Delete skill"
                    >
                      <Trash2 className="w-5 h-5 text-blaze-orange" />
                    </button>
                  )}
                </div>

                {skillDetails.description && (
                  <p className="text-light-grey mb-4">{skillDetails.description}</p>
                )}

                {skillDetails.tags && skillDetails.tags.length > 0 && (
                  <div className="flex gap-2 mb-4 flex-wrap">
                    <Tag className="w-4 h-4 text-light-grey" />
                    {skillDetails.tags.map((tag: string) => (
                      <span key={tag} className="text-xs bg-cool-blue/20 text-light-grey px-2 py-1 rounded">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}

                <div className="border-t border-electric-teal/20 pt-4">
                  <h4 className="text-sm font-bold text-electric-teal mb-2">Content</h4>
                  <pre className="bg-deep-night/50 border border-electric-teal/20 rounded-lg p-4 overflow-auto max-h-[400px] text-sm text-light-grey whitespace-pre-wrap">
                    {skillDetails.content || 'No content available'}
                  </pre>
                </div>

                <div className="flex gap-4 text-xs text-light-grey mt-4">
                  <span>Created: {new Date(skillDetails.created).toLocaleDateString()}</span>
                  <span>Modified: {new Date(skillDetails.modified).toLocaleDateString()}</span>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-light-grey">Failed to load skill details</div>
              </div>
            )
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Eye className="w-16 h-16 text-electric-teal/30 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-light-grey mb-2">Select a Skill</h3>
                <p className="text-light-grey text-sm">
                  Click on a skill to view its details and content
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Install Template Modal */}
      <AnimatePresence>
        {showTemplates && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
            onClick={() => setShowTemplates(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-deep-night border border-electric-teal/30 rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-white">Install Skills</h2>
                <button
                  onClick={() => setShowTemplates(false)}
                  className="p-1 hover:bg-electric-teal/20 rounded"
                >
                  <X className="w-5 h-5 text-light-grey" />
                </button>
              </div>

              {/* Tab Selector */}
              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => setTemplateTab('local')}
                  className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2 ${
                    templateTab === 'local'
                      ? 'bg-electric-teal text-deep-night'
                      : 'bg-cool-blue/20 text-light-grey hover:bg-cool-blue/30'
                  }`}
                >
                  <FolderOpen className="w-4 h-4" />
                  Local Templates
                </button>
                <button
                  onClick={() => setTemplateTab('community')}
                  className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2 ${
                    templateTab === 'community'
                      ? 'bg-electric-teal text-deep-night'
                      : 'bg-cool-blue/20 text-light-grey hover:bg-cool-blue/30'
                  }`}
                >
                  <Github className="w-4 h-4" />
                  Community Skills
                </button>
              </div>

              {/* Search and Source Filter */}
              <div className="flex gap-2 mb-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-light-grey" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder={templateTab === 'local' ? 'Search templates...' : 'Search community skills...'}
                    className="input w-full pl-10"
                  />
                </div>
                {templateTab === 'community' && (
                  <>
                    <select
                      value={selectedCommunitySource}
                      onChange={(e) => setSelectedCommunitySource(e.target.value)}
                      className="input w-40"
                    >
                      <option value="all">All Sources</option>
                      {Object.entries(communitySources).map(([key, source]) => (
                        <option key={key} value={key}>{source.name}</option>
                      ))}
                    </select>
                    <button
                      onClick={() => refetchCommunity()}
                      className="btn-secondary p-2"
                      title="Refresh community skills"
                    >
                      <RefreshCw className={`w-4 h-4 ${communityLoading ? 'animate-spin' : ''}`} />
                    </button>
                  </>
                )}
              </div>

              {/* Content based on tab */}
              <div className="flex-1 overflow-y-auto space-y-2">
                {templateTab === 'local' ? (
                  // Local Templates
                  templatesLoading ? (
                    <div className="text-center py-8 text-light-grey">Loading templates...</div>
                  ) : (
                    categories.map((category) => {
                      const categoryTemplates = templatesByCategory[category] || [];
                      if (categoryTemplates.length === 0) return null;

                      return (
                        <div key={category} className="border border-electric-teal/20 rounded-lg overflow-hidden">
                          <button
                            onClick={() => toggleCategory(category)}
                            className="w-full px-4 py-3 flex items-center justify-between bg-cool-blue/10 hover:bg-cool-blue/20 transition-colors"
                          >
                            <span className="font-semibold text-electric-teal capitalize">
                              {category} ({categoryTemplates.length})
                            </span>
                            {expandedCategories.has(category) ? (
                              <ChevronDown className="w-4 h-4 text-light-grey" />
                            ) : (
                              <ChevronRight className="w-4 h-4 text-light-grey" />
                            )}
                          </button>
                          {expandedCategories.has(category) && (
                            <div className="divide-y divide-electric-teal/10">
                              {categoryTemplates.map((template) => {
                                const isInstalled = projectSkills.some(s => s.name === template.name);
                                return (
                                  <div
                                    key={template.name}
                                    className="p-4 hover:bg-cool-blue/10 transition-colors"
                                  >
                                    <div className="flex items-start justify-between">
                                      <div className="flex-1">
                                        <div className="font-medium text-white">{template.name}</div>
                                        <div className="text-sm text-light-grey mt-1">
                                          {template.description}
                                        </div>
                                        <div className="flex gap-1 mt-2 flex-wrap">
                                          {template.tags.map(tag => (
                                            <span key={tag} className="text-xs bg-cool-blue/20 text-light-grey px-1.5 py-0.5 rounded">
                                              {tag}
                                            </span>
                                          ))}
                                        </div>
                                      </div>
                                      <button
                                        onClick={() => installTemplateMutation.mutate(template.name)}
                                        disabled={isInstalled || installTemplateMutation.isPending}
                                        className={`ml-4 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                                          isInstalled
                                            ? 'bg-electric-teal/20 text-electric-teal cursor-not-allowed'
                                            : 'bg-electric-teal text-deep-night hover:bg-electric-teal/80'
                                        }`}
                                      >
                                        {isInstalled ? (
                                          <span className="flex items-center gap-1">
                                            <Check className="w-4 h-4" />
                                            Installed
                                          </span>
                                        ) : installTemplateMutation.isPending ? (
                                          'Installing...'
                                        ) : (
                                          'Install'
                                        )}
                                      </button>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      );
                    })
                  )
                ) : (
                  // Community Skills
                  communityLoading ? (
                    <div className="text-center py-8">
                      <RefreshCw className="w-8 h-8 text-electric-teal animate-spin mx-auto mb-2" />
                      <div className="text-light-grey">Fetching community skills from GitHub...</div>
                      <div className="text-light-grey text-sm mt-1">This may take a moment</div>
                    </div>
                  ) : filteredCommunitySkills.length === 0 ? (
                    <div className="text-center py-8">
                      <Github className="w-12 h-12 text-light-grey/30 mx-auto mb-2" />
                      <div className="text-light-grey">No community skills found</div>
                      <div className="text-light-grey text-sm mt-1">Try a different search or source</div>
                    </div>
                  ) : (
                    Object.entries(communityBySource).map(([source, skills]) => {
                      const sourceInfo = communitySources[source];
                      return (
                        <div key={source} className="border border-electric-teal/20 rounded-lg overflow-hidden">
                          <button
                            onClick={() => toggleCategory(source)}
                            className="w-full px-4 py-3 flex items-center justify-between bg-cool-blue/10 hover:bg-cool-blue/20 transition-colors"
                          >
                            <div className="flex items-center gap-2">
                              <Github className="w-4 h-4 text-light-grey" />
                              <span className="font-semibold text-electric-teal">
                                {sourceInfo?.name || source} ({skills.length})
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <a
                                href={`https://github.com/${sourceInfo?.repo || source}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(e) => e.stopPropagation()}
                                className="text-light-grey hover:text-electric-teal"
                              >
                                <ExternalLink className="w-4 h-4" />
                              </a>
                              {expandedCategories.has(source) ? (
                                <ChevronDown className="w-4 h-4 text-light-grey" />
                              ) : (
                                <ChevronRight className="w-4 h-4 text-light-grey" />
                              )}
                            </div>
                          </button>
                          {expandedCategories.has(source) && (
                            <div className="divide-y divide-electric-teal/10">
                              {skills.map((skill) => {
                                const isInstalled = projectSkills.some(s => s.name === skill.name);
                                return (
                                  <div
                                    key={`${skill.source}-${skill.name}`}
                                    className="p-4 hover:bg-cool-blue/10 transition-colors"
                                  >
                                    <div className="flex items-start justify-between">
                                      <div className="flex-1">
                                        <div className="flex items-center gap-2">
                                          <div className="font-medium text-white">{skill.name}</div>
                                          <a
                                            href={skill.readme_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-light-grey hover:text-electric-teal"
                                            title="View on GitHub"
                                          >
                                            <ExternalLink className="w-3 h-3" />
                                          </a>
                                        </div>
                                        <div className="text-sm text-light-grey mt-1">
                                          {skill.description || 'No description available'}
                                        </div>
                                        <div className="text-xs text-light-grey/60 mt-1">
                                          {skill.repo}
                                        </div>
                                      </div>
                                      <button
                                        onClick={() => installCommunityMutation.mutate(skill)}
                                        disabled={isInstalled || installCommunityMutation.isPending}
                                        className={`ml-4 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                                          isInstalled
                                            ? 'bg-electric-teal/20 text-electric-teal cursor-not-allowed'
                                            : 'bg-electric-teal text-deep-night hover:bg-electric-teal/80'
                                        }`}
                                      >
                                        {isInstalled ? (
                                          <span className="flex items-center gap-1">
                                            <Check className="w-4 h-4" />
                                            Installed
                                          </span>
                                        ) : installCommunityMutation.isPending ? (
                                          'Installing...'
                                        ) : (
                                          'Install'
                                        )}
                                      </button>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      );
                    })
                  )
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Create Skill Modal */}
      <AnimatePresence>
        {showCreateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
            onClick={() => setShowCreateModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-deep-night border border-electric-teal/30 rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="text-2xl font-bold text-white mb-4">Create Custom Skill</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-light-grey mb-2">Skill Name *</label>
                  <input
                    type="text"
                    value={newSkillName}
                    onChange={(e) => setNewSkillName(e.target.value)}
                    placeholder="my-skill"
                    className="input w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm text-light-grey mb-2">Description *</label>
                  <input
                    type="text"
                    value={newSkillDescription}
                    onChange={(e) => setNewSkillDescription(e.target.value)}
                    placeholder="What this skill does..."
                    className="input w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm text-light-grey mb-2">Category (optional)</label>
                  <input
                    type="text"
                    value={newSkillCategory}
                    onChange={(e) => setNewSkillCategory(e.target.value)}
                    placeholder="e.g., backend, frontend, testing"
                    className="input w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm text-light-grey mb-2">Tags (comma-separated)</label>
                  <input
                    type="text"
                    value={newSkillTags}
                    onChange={(e) => setNewSkillTags(e.target.value)}
                    placeholder="ruby, rails, api"
                    className="input w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm text-light-grey mb-2">Content (Markdown) *</label>
                  <textarea
                    value={newSkillContent}
                    onChange={(e) => setNewSkillContent(e.target.value)}
                    placeholder="# My Skill&#10;&#10;Describe what this skill does and how to use it..."
                    className="input w-full h-64 font-mono text-sm resize-none"
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    onClick={() => {
                      setShowCreateModal(false);
                      resetCreateForm();
                    }}
                    className="btn-secondary flex-1"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => createSkillMutation.mutate()}
                    disabled={!newSkillName.trim() || !newSkillDescription.trim() || !newSkillContent.trim() || createSkillMutation.isPending}
                    className="btn-primary flex-1"
                  >
                    {createSkillMutation.isPending ? 'Creating...' : 'Create Skill'}
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
