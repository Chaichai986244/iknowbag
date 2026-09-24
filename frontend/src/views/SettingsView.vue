<script setup>
import { onMounted, reactive, ref } from "vue";

import Icon from "../components/Icon.vue";
import { getJson, putJson } from "../api";
import { useAppStore } from "../stores/app";

const app = useAppStore();

const form = reactive({
  chunk_size: "",
  chunk_overlap: "",
  max_split: "",
  top_k: "",
  separators: "",
  weather_default_location: "北京",
  agent_weather_enabled: true,
});
const status = ref("正在读取设置…");
const saving = ref(false);

const visibleSeparatorLabels = new Map([
  ["\\n\\n", "\n\n"],
  ["\\n", "\n"],
  ["\\t", "\t"],
  ["空格", " "],
]);

function decodeSeparatorLines(value) {
  return String(value || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => visibleSeparatorLabels.get(line) ?? line);
}

const separatorLabels = new Map([
  ["\n\n", "\\n\\n"],
  ["\n", "\\n"],
  ["\t", "\\t"],
  [" ", "空格"],
]);

function encodeSeparatorLines(separators) {
  return (separators || [])
    .map((separator) => separatorLabels.get(separator) ?? separator)
    .join("\n");
}

function fill(settings) {
  form.chunk_size = settings.chunk_size;
  form.chunk_overlap = settings.chunk_overlap;
  form.max_split = settings.max_split;
  form.top_k = settings.top_k;
  form.separators = encodeSeparatorLines(settings.separators);
  form.weather_default_location = settings.weather?.default_location || "北京";
  form.agent_weather_enabled = Boolean(settings.agent_tools?.weather);
}

async function refresh() {
  try {
    const settings = await getJson("/api/settings");
    fill(settings);
    status.value = "当前设置已读取。";
  } catch (error) {
    status.value = "设置读取失败。";
    app.toast(error.message, "error");
  }
}

async function save() {
  saving.value = true;
  status.value = "正在保存设置…";
  try {
    const payload = {
      chunk_size: Number.parseInt(form.chunk_size, 10),
      chunk_overlap: Number.parseInt(form.chunk_overlap, 10),
      max_split: Number.parseInt(form.max_split, 10),
      top_k: Number.parseInt(form.top_k, 10),
      separators: decodeSeparatorLines(form.separators),
      weather: { default_location: form.weather_default_location.trim() },
      agent_tools: { weather: Boolean(form.agent_weather_enabled) },
    };
    const settings = await putJson("/api/settings", payload);
    fill(settings);
    status.value = "设置已保存；新上传资料会使用新的切分规则。";
    app.toast("设置已保存");
    app.loadWeather();
  } catch (error) {
    status.value = error.message;
    app.toast(error.message, "error");
  } finally {
    saving.value = false;
  }
}

onMounted(refresh);
</script>

<template>
  <section class="page settings-page">
    <div class="page-intro">
      <h2>设置</h2>
      <p>管理知识库检索、天气显示，以及 Agent 可以调用哪些工具。</p>
    </div>

    <form class="settings-panel" @submit.prevent="save">
      <section class="settings-group settings-group-hero">
        <div class="settings-group-title">
          <h3>文本切分</h3>
          <p>这些参数会影响之后上传的 PDF / TXT。</p>
        </div>
        <label class="setting-row">
          <span class="setting-copy">
            <span class="setting-label">分块长度</span>
            <small class="setting-hint">建议 500-1500。</small>
          </span>
          <span class="setting-control">
            <input
              v-model="form.chunk_size"
              type="number"
              min="100"
              max="8000"
              step="50"
              required
            />
          </span>
        </label>
        <label class="setting-row">
          <span class="setting-copy">
            <span class="setting-label">重叠长度</span>
            <small class="setting-hint">必须小于分块长度。</small>
          </span>
          <span class="setting-control">
            <input
              v-model="form.chunk_overlap"
              type="number"
              min="0"
              max="4000"
              step="10"
              required
            />
          </span>
        </label>
        <label class="setting-row">
          <span class="setting-copy">
            <span class="setting-label">超过多少字符才切分</span>
            <small class="setting-hint">短文本低于这个值会整段入库。</small>
          </span>
          <span class="setting-control">
            <input
              v-model="form.max_split"
              type="number"
              min="100"
              max="20000"
              step="50"
              required
            />
          </span>
        </label>
      </section>

      <section class="settings-group">
        <div class="settings-group-title">
          <h3>分隔符</h3>
          <p>按从优先到兜底的顺序填写，每行一个。</p>
        </div>
        <label class="setting-row setting-row-wide">
          <span class="setting-copy">
            <span class="setting-label">分割规则</span>
            <small class="setting-hint">可写 \n\n、\n、空格、\t，也可以写普通符号。</small>
          </span>
          <span class="setting-control">
            <textarea
              v-model="form.separators"
              rows="5"
              spellcheck="false"
              required
            ></textarea>
          </span>
        </label>
      </section>

      <section class="settings-group">
        <div class="settings-group-title">
          <h3>检索</h3>
          <p>这个参数会影响下一次提问。</p>
        </div>
        <label class="setting-row">
          <span class="setting-copy">
            <span class="setting-label">参考片段数 top_k</span>
            <small class="setting-hint">越大参考越多，但回答会更慢。</small>
          </span>
          <span class="setting-control">
            <input
              v-model="form.top_k"
              type="number"
              min="1"
              max="30"
              step="1"
              required
            />
          </span>
        </label>
      </section>

      <section class="settings-group tool-config-group">
        <div class="settings-group-title">
          <h3>天气显示</h3>
          <p>用于侧栏天气卡片，也供天气工具读取。API Key 固定在后端，不在前端填写。</p>
        </div>
        <label class="setting-row">
          <span class="setting-copy">
            <span class="setting-label">默认位置</span>
            <small class="setting-hint">浏览器无法定位时使用这个位置。</small>
          </span>
          <span class="setting-control">
            <input
              v-model="form.weather_default_location"
              type="text"
              placeholder="例如：北京 / 上海 / 成都"
            />
          </span>
        </label>
      </section>

      <section class="settings-group agent-tools-group">
        <div class="settings-group-title">
          <h3>Agent 工具权限</h3>
          <p>这里只控制 Agent 在对话中能不能调用工具，不影响页面上的天气显示。</p>
        </div>
        <label class="setting-row tool-switch">
          <span class="setting-copy">
            <span class="setting-label">天气工具</span>
            <small class="setting-hint">允许 Agent 根据问题自主查询指定位置天气。</small>
          </span>
          <span class="setting-control switch-control">
            <input v-model="form.agent_weather_enabled" type="checkbox" />
            <span class="switch-track"></span>
          </span>
        </label>
      </section>

      <div class="settings-actions">
        <p aria-live="polite">{{ status }}</p>
        <button type="submit" :disabled="saving">
          <Icon name="settings" />
          {{ saving ? "保存中…" : "保存设置" }}
        </button>
      </div>
    </form>
  </section>
</template>
