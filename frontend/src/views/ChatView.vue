<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { storeToRefs } from "pinia";

import Icon from "../components/Icon.vue";
import SourceBlock from "../components/SourceBlock.vue";
import { getJson, streamChat } from "../api";
import { renderMarkdown } from "../utils/markdown";
import {
  formatDisplayTime,
  getThinkingStatusText,
  RAG_MODE_HINTS,
} from "../utils/format";
import { useAppStore } from "../stores/app";

const app = useAppStore();
const { sessionId, ragMode, chatTitle } = storeToRefs(app);

const messages = ref([]);
const scrollEl = ref(null);
const inputEl = ref(null);
const inputValue = ref("");
const busy = ref(false);
const controller = ref(null);
const lastQuestion = ref("");
const suggestions = ["概括我的知识库", "列出资料的核心观点", "为我制定一份学习计划"];

const ragOptions = [
  { value: "off", label: "关闭 RAG" },
  { value: "force", label: "强制参考" },
  { value: "auto", label: "智能筛选" },
];

const isEmpty = computed(() => messages.value.length === 0);

function scrollBottom() {
  nextTick(() => {
    if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight;
  });
}

function renderAssistant(content) {
  return renderMarkdown(content);
}

async function loadHistory() {
  controller.value?.abort();
  controller.value = null;
  busy.value = false;
  messages.value = [];
  try {
    const items = await getJson(
      `/api/history?session_id=${encodeURIComponent(sessionId.value)}`
    );
    messages.value = items.map((item) => ({
      role: item.role,
      content: item.content,
      createdAt: item.created_at,
      status: "",
      statusText: "",
      sources: null,
    }));
    scrollBottom();
  } catch (error) {
    app.toast(error.message, "error");
  }
}

async function send(question, addUser = true) {
  const input = question.trim();
  if (!input || busy.value) return;
  lastQuestion.value = input;
  if (addUser) {
    messages.value.push({
      role: "user",
      content: input,
      createdAt: new Date().toISOString(),
      status: "",
      statusText: "",
      sources: null,
    });
  }
  inputValue.value = "";
  autoResize();

  const answer = {
    role: "assistant",
    content: "",
    createdAt: new Date().toISOString(),
    status: ragMode.value === "off" ? "writing" : "retrieving",
    statusText: getThinkingStatusText(ragMode.value === "off" ? "writing" : "retrieving"),
    sources: null,
  };
  messages.value.push(answer);
  busy.value = true;
  controller.value = new AbortController();
  let fullText = "";

  try {
    await streamChat({
      input,
      sessionId: sessionId.value,
      ragMode: ragMode.value,
      signal: controller.value.signal,
      onEvent(event) {
        if (event.type === "status") {
          answer.statusText = event.content;
        }
        if (event.type === "sources") {
          answer.sources = event.sources;
        }
        if (event.type === "chunk") {
          answer.status = "writing";
          answer.statusText = getThinkingStatusText("writing");
          fullText += event.content;
          answer.content = fullText;
          scrollBottom();
        }
        if (event.type === "error") {
          throw new Error(event.content);
        }
      },
    });
    answer.status = "";
    answer.statusText = "";
    await app.loadSessions();
  } catch (error) {
    answer.status = "";
    answer.statusText = "";
    if (error.name === "AbortError") {
      if (!fullText) answer.content = "已停止生成。";
    } else {
      answer.content = fullText || `未能生成回答：${error.message}`;
      answer.error = true;
    }
  } finally {
    busy.value = false;
    controller.value = null;
    inputEl.value?.focus();
  }
}

function retry() {
  if (messages.value.length) messages.value.pop();
  send(lastQuestion.value, false);
}

function autoResize() {
  if (!inputEl.value) return;
  inputEl.value.style.height = "auto";
  inputEl.value.style.height = `${Math.min(inputEl.value.scrollHeight, 140)}px`;
}

function onSubmit() {
  send(inputValue.value);
}

function onKeydown(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    send(inputValue.value);
  }
}

function stop() {
  controller.value?.abort();
}

watch(sessionId, () => {
  loadHistory();
});

onMounted(() => {
  loadHistory();
  app.loadSessions();
});
</script>

<template>
  <section class="page chat-page">
    <div ref="scrollEl" class="chat-scroll">
      <div class="messages chat-records">
        <article
          v-for="(message, index) in messages"
          :key="index"
          class="message message-record"
          :class="[message.role, `message-record--${message.role}`]"
        >
          <div
            :class="message.role === 'assistant' ? 'answer-paper answer-body' : 'message-content'"
          >
            <div
              v-if="message.role === 'user'"
              class="message-text break-anywhere"
            >{{ message.content }}</div>
            <div
              v-else
              class="message-text break-anywhere"
              :class="{ 'has-error': message.error }"
              v-html="renderAssistant(message.content)"
            ></div>
            <div
              v-if="message.role === 'assistant' && message.status"
              class="message-state thinking-state"
            >
              <span>{{ message.statusText }}</span>
              <i></i><i></i><i></i>
            </div>
            <time class="message-time" :datetime="message.createdAt">
              {{ formatDisplayTime(message.createdAt) }}
            </time>
            <button
              v-if="message.error"
              class="retry-button"
              @click="retry"
            >
              重新生成
            </button>
          </div>
          <SourceBlock
            v-if="message.role === 'assistant'"
            class="citation-rail"
            :sources="message.sources"
          />
        </article>
      </div>

      <section v-if="isEmpty" class="chat-empty">
        <span class="empty-pack"><Icon name="pack" /></span>
        <h2>从你的资料里，拆出答案</h2>
        <p>我会优先检索你放进 Know包的内容。</p>
        <div class="prompt-suggestions">
          <button
            v-for="(text, index) in suggestions"
            :key="index"
            @click="send(text)"
          >
            {{ text }}
          </button>
        </div>
      </section>
    </div>

    <div class="composer-wrap">
      <div class="rag-control">
        <div class="rag-segment" role="radiogroup" aria-label="知识库检索模式">
          <label v-for="option in ragOptions" :key="option.value">
            <input
              type="radio"
              name="rag-mode"
              :value="option.value"
              :checked="ragMode === option.value"
              @change="app.setRagMode(option.value)"
            />
            <span>{{ option.label }}</span>
          </label>
        </div>
        <small>{{ RAG_MODE_HINTS[ragMode] }}</small>
      </div>
      <form class="composer" @submit.prevent="onSubmit">
        <textarea
          ref="inputEl"
          v-model="inputValue"
          rows="1"
          maxlength="4000"
          placeholder="向你的知识包提问…"
          @input="autoResize"
          @keydown="onKeydown"
        ></textarea>
        <button
          class="send-button"
          type="submit"
          :disabled="busy"
          aria-label="发送"
        >
          <Icon name="send" />
        </button>
        <button
          class="stop-button"
          :class="{ hidden: !busy }"
          type="button"
          @click="stop"
        >
          <Icon name="stop" />停止
        </button>
      </form>
      <small>Enter 发送 · Shift + Enter 换行</small>
    </div>
  </section>
</template>
