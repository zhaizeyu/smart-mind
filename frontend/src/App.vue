<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import MindMapCanvas from './components/MindMapCanvas.vue';
import MindNode from './components/MindNode.vue';
import { useMindStore } from './stores/useMindStore';
import { askQuestion, summarizeNode, type SummaryEntry } from './utils/useAI';
import { clearMindMap, loadMindMap, saveMindMap } from './utils/db';
import type { MindNode as MindNodeType } from './types/mind';

const store = useMindStore();
const isAsking = ref(false);
const isSummarizing = ref(false);
const toast = ref<string | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);

const selectedNode = computed(() => store.selectedNode);

onMounted(async () => {
  const persisted = await loadMindMap();
  if (persisted?.length) {
    store.replaceAll(persisted);
  }
  store.ensureRoot();
});

watch(
  () => store.nodes,
  nodes => {
    const snapshot = JSON.parse(JSON.stringify(nodes)) as MindNodeType[];
    saveMindMap(snapshot);
  },
  { deep: true }
);

async function handleAsk() {
  const node = selectedNode.value;
  if (!node || !node.question.trim()) return;
  isAsking.value = true;
  try {
    const { answer } = await askQuestion({ question: node.question });
    store.updateNode(node.id, { answer });
    toast.value = 'AI 回答已写入节点';
  } catch (error) {
    store.updateNode(node.id, {
      answer: `调用 AI 失败：${(error as Error).message}`
    });
  } finally {
    isAsking.value = false;
    setTimeout(() => (toast.value = null), 2000);
  }
}

function collectSummaryEntries(node: MindNodeType, depth = 0, acc: SummaryEntry[] = []): SummaryEntry[] {
  acc.push({
    question: node.question,
    answer: node.answer,
    depth
  });
  node.children.forEach(child => collectSummaryEntries(child, depth + 1, acc));
  return acc;
}

async function handleSummarize() {
  const node = selectedNode.value;
  if (!node) return;
  isSummarizing.value = true;
  try {
    const entries = collectSummaryEntries(node);
    const { summary } = await summarizeNode({
      topic: node.question,
      entries
    });
    store.updateNode(node.id, { answer: summary });
    toast.value = '节点汇总完成';
  } catch (error) {
    toast.value = `节点汇总失败：${(error as Error).message}`;
  } finally {
    isSummarizing.value = false;
    setTimeout(() => (toast.value = null), 2000);
  }
}

function handleAddRoot() {
  store.addNode({ parentId: null, question: '新的中心问题', position: { x: 200, y: 120 } });
}

function handleAddChild(parentId?: string) {
  if (!parentId && !selectedNode.value) return;
  store.addNode({
    parentId: parentId ?? selectedNode.value?.id ?? null,
    question: '子问题',
    position: { x: (selectedNode.value?.position.x ?? 200) + 240, y: selectedNode.value?.position.y ?? 200 }
  });
}

function exportMindMap() {
  const payload = JSON.stringify(store.nodes, null, 2);
  const blob = new Blob([payload], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'mindflow.json';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

async function importMindMap(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  try {
    const text = await file.text();
    const data = JSON.parse(text) as MindNodeType[];
    store.replaceAll(data);
  } catch (error) {
    toast.value = `导入失败：${(error as Error).message}`;
  } finally {
    input.value = '';
  }
}

async function resetMindMap() {
  await clearMindMap();
  store.replaceAll([]);
  store.ensureRoot();
}
</script>

<template>
  <div class="app-shell">
    <header class="hero">
      <div>
        <p class="eyebrow">MindFlow</p>
        <h1>MindFlow 智能思维导图</h1>
        <p>以节点组织问题，连接大模型，管理灵感。</p>
      </div>
      <div class="toolbar">
        <button type="button" @click="handleAddRoot">新增根节点</button>
        <button type="button" @click="handleAddChild()">新增子节点</button>
        <button type="button" @click="exportMindMap">导出 JSON</button>
        <button type="button" @click="fileInput?.click()">导入 JSON</button>
        <button type="button" class="ghost" @click="resetMindMap">清空</button>
        <input ref="fileInput" type="file" accept="application/json" hidden @change="importMindMap" />
      </div>
    </header>

    <main>
      <section class="canvas-area">
        <MindMapCanvas
          :nodes="store.nodes"
          :selected-id="store.selectedNodeId"
          @select="store.selectNode"
          @add-child="handleAddChild"
          @delete-node="store.removeNode"
        />
      </section>
      <section class="panel-area" v-if="selectedNode">
        <MindNode
          :node="selectedNode"
          :loading="isAsking"
          :summarizing="isSummarizing"
          @update:question="value => store.updateNode(selectedNode.id, { question: value })"
          @update:answer="value => store.updateNode(selectedNode.id, { answer: value })"
          @ask="handleAsk"
          @summarize="handleSummarize"
          @delete="() => store.removeNode(selectedNode.id)"
        />
      </section>
      <section class="panel-area placeholder" v-else>
        <p>请选择一个节点查看详情</p>
      </section>
    </main>

    <transition name="toast">
      <div v-if="toast" class="toast">{{ toast }}</div>
    </transition>
  </div>
</template>

<style scoped>
.app-shell {
  padding: 2.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  min-height: 100vh;
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #eff6ff, #e0f2fe);
  border-radius: 24px;
  padding: 1.5rem 2rem;
  box-shadow: 0 20px 40px rgba(59, 130, 246, 0.25);
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.2rem;
  color: #3b82f6;
  font-size: 0.8rem;
}

.hero h1 {
  margin: 0.2rem 0;
}

.toolbar {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.toolbar button {
  border: none;
  border-radius: 999px;
  padding: 0.6rem 1.4rem;
  background: #1d4ed8;
  color: #fff;
  font-weight: 600;
}

button.ghost {
  background: transparent;
  color: #1d4ed8;
  border: 1px solid rgba(29, 78, 216, 0.3);
}

main {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
  flex: 1;
}

.canvas-area,
.panel-area {
  min-height: 500px;
}

.panel-area.placeholder {
  display: grid;
  place-items: center;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px dashed #cbd5f5;
}

.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: #0f172a;
  color: #fff;
  padding: 0.8rem 1.2rem;
  border-radius: 999px;
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(12px);
}

@media (max-width: 1024px) {
  main {
    grid-template-columns: 1fr;
  }
}
</style>
