<script setup lang="ts">
import type { KonvaEventObject } from 'konva/lib/Node';
import { computed, ref } from 'vue';
import type { MindNode } from '../types/mind';
import { NODE_HEIGHT, NODE_WIDTH } from '../utils/layout';

const props = defineProps<{
  nodes: MindNode[];
  selectedId?: string;
}>();

const emit = defineEmits<{
  (e: 'select', id: string): void;
  (e: 'add-child', parentId: string): void;
  (e: 'delete-node', nodeId: string): void;
}>();

const expandedNodeId = ref<string | null>(null);

const flatNodes = computed(() => props.nodes.flatMap(walkNodes));

const connectors = computed(() => {
  const lines: { id: string; points: number[] }[] = [];
  const traverse = (node: MindNode) => {
    for (const child of node.children) {
      const startX = node.position.x + NODE_WIDTH;
      const startY = node.position.y + NODE_HEIGHT / 2;
      const endX = child.position.x;
      const endY = child.position.y + NODE_HEIGHT / 2;
      lines.push({ id: `${node.id}-${child.id}`, points: [startX, startY, endX, endY] });
      traverse(child);
    }
  };
  props.nodes.forEach(traverse);
  return lines;
});

const stageSize = computed(() => {
  const padding = 200;
  const minWidth = 900;
  const minHeight = 600;
  if (!flatNodes.value.length) {
    return { width: minWidth, height: minHeight };
  }
  const maxX = Math.max(...flatNodes.value.map(node => node.position.x + NODE_WIDTH));
  const maxY = Math.max(...flatNodes.value.map(node => node.position.y + NODE_HEIGHT));
  return {
    width: Math.max(maxX + padding, minWidth),
    height: Math.max(maxY + padding, minHeight)
  };
});

function walkNodes(node: MindNode): MindNode[] {
  return [node, ...node.children.flatMap(walkNodes)];
}

function handleAddChild(event: KonvaEventObject<MouseEvent>, parentId: string) {
  event.cancelBubble = true;
  emit('add-child', parentId);
}

function handleDelete(event: KonvaEventObject<MouseEvent>, nodeId: string) {
  event.cancelBubble = true;
  emit('delete-node', nodeId);
}

function openExpanded(event: KonvaEventObject<MouseEvent>, nodeId: string) {
  event.cancelBubble = true;
  expandedNodeId.value = nodeId;
}

function closeExpanded() {
  expandedNodeId.value = null;
}

const expandedNode = computed(() => flatNodes.value.find(node => node.id === expandedNodeId.value));
</script>

<template>
  <div class="canvas-wrapper">
    <v-stage :config="stageSize">
      <v-layer>
        <v-line
          v-for="line in connectors"
          :key="line.id"
          :config="{ points: line.points, stroke: '#cbd5f5', strokeWidth: 2, lineCap: 'round' }"
        />

        <template v-for="node in flatNodes" :key="node.id">
          <v-group :config="{ x: node.position.x, y: node.position.y }" @click="emit('select', node.id)">
            <v-rect
              :config="{
                width: NODE_WIDTH,
                height: NODE_HEIGHT,
                fill: node.id === selectedId ? '#e0f2fe' : '#fff',
                stroke: node.id === selectedId ? '#0ea5e9' : '#cbd5f5',
                cornerRadius: 20,
                shadowColor: '#94a3b8',
                shadowBlur: 12,
                shadowOpacity: 0.2
              }"
            />
            <v-text
              :config="{
                text: node.question,
                width: NODE_WIDTH - 24,
                x: 12,
                y: 14,
                fontSize: 16,
                fontStyle: '600',
                fill: '#0f172a'
              }"
            />
            <v-text
              :config="{
                text: node.answer ? node.answer : '等待回答...',
                width: NODE_WIDTH - 24,
                height: NODE_HEIGHT - 70,
                x: 12,
                y: 52,
                fontSize: 13,
                fill: '#475569',
                wrap: 'word',
                ellipsis: true,
                align: 'left',
                lineHeight: 1.4
              }"
            />
            <v-text
              :config="{
                text: '+',
                x: NODE_WIDTH - 44,
                y: NODE_HEIGHT - 32,
                fontSize: 24,
                fontStyle: '700',
                fill: '#22c55e'
              }"
              @click="handleAddChild($event, node.id)"
            />
            <v-text
              :config="{
                text: '-',
                x: NODE_WIDTH - 24,
                y: NODE_HEIGHT - 30,
                fontSize: 24,
                fontStyle: '700',
                fill: '#ef4444'
              }"
              @click="handleDelete($event, node.id)"
            />
            <v-text
              :config="{
                text: '···',
                x: NODE_WIDTH - 64,
                y: NODE_HEIGHT - 32,
                fontSize: 18,
                fill: '#0ea5e9'
              }"
              @click="openExpanded($event, node.id)"
            />
          </v-group>
        </template>
      </v-layer>
    </v-stage>

    <transition name="overlay">
      <div v-if="expandedNode" class="answer-overlay" @click.self="closeExpanded">
        <section class="answer-card">
          <header>
            <h3>{{ expandedNode.question }}</h3>
            <button type="button" @click="closeExpanded">关闭</button>
          </header>
          <article>
            <p v-if="expandedNode.answer">{{ expandedNode.answer }}</p>
            <p v-else class="placeholder">暂无回答</p>
          </article>
        </section>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.canvas-wrapper {
  width: 100%;
  height: 100%;
  border-radius: 24px;
  overflow: auto;
  box-shadow: inset 0 0 40px rgba(15, 23, 42, 0.06);
  background: linear-gradient(180deg, #f8fbff 0%, #eef2ff 100%);
  position: relative;
}

.answer-overlay {
  position: absolute;
  inset: 0;
  backdrop-filter: blur(6px);
  background: rgba(15, 23, 42, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.answer-card {
  width: min(560px, 90%);
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 30px 60px rgba(15, 23, 42, 0.2);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.answer-card header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.answer-card h3 {
  margin: 0;
}

.answer-card button {
  border: none;
  background: #0ea5e9;
  color: #fff;
  padding: 0.4rem 1rem;
  border-radius: 999px;
  font-weight: 600;
  cursor: pointer;
}

.answer-card article {
  max-height: 320px;
  overflow: auto;
  line-height: 1.6;
  color: #0f172a;
  white-space: pre-wrap;
}

.overlay-enter-active,
.overlay-leave-active {
  transition: opacity 0.2s ease;
}

.overlay-enter-from,
.overlay-leave-to {
  opacity: 0;
}
</style>
