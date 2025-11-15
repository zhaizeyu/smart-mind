import axios from 'axios';
import type { MindNode } from '../types/mind';

const client = axios.create({
  baseURL: '/api'
});

interface MindMapResponse {
  nodes: MindNode[];
}

export async function fetchServerMindMap(): Promise<MindNode[] | null> {
  try {
    const { data } = await client.get<MindMapResponse>('/mindmap');
    return data.nodes ?? null;
  } catch {
    return null;
  }
}

export async function persistServerMindMap(nodes: MindNode[]): Promise<void> {
  try {
    await client.post('/mindmap', { nodes } as MindMapResponse);
  } catch {
    // best-effort; 前端不阻塞
  }
}
