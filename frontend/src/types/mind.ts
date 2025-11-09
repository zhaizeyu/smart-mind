export interface NodePosition {
  x: number;
  y: number;
}

export interface MindNode {
  id: string;
  parentId: string | null;
  question: string;
  answer?: string;
  children: MindNode[];
  position: NodePosition;
  createdAt: string;
  updatedAt: string;
}

export interface MindMapState {
  nodes: MindNode[];
  selectedNodeId?: string;
}
