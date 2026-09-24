<script setup>
import { onMounted, ref } from "vue";

import ConfirmDialog from "../components/ConfirmDialog.vue";
import Icon from "../components/Icon.vue";
import { deleteJson, getJson, uploadFile } from "../api";
import { formatFileSize, validateKnowledgeFile } from "../utils/format";
import { useAppStore } from "../stores/app";

const app = useAppStore();

const summary = ref("正在读取资料…");
const total = ref("");
const sources = ref([]);
const selectedFile = ref(null);
const uploading = ref(false);
const status = ref("");

const fileInput = ref(null);
const deleteDialog = ref(null);
const pendingDelete = ref(null);

function clearFile() {
  selectedFile.value = null;
  if (fileInput.value) fileInput.value.value = "";
  uploading.value = false;
  status.value = "";
}

function selectFile(file) {
  const result = validateKnowledgeFile(file);
  if (!result.ok) {
    app.toast(result.message, "error");
    return;
  }
  selectedFile.value = file;
  status.value = "";
}

function onDrop(event) {
  event.preventDefault();
  selectFile(event.dataTransfer?.files?.[0]);
}

function fileMeta(file) {
  return `${formatFileSize(file.size)} · ${file.name.split(".").pop().toUpperCase()}`;
}

function itemMeta(item) {
  return `${String(item.file_type).toUpperCase()} · ${item.chunk_count} 个内容片段`;
}

async function refresh() {
  try {
    const data = await getJson("/api/knowledge");
    summary.value = `${data.source_count} 份资料 · ${data.document_count} 个内容片段`;
    total.value = `${data.source_count} 份`;
    app.setKnowledgeCount(data.source_count);
    sources.value = data.source_details;
  } catch (error) {
    app.toast(error.message, "error");
  }
}

function requestDelete(item) {
  pendingDelete.value = item;
  deleteDialog.value?.show(
    `“${item.source}”包含 ${item.chunk_count} 个内容片段，删除后无法撤销。`
  );
}

async function confirmDelete() {
  const item = pendingDelete.value;
  pendingDelete.value = null;
  if (!item) return;
  try {
    const result = await deleteJson("/api/knowledge/source", { source: item.source });
    app.toast(result.message);
    await refresh();
  } catch (error) {
    app.toast(error.message, "error");
  }
}

async function upload() {
  if (!selectedFile.value || uploading.value) return;
  uploading.value = true;
  status.value = "正在处理资料…";
  try {
    const result = await uploadFile(selectedFile.value);
    app.toast(result.message);
    clearFile();
    await refresh();
  } catch (error) {
    if (error.message.includes("已存在")) {
      status.value = "这份资料已经在包里了。";
    } else if (error.message.includes("OCR")) {
      status.value = "这份 PDF 没有可提取的文字，请先进行 OCR。";
    } else {
      status.value = error.message;
    }
    uploading.value = false;
  }
}

onMounted(refresh);
</script>

<template>
  <section class="page knowledge-page">
    <div class="page-intro">
      <h2>管理知识包</h2>
      <p>{{ summary }}</p>
    </div>

    <section class="upload-section">
      <div>
        <h3>放进新资料</h3>
        <p>支持 PDF 和 UTF-8 TXT，单个文件不超过 30 MB。</p>
      </div>
      <label
        class="drop-zone"
        for="file-input"
        @dragenter.prevent
        @dragover.prevent
        @dragleave.prevent
        @drop.prevent="onDrop"
      >
        <Icon name="upload" />
        <strong>选择或拖放文件</strong>
        <span>PDF / TXT</span>
      </label>
      <input
        id="file-input"
        ref="fileInput"
        type="file"
        accept=".pdf,.txt"
        hidden
        @change="selectFile(fileInput.files[0])"
      />
      <div v-if="selectedFile" class="selected-file">
        <Icon name="file" />
        <span class="selected-file-info">
          <strong class="truncate" :title="selectedFile.name">{{ selectedFile.name }}</strong>
          <small>{{ fileMeta(selectedFile) }}</small>
        </span>
        <button class="icon-button" aria-label="取消选择" @click="clearFile">
          <Icon name="close" />
        </button>
      </div>
      <button
        class="upload-button"
        :disabled="!selectedFile || uploading"
        @click="upload"
      >
        <Icon name="pack" />
        <span>{{ uploading ? "正在处理…" : "装入知识包" }}</span>
      </button>
      <p class="upload-status" aria-live="polite">{{ status }}</p>
    </section>

    <section class="sources-section">
      <div class="section-title">
        <h3>包里的资料</h3>
        <span>{{ total }}</span>
      </div>
      <div class="source-list document-cabinet">
        <div v-if="!sources.length" class="empty-source">
          知识包还是空的，先放进一份 PDF 或 TXT。
        </div>
        <article
          v-for="item in sources"
          :key="item.source"
          class="source-item document-row"
        >
          <Icon name="file" />
          <span class="source-info document-name">
            <strong class="truncate" :title="item.source">{{ item.source }}</strong>
            <small>{{ itemMeta(item) }}</small>
          </span>
          <button
            class="icon-button delete-source document-actions"
            aria-label="删除资料"
            @click="requestDelete(item)"
          >
            <Icon name="trash" />
          </button>
        </article>
      </div>
    </section>

    <ConfirmDialog
      ref="deleteDialog"
      title="从知识包移除？"
      @confirm="confirmDelete"
    />
  </section>
</template>
