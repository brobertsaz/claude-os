import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Activity,
  Server,
  Database,
  Zap,
  Eye,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Cpu,
  MemoryStick
} from 'lucide-react';
import axios from 'axios';

interface Service {
  name: string;
  type: string;
  port: number | null;
  running: boolean;
  status: string;
  pid: number | null;
  cpu: number;
  memory: number;
  description: string;
}

interface ServicesResponse {
  services: Service[];
  summary: {
    total: number;
    running: number;
    stopped: number;
    health: 'healthy' | 'degraded' | 'critical';
  };
  timestamp: number;
}

const SERVICE_ICONS: Record<string, any> = {
  mcp_server: Server,
  frontend: Activity,
  redis: Database,
  rq_worker: Zap,
  ollama: Cpu,
  file_watcher: Eye
};

const STATUS_COLORS = {
  running: {
    bg: 'bg-green-500/20',
    border: 'border-green-500',
    text: 'text-green-400',
    icon: CheckCircle2
  },
  stopped: {
    bg: 'bg-gray-500/20',
    border: 'border-gray-500',
    text: 'text-gray-400',
    icon: XCircle
  },
  unknown: {
    bg: 'bg-yellow-500/20',
    border: 'border-yellow-500',
    text: 'text-yellow-400',
    icon: AlertCircle
  }
};

export default function ServiceDashboard() {
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch services status
  const { data: servicesData, isLoading, refetch } = useQuery<ServicesResponse>({
    queryKey: ['services-status'],
    queryFn: async () => {
      const response = await axios.get('/api/services/status');
      return response.data;
    },
    refetchInterval: autoRefresh ? 5000 : false, // Refresh every 5 seconds if enabled
  });

  const services = servicesData?.services || [];
  const summary = servicesData?.summary;

  const getHealthColor = (health?: string) => {
    switch (health) {
      case 'healthy':
        return 'text-green-400';
      case 'degraded':
        return 'text-yellow-400';
      case 'critical':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold gradient-text flex items-center gap-2">
            <Activity className="w-6 h-6" />
            Service Dashboard
          </h2>
          <p className="text-light-grey text-sm mt-1">
            Real-time monitoring of Claude OS services
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
              {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
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
      {summary && (
        <div className="grid grid-cols-4 gap-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-panel p-4"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="text-light-grey text-sm">Total Services</div>
                <div className="text-3xl font-bold text-white mt-1">{summary.total}</div>
              </div>
              <Server className="w-8 h-8 text-electric-teal opacity-50" />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-panel p-4"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="text-light-grey text-sm">Running</div>
                <div className="text-3xl font-bold text-green-400 mt-1">{summary.running}</div>
              </div>
              <CheckCircle2 className="w-8 h-8 text-green-400 opacity-50" />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-panel p-4"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="text-light-grey text-sm">Stopped</div>
                <div className="text-3xl font-bold text-gray-400 mt-1">{summary.stopped}</div>
              </div>
              <XCircle className="w-8 h-8 text-gray-400 opacity-50" />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-panel p-4"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="text-light-grey text-sm">System Health</div>
                <div className={`text-2xl font-bold mt-1 capitalize ${getHealthColor(summary.health)}`}>
                  {summary.health}
                </div>
              </div>
              <Activity className={`w-8 h-8 opacity-50 ${getHealthColor(summary.health)}`} />
            </div>
          </motion.div>
        </div>
      )}

      {/* Services Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {services.map((service, index) => {
          const Icon = SERVICE_ICONS[service.type] || Server;
          const statusConfig = STATUS_COLORS[service.status] || STATUS_COLORS.unknown;
          const StatusIcon = statusConfig.icon;

          return (
            <motion.div
              key={service.type}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.05 }}
              className={`glass-panel p-5 border-2 ${service.running ? 'border-green-500/30' : 'border-gray-500/30'}`}
            >
              {/* Service Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${service.running ? 'bg-green-500/20' : 'bg-gray-500/20'}`}>
                    <Icon className={`w-5 h-5 ${service.running ? 'text-green-400' : 'text-gray-400'}`} />
                  </div>
                  <div>
                    <h3 className="font-bold text-white">{service.name}</h3>
                    <p className="text-xs text-light-grey">{service.description}</p>
                  </div>
                </div>

                {/* Status Badge */}
                <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${statusConfig.bg} border ${statusConfig.border}`}>
                  <StatusIcon className={`w-3 h-3 ${statusConfig.text}`} />
                  <span className={`text-xs font-medium ${statusConfig.text} capitalize`}>
                    {service.status}
                  </span>
                </div>
              </div>

              {/* Service Details */}
              <div className="space-y-2">
                {service.port && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-light-grey">Port:</span>
                    <span className="text-white font-mono">{service.port}</span>
                  </div>
                )}

                {service.pid && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-light-grey">PID:</span>
                    <span className="text-white font-mono">{service.pid}</span>
                  </div>
                )}

                {service.running && service.cpu !== undefined && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-light-grey flex items-center gap-1">
                      <Cpu className="w-3 h-3" />
                      CPU:
                    </span>
                    <span className="text-white font-mono">{service.cpu.toFixed(1)}%</span>
                  </div>
                )}

                {service.running && service.memory !== undefined && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-light-grey flex items-center gap-1">
                      <MemoryStick className="w-3 h-3" />
                      Memory:
                    </span>
                    <span className="text-white font-mono">{service.memory.toFixed(1)}%</span>
                  </div>
                )}
              </div>

              {/* Service URL (if applicable) */}
              {service.port && service.running && (
                <div className="mt-4 pt-4 border-t border-electric-teal/20">
                  <a
                    href={`http://localhost:${service.port}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-electric-teal hover:text-electric-teal/80 transition-colors font-mono"
                  >
                    http://localhost:{service.port}
                  </a>
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Help Text */}
      <div className="glass-panel p-4 border border-electric-teal/30">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-electric-teal flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-white mb-1">Service Management</h4>
            <p className="text-sm text-light-grey">
              To start/stop services, use the management scripts:
            </p>
            <div className="mt-2 space-y-1">
              <code className="text-xs text-electric-teal block">./start_all_services.sh</code>
              <code className="text-xs text-electric-teal block">./stop_all_services.sh</code>
              <code className="text-xs text-electric-teal block">./restart_services.sh</code>
            </div>
          </div>
        </div>
      </div>

      {/* Last Updated */}
      {servicesData && (
        <div className="text-center text-xs text-light-grey">
          Last updated: {new Date(servicesData.timestamp * 1000).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}
