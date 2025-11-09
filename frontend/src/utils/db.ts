import localforage from 'localforage';
import type { MindNode } from '../types/mind';

const db = localforage.createInstance({
  name: 'smartmind',
  storeName: 'mindmap'
});

const KEY = 'graph';

export async function loadMindMap(): Promise<MindNode[] | null> {
  return (await db.getItem<MindNode[]>(KEY)) ?? null;
}

export async function saveMindMap(nodes: MindNode[]): Promise<void> {
  await db.setItem(KEY, nodes);
}

export async function clearMindMap(): Promise<void> {
  await db.removeItem(KEY);
}
