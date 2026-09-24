<script setup>
import { ref } from "vue";
import { storeToRefs } from "pinia";

import ConfirmDialog from "./ConfirmDialog.vue";
import Icon from "./Icon.vue";
import { deleteJson } from "../api";
import { useAppStore } from "../stores/app";

const app = useAppStore();
const { weather, sessions, sessionId, currentPage, knowledgeCount } =
  storeToRefs(app);

const pageMeta = {
  chat: ["对话", "向你的资料提问"],
  knowledge: ["知识库", "整理和更新 Know包"],
  settings: ["设置", "调整切分和检索参数"],
};

const deleteDialog = ref(null);
const pendingDelete = ref(null);

function formatTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (number) => String(number).padStart(2, "0");
  return `${pad(date.getMonth() + 1)}/${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function requestDelete(session) {
  pendingDelete.value = session;
  deleteDialog.value?.show(`确定删除“${session.title}”吗？删除后无法恢复。`);
}

async function confirmDelete() {
  const session = pendingDelete.value;
  pendingDelete.value = null;
  if (!session) return;
  try {
    const result = await deleteJson(
      `/api/history/${encodeURIComponent(session.session_id)}`
    );
    app.toast(result.message);
    if (session.session_id === sessionId.value) {
      app.startNewConversation();
    }
    await app.loadSessions();
  } catch (error) {
    app.toast(error.message, "error");
  }
}
</script>

<template>
  <aside class="sidebar">
    <div class="brand">
      <span class="brand-icon"><Icon name="pack" /></span>
      <span><strong>Know包</strong><small>把资料装进自己的知识包</small></span>
    </div>

    <section class="weather-card" :data-state="weather.state" aria-live="polite">
      <div class="cardContainer">
        <div class="card">
          <span class="city">{{ weather.city || '--' }}</span>
          <span class="weather-text">{{ weather.text || '...' }}</span>
          <span class="temp">{{ weather.temp || '--' }}°</span>
          <div class="minmaxContainer">
            <div class="min">
              <span class="minHeading">体感</span>
              <span class="minTemp">{{ weather.feels_like || '--' }}°</span>
            </div>
            <div class="max">
              <span class="maxHeading">湿度</span>
              <span class="maxTemp">{{ weather.humidity || '--' }}%</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <button class="new-chat" @click="app.startNewConversation()">
      <Icon name="plus" />新建对话
    </button>
    <p class="sidebar-label">最近对话</p>
    <nav class="conversation-list" aria-label="最近对话">
      <div
        v-for="session in sessions"
        :key="session.session_id"
        class="conversation-row"
      >
        <button
          class="conversation-item"
          :class="{ active: session.session_id === sessionId }"
          :title="session.title"
          @click="app.selectSession(session)"
        >
          <span>{{ session.title }}</span>
          <time v-if="formatTime(session.updated_at)">更新于 {{ formatTime(session.updated_at) }}</time>
        </button>
        <button
          class="icon-button delete-conversation"
          type="button"
          :title="`删除对话：${session.title}`"
          :aria-label="`删除对话：${session.title}`"
          @click="requestDelete(session)"
        >
          <Icon name="trash" />
        </button>
      </div>
    </nav>

    <div class="sidebar-bottom">
      <button
        v-for="page in ['chat', 'knowledge', 'settings']"
        :key="page"
        class="side-link"
        :class="{ active: currentPage === page }"
        @click="app.navigate(page)"
      >
        <Icon
          :name="page === 'chat' ? 'chat' : page === 'knowledge' ? 'library' : 'settings'"
        />
        {{ pageMeta[page][0] }}
        <span v-if="page === 'knowledge'">{{ knowledgeCount }}</span>
      </button>
    </div>

    <ConfirmDialog
      ref="deleteDialog"
      title="删除历史对话？"
      @confirm="confirmDelete"
    />
  </aside>
</template>
