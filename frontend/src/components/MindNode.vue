<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { MindNode } from '../types/mind';

const props = defineProps<{
  node: MindNode;
  loading?: boolean;
  summarizing?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:question', value: string): void;
  (e: 'update:answer', value: string): void;
  (e: 'ask'): void;
  (e: 'summarize'): void;
  (e: 'delete'): void;
}>();

const draftQuestion = ref(props.node.question);
const draftAnswer = ref(props.node.answer ?? '');

watch(
  () => props.node.question,
  newVal => {
    draftQuestion.value = newVal;
  }
);

watch(
  () => props.node.answer,
  newVal => {
    draftAnswer.value = newVal ?? '';
  }
);

const disableAsk = computed(() => props.loading || props.summarizing || !draftQuestion.value.trim());
const disableSummarize = computed(() => props.loading || props.summarizing);
const disableSaveAnswer = computed(() => props.loading || props.summarizing || draftAnswer.value === (props.node.answer ?? ''));

function handleSubmit() {
  if (disableAsk.value) return;
  emit('update:question', draftQuestion.value.trim());
  emit('ask');
}

function handleSaveAnswer() {
  if (disableSaveAnswer.value) return;
  emit('update:answer', draftAnswer.value);
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
      <button type="button" :disabled="disableAsk" @click="handleSubmit">
        {{ loading ? '提问中...' : '向 AI 提问' }}
      </button>
      <button class="secondary" type="button" :disabled="disableSummarize" @click="emit('summarize')">
        {{ summarizing ? '汇总中...' : '节点汇总' }}
      </button>
    </div>

    <label>
      回答
      <textarea
        v-model="draftAnswer"
        rows="8"
        placeholder="可手动编辑回答内容，或等待 AI 返回结果"
      ></textarea>
      <div class="actions">
        <button class="secondary" type="button" :disabled="disableSaveAnswer" @click="handleSaveAnswer">
          保存答案
        </button>
      </div>
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
  gap: 0.5rem;
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

button.secondary {
  background: transparent;
  color: #0ea5e9;
  border: 1px solid rgba(14, 165, 233, 0.4);
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
