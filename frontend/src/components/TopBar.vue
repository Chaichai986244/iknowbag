<script setup>
import { storeToRefs } from "pinia";

import Icon from "./Icon.vue";
import { useAppStore } from "../stores/app";

const app = useAppStore();
const { chatTitle, currentPage, knowledgeCount } = storeToRefs(app);

const subtitles = {
  chat: "向你的资料提问",
  knowledge: "整理和更新 Know包",
  settings: "调整切分和检索参数",
};
</script>

<template>
  <header class="topbar">
    <button
      class="icon-button mobile-only"
      aria-label="打开导航"
      @click="app.toggleDrawer()"
    >
      <Icon name="menu" />
    </button>
    <div>
      <h1>
        {{
          currentPage === "chat"
            ? chatTitle
            : currentPage === "knowledge"
              ? "知识库"
              : "设置"
        }}
      </h1>
      <p>{{ subtitles[currentPage] }}</p>
    </div>
    <button class="library-shortcut" @click="app.navigate('knowledge')">
      <Icon name="library" />
      <span>{{ knowledgeCount }} 份资料</span>
    </button>
  </header>
</template>
