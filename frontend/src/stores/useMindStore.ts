import { defineStore } from 'pinia';
import type { MindMapState, MindNode, NodePosition } from '../types/mind';
import { computeTreeLayout } from '../utils/layout';

interface AddNodePayload {
  parentId?: string | null;
  question?: string;
  position?: NodePosition;
}

interface UpdateNodePayload {
  question?: string;
  answer?: string;
  position?: NodePosition;
}

const defaultPosition: NodePosition = { x: 80, y: 80 };

interface LocatedNode {
  node: MindNode;
  parent: MindNode | null;
}

function uid() {
  return crypto?.randomUUID?.() ?? `node-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function createNode(partial: Partial<MindNode> = {}): MindNode {
  const timestamp = new Date().toISOString();
  return {
    id: partial.id ?? uid(),
    parentId: partial.parentId ?? null,
    question: partial.question ?? '新的问题',
    answer: partial.answer,
    children: partial.children ?? [],
    position: partial.position ?? { ...defaultPosition },
    createdAt: partial.createdAt ?? timestamp,
    updatedAt: partial.updatedAt ?? timestamp
  };
}

function removeNode(nodes: MindNode[], id: string): boolean {
  const index = nodes.findIndex(node => node.id === id);
  if (index !== -1) {
    nodes.splice(index, 1);
    return true;
  }
  for (const node of nodes) {
    if (removeNode(node.children, id)) {
      return true;
    }
  }
  return false;
}

function hasDescendant(root: MindNode, targetId: string): boolean {
  for (const child of root.children) {
    if (child.id === targetId || hasDescendant(child, targetId)) {
      return true;
    }
  }
  return false;
}

export const useMindStore = defineStore('mind', {
  state: (): MindMapState => ({
    nodes: [],
    selectedNodeId: undefined
  }),
  getters: {
    selectedNode(state): MindNode | undefined {
      if (!state.selectedNodeId) return undefined;
      return state.nodes.flatMap(flattenNodes).find(node => node.id === state.selectedNodeId);
    }
  },
  actions: {
    ensureRoot() {
      if (this.nodes.length === 0) {
        const root = createNode({ question: '输入一个中心问题', position: { x: 400, y: 200 } });
        this.nodes.push(root);
        this.selectedNodeId = root.id;
        this.autoArrange();
      }
    },
    addNode(payload: AddNodePayload = {}) {
      const base = createNode({
        parentId: payload.parentId ?? null,
        question: payload.question ?? '新的问题',
        position: payload.position ?? defaultPosition
      });

      if (payload.parentId) {
        const res = this.findNodeById(payload.parentId);
        res?.node.children.push(base);
      } else {
        this.nodes.push(base);
      }
      this.selectedNodeId = base.id;
      this.autoArrange();
      return base;
    },
    updateNode(id: string, payload: UpdateNodePayload) {
      const res = this.findNodeById(id);
      if (!res) return;
      Object.assign(res.node, payload, { updatedAt: new Date().toISOString() });
    },
    moveNode(id: string, position: NodePosition) {
      this.updateNode(id, { position });
    },
    removeNode(id: string) {
      if (!id) return;
      removeNode(this.nodes, id);
      if (this.selectedNodeId === id) {
        this.selectedNodeId = this.nodes[0]?.id;
      }
      if (!this.nodes.length) {
        this.ensureRoot();
      } else {
        this.autoArrange();
      }
    },
    selectNode(id?: string) {
      this.selectedNodeId = id;
    },
    replaceAll(nodes: MindNode[]) {
      this.nodes = nodes;
      this.selectedNodeId = nodes[0]?.id;
      if (this.nodes.length) {
        this.autoArrange();
      } else {
        this.ensureRoot();
      }
    },
    findNodeById(id: string): LocatedNode | null {
      const stack: LocatedNode[] = this.nodes.map(node => ({ node, parent: null }));
      while (stack.length) {
        const current = stack.pop()!;
        if (current.node.id === id) {
          return current;
        }
        for (const child of current.node.children) {
          stack.push({ node: child, parent: current.node });
        }
      }
      return null;
    },
    reparentNode(id: string, newParentId: string | null) {
      if (id === newParentId) return;
      const target = this.findNodeById(id);
      if (!target) return;
      if (target.node.parentId === newParentId) return;
      if (newParentId) {
        const newParent = this.findNodeById(newParentId);
        if (!newParent) return;
        if (hasDescendant(target.node, newParentId)) {
          return;
        }
      }
      if (target.parent) {
        target.parent.children = target.parent.children.filter(child => child.id !== id);
      } else {
        this.nodes = this.nodes.filter(node => node.id !== id);
      }
      target.node.parentId = newParentId;
      target.node.updatedAt = new Date().toISOString();
      if (newParentId) {
        const newParent = this.findNodeById(newParentId);
        newParent?.node.children.push(target.node);
      } else {
        this.nodes.push(target.node);
      }
      this.autoArrange();
    },
    autoArrange() {
      if (!this.nodes.length) return;
      const layout = computeTreeLayout(this.nodes);
      applyPositions(this.nodes, layout);
    }
  }
});

function flattenNodes(node: MindNode): MindNode[] {
  return [node, ...node.children.flatMap(flattenNodes)];
}

function applyPositions(nodes: MindNode[], layout: Record<string, NodePosition>) {
  for (const node of nodes) {
    const position = layout[node.id];
    if (position) {
      node.position = { ...position };
    }
    if (node.children.length) {
      applyPositions(node.children, layout);
    }
  }
}
