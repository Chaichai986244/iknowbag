<script setup>
import { storeToRefs } from "pinia";

import { useAppStore } from "../stores/app";

const app = useAppStore();
const { toasts } = storeToRefs(app);
</script>

<template>
  <div class="toast-region" aria-live="polite">
    <div
      v-for="item in toasts"
      :key="item.id"
      class="toast"
      :class="{ error: item.type === 'error' }"
    >
      {{ item.message }}
    </div>
  </div>
</template>
