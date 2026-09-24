<script setup>
import { onMounted } from "vue";
import { storeToRefs } from "pinia";

import ChatView from "./views/ChatView.vue";
import KnowledgeView from "./views/KnowledgeView.vue";
import SettingsView from "./views/SettingsView.vue";
import Sidebar from "./components/Sidebar.vue";
import ToastRegion from "./components/ToastRegion.vue";
import TopBar from "./components/TopBar.vue";
import { useAppStore } from "./stores/app";

const app = useAppStore();
const { currentPage, drawerOpen } = storeToRefs(app);

onMounted(() => {
  app.initWeather();
  app.loadSessions();
});
</script>

<template>
  <div class="app-shell">
    <Sidebar :class="{ open: drawerOpen }" />
    <div
      class="drawer-backdrop"
      :class="{ open: drawerOpen }"
      @click="app.closeDrawer()"
    ></div>

    <main class="workspace">
      <TopBar />
      <ChatView
        v-show="currentPage === 'chat'"
        :class="{ active: currentPage === 'chat' }"
      />
      <KnowledgeView
        v-show="currentPage === 'knowledge'"
        :class="{ active: currentPage === 'knowledge' }"
      />
      <SettingsView
        v-show="currentPage === 'settings'"
        :class="{ active: currentPage === 'settings' }"
      />
    </main>
  </div>

  <ToastRegion />
</template>
