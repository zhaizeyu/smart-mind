import type { MindNode, NodePosition } from '../types/mind';

export const NODE_WIDTH = 240;
export const NODE_HEIGHT = 140;

interface LayoutOptions {
  startX?: number;
  startY?: number;
  levelGap?: number;
  siblingGap?: number;
  rootGap?: number;
  nodeHeight?: number;
}

const DEFAULT_OPTIONS: Required<LayoutOptions> = {
  startX: 80,
  startY: 80,
  levelGap: 260,
  siblingGap: 180,
  rootGap: 240,
  nodeHeight: NODE_HEIGHT
};

export function computeTreeLayout(nodes: MindNode[], options: LayoutOptions = {}): Record<string, NodePosition> {
  if (!nodes.length) return {};
  const config = { ...DEFAULT_OPTIONS, ...options };
  const unitHeight = config.siblingGap;
  const sizeMap = new Map<string, number>();

  const measure = (node: MindNode): number => {
    if (!node.children.length) {
      sizeMap.set(node.id, 1);
      return 1;
    }
    const sum = node.children.reduce((acc, child) => acc + measure(child), 0);
    sizeMap.set(node.id, Math.max(sum, 1));
    return Math.max(sum, 1);
  };

  nodes.forEach(measure);
  let currentTop = config.startY;
  const positions: Record<string, NodePosition> = {};

  const assign = (node: MindNode, depth: number, top: number) => {
    const spanUnits = sizeMap.get(node.id) ?? 1;
    const subtreeHeight = Math.max(spanUnits * unitHeight, config.nodeHeight);
    const nodeCenterY = top + subtreeHeight / 2;
    positions[node.id] = {
      x: config.startX + depth * config.levelGap,
      y: nodeCenterY - config.nodeHeight / 2
    };
    if (!node.children.length) return;
    let childTop = top;
    for (const child of node.children) {
      const childUnits = sizeMap.get(child.id) ?? 1;
      const childHeight = Math.max(childUnits * unitHeight, config.nodeHeight);
      assign(child, depth + 1, childTop);
      childTop += childHeight;
    }
  };

  for (const root of nodes) {
    const spanUnits = sizeMap.get(root.id) ?? 1;
    const subtreeHeight = Math.max(spanUnits * unitHeight, config.nodeHeight);
    assign(root, 0, currentTop);
    currentTop += subtreeHeight + config.rootGap;
  }

  return positions;
}
