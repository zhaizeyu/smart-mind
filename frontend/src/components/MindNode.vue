<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { MindNode } from '../types/mind';

const props = defineProps<{
  node: MindNode;
  loading?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:question', value: string): void;
  (e: 'ask'): void;
  (e: 'delete'): void;
}>();

const draftQuestion = ref(props.node.question);

watch(
  () => props.node.question,
  newVal => {
    draftQuestion.value = newVal;
  }
);

const disableActions = computed(() => props.loading || !draftQuestion.value.trim());

function handleSubmit() {
  if (disableActions.value) return;
  emit('update:question', draftQuestion.value.trim());
  emit('ask');
}
</script>

<template>
  <section class="node-panel">
    <header>
      <h2>节点详情</h2>
      <button class="danger" type="button" @click="emit('delete')">删除节点</button>
    </header>

    <label>
      问题
      <textarea v-model="draftQuestion" rows="4" placeholder="输入要提问的大模型问题"></textarea>
    </label>

    <div class="actions">
      <button type="button" :disabled="disableActions" @click="handleSubmit">
        {{ loading ? '提问中...' : '向 AI 提问' }}
      </button>
    </div>

    <label>
      回答
      <article v-if="node.answer" class="answer">
        {{ node.answer }}
      </article>
      <p v-else class="placeholder">等待 AI 返回回答...</p>
    </label>
  </section>
</template>

<style scoped>
.node-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  background: #fff;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
  height: 100%;
}

header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

h2 {
  margin: 0;
  font-size: 1.1rem;
}

label {
  display: flex;
  flex-direction: column;
  font-size: 0.85rem;
  color: #475569;
  gap: 0.5rem;
}

textarea {
  border-radius: 12px;
  border: 1px solid #cbd5f5;
  padding: 0.75rem;
  font-size: 0.95rem;
  resize: vertical;
  font-family: inherit;
}

.actions {
  display: flex;
  justify-content: flex-end;
}

button {
  border: none;
  border-radius: 999px;
  padding: 0.6rem 1.6rem;
  background: #2563eb;
  color: #fff;
  font-weight: 600;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

button.danger {
  background: transparent;
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.4);
}

.answer {
  min-height: 160px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px dashed #cbd5f5;
  padding: 1rem;
  line-height: 1.5;
  color: #0f172a;
  white-space: pre-wrap;
}

.placeholder {
  margin: 0;
  color: #94a3b8;
}
</style>
