import { defineStore } from "pinia";
import { reactive, ref } from "vue";

import { getJson } from "../api";
import { createSessionId, normalizeRagMode } from "../utils/format";

export const useAppStore = defineStore("app", () => {
  // ---------- 页面导航 ----------
  const currentPage = ref("chat");
  const chatTitle = ref("新对话");
  const drawerOpen = ref(false);

  function navigate(name) {
    if (name === "help") name = "settings";
    currentPage.value = name;
    drawerOpen.value = false;
  }

  function toggleDrawer() {
    drawerOpen.value = !drawerOpen.value;
  }

  function closeDrawer() {
    drawerOpen.value = false;
  }

  // ---------- Toast ----------
  let toastCounter = 0;
  const toasts = ref([]);

  function toast(message, type = "success") {
    const id = ++toastCounter;
    toasts.value.push({ id, message, type });
    setTimeout(() => {
      toasts.value = toasts.value.filter((item) => item.id !== id);
    }, 4200);
  }

  // ---------- 会话 ----------
  const sessionId = ref(
    localStorage.getItem("knowbao-session") || createSessionId()
  );

  function setSessionId(value) {
    sessionId.value = value;
    localStorage.setItem("knowbao-session", value);
  }

  // ---------- RAG 模式 ----------
  const ragMode = ref(
    normalizeRagMode(localStorage.getItem("knowbao-rag-mode"))
  );

  function setRagMode(value) {
    ragMode.value = normalizeRagMode(value);
    localStorage.setItem("knowbao-rag-mode", ragMode.value);
  }

  // ---------- 会话列表 ----------
  const sessions = ref([]);

  async function loadSessions() {
    try {
      sessions.value = await getJson("/api/sessions");
    } catch (error) {
      toast(error.message, "error");
    }
  }

  // ---------- 知识库统计 ----------
  const knowledgeCount = ref(0);

  function setKnowledgeCount(count) {
    knowledgeCount.value = Number(count) || 0;
  }

  function selectSession(session) {
    setSessionId(session.session_id);
    chatTitle.value = session.title || "新对话";
    navigate("chat");
  }

  function startNewConversation() {
    setSessionId(createSessionId());
    chatTitle.value = "新对话";
    navigate("chat");
  }

  // ---------- 天气 ----------
  const weather = reactive({
    state: "",
    title: "读取天气…",
    detail: "正在获取当前位置",
    // 用于天气卡片 UI 的原始字段
    city: "",
    text: "",
    temp: "",
    feels_like: "",
    humidity: "",
  });

  function setWeatherCard(title, detail, state = "") {
    weather.title = title;
    weather.detail = detail;
    weather.state = state;
  }

  async function loadWeather(location = "") {
    try {
      const query = location
        ? `?location=${encodeURIComponent(location)}`
        : "";
      const data = await getJson(`/api/weather/current${query}`);
      // 提取纯城市名（去掉 "省 · " 前缀）
      const raw = data.location || "";
      const city = raw.includes("·") ? raw.split("·").pop().trim() : raw;
      weather.city = city;
      weather.text = data.text || "";
      weather.temp = data.temp || "";
      weather.feels_like = data.feels_like || "";
      weather.humidity = data.humidity || "";
      weather.state = "ready";
      setWeatherCard(
        `${raw || "当前位置"} · ${data.text || "天气"}`,
        `${data.temp || "-"}℃ · 体感 ${data.feels_like || "-"}℃ · 湿度 ${data.humidity || "-"}%`,
        "ready"
      );
    } catch (error) {
      weather.city = "";
      weather.text = "";
      weather.temp = "";
      weather.feels_like = "";
      weather.humidity = "";
      weather.state = "error";
      setWeatherCard(
        "天气未就绪",
        error.message || "请在设置中配置和风天气",
        "error"
      );
    }
  }

  function initWeather() {
    if (!navigator.geolocation) {
      loadWeather();
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { longitude, latitude } = position.coords;
        loadWeather(`${longitude.toFixed(2)},${latitude.toFixed(2)}`);
      },
      () => loadWeather(),
      { timeout: 5000, maximumAge: 1000 * 60 * 20 }
    );
  }

  return {
    currentPage,
    chatTitle,
    drawerOpen,
    navigate,
    toggleDrawer,
    closeDrawer,
    toasts,
    toast,
    sessionId,
    setSessionId,
    ragMode,
    setRagMode,
    sessions,
    loadSessions,
    knowledgeCount,
    setKnowledgeCount,
    selectSession,
    startNewConversation,
    weather,
    loadWeather,
    initWeather,
  };
});
