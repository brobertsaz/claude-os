export interface CommonPath {
  label: string;
  path: string;
  description?: string;
}

export function getCommonProjectPaths(): CommonPath[] {
  return [
    { label: 'Home', path: '~', description: 'Your home directory' },
    { label: 'Documents', path: '~/Documents', description: 'Documents folder' },
    { label: 'Projects', path: '~/Projects', description: 'Common projects folder' },
    { label: 'Sites', path: '~/sites', description: 'Web projects' },
    { label: 'Code', path: '~/code', description: 'Code repositories' },
    { label: 'Desktop', path: '~/Desktop', description: 'Desktop folder' },
  ];
}

export function formatPathForDisplay(path: string): string {
  if (!path) return '';

  // Replace home directory with ~
  const homeDir = '/home/' + (typeof window !== 'undefined' ? 'user' : 'user');
  if (path.startsWith(homeDir)) {
    return path.replace(homeDir, '~');
  }

  // Shorten long paths
  if (path.length > 50) {
    const parts = path.split('/');
    if (parts.length > 4) {
      return `${parts[0]}/${parts[1]}/.../${parts[parts.length - 2]}/${parts[parts.length - 1]}`;
    }
  }

  return path;
}
