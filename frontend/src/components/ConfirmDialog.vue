<script setup>
import { nextTick, ref } from "vue";

import Icon from "./Icon.vue";

const props = defineProps({
  title: { type: String, default: "确认操作" },
  confirmText: { type: String, default: "确认删除" },
  danger: { type: Boolean, default: true },
});

const emit = defineEmits(["confirm", "cancel"]);

const open = ref(false);
const message = ref("");
const dialogEl = ref(null);

function show(text) {
  message.value = text;
  open.value = true;
  nextTick(() => dialogEl.value?.showModal());
}

function close(result) {
  open.value = false;
  if (dialogEl.value?.open) dialogEl.value.close();
  emit(result === "confirm" ? "confirm" : "cancel");
}

defineExpose({ show });
</script>

<template>
  <dialog ref="dialogEl" class="dialog">
    <form method="dialog" @submit.prevent="close($event.submitter?.value)">
      <span class="dialog-icon"><Icon name="trash" /></span>
      <h2>{{ title }}</h2>
      <p>{{ message }}</p>
      <div>
        <button value="cancel" @click="close('cancel')">取消</button>
        <button value="confirm" :class="{ danger }" @click="close('confirm')">
          {{ confirmText }}
        </button>
      </div>
    </form>
  </dialog>
</template>
