const API_BASE = 'http://localhost:8051';

export interface ChatResponse {
  response: string;
  sources?: Array<{
    filename: string;
    content: string;
    score: number;
  }>;
  thinking_time?: number;
}

export interface KBStats {
  document_count: number;
  chunk_count: number;
  last_updated?: string;
  total_size?: number;
}

export interface Document {
  filename: string;
  chunk_count: number;
  created_at?: string;
}

export async function chat(
  kbName: string,
  query: string,
  options?: { useHybrid?: boolean; useRerank?: boolean; useAgentic?: boolean }
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/kb/${kbName}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      use_hybrid: options?.useHybrid ?? false,
      use_rerank: options?.useRerank ?? false,
      use_agentic: options?.useAgentic ?? false,
    }),
  });

  if (!res.ok) {
    throw new Error(`Chat failed: ${res.statusText}`);
  }

  return res.json();
}

export async function getKBStats(kbName: string): Promise<KBStats> {
  const res = await fetch(`${API_BASE}/api/kb/${kbName}/stats`);
  if (!res.ok) {
    throw new Error(`Failed to get KB stats: ${res.statusText}`);
  }
  return res.json();
}

export async function listDocuments(kbName: string): Promise<Document[]> {
  const res = await fetch(`${API_BASE}/api/kb/${kbName}/documents`);
  if (!res.ok) {
    throw new Error(`Failed to list documents: ${res.statusText}`);
  }
  const data = await res.json();
  return data.documents || [];
}

export async function uploadDocument(kbName: string, file: File): Promise<void> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/api/kb/${kbName}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    throw new Error(`Failed to upload document: ${res.statusText}`);
  }
}

export async function deleteDocument(kbName: string, filename: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/kb/${kbName}/documents/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  });

  if (!res.ok) {
    throw new Error(`Failed to delete document: ${res.statusText}`);
  }
}
