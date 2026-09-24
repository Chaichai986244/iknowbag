<script setup>
import { ref } from "vue";

defineProps({
  sources: { type: Array, default: () => [] },
});

const expanded = ref(false);
</script>

<template>
  <div v-if="sources?.length" class="source-block">
    <div class="source-summary">
      <span>已参考 {{ sources.length }} 个片段</span>
      <button type="button" @click="expanded = !expanded">
        {{ expanded ? "收起来源" : "查看来源" }}
      </button>
    </div>
    <div v-show="expanded" class="source-tags">
      <div
        v-for="(source, index) in sources"
        :key="index"
        class="source-tag"
      >
        <span class="source-index">{{ index + 1 }}</span>
        <span
          class="source-title break-anywhere"
          :title="source.page ? `${source.source} · 第 ${source.page} 页` : source.source"
        >
          {{ source.page ? `${source.source} · 第 ${source.page} 页` : source.source }}
        </span>
      </div>
    </div>
  </div>
</template>
