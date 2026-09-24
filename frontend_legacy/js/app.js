import { getJson } from "./api.js?v=20260803l";
import { initChat } from "./chat.js?v=20260803l";
import { initKnowledge } from "./knowledge.js?v=20260803l";
import { initSettings } from "./settings.js?v=20260803l";

const sidebar = document.querySelector("#mobile-nav");
const backdrop = document.querySelector("#drawer-backdrop");
const pageTitle = document.querySelector("#page-title");
const pageSubtitle = document.querySelector("#page-subtitle");
let chatTitle = "新对话";
const weatherNodes = {
  card: document.querySelector("#sidebar-weather"),
  title: document.querySelector("#weather-title"),
  detail: document.querySelector("#weather-detail"),
};

function toast(message, type = "success") {
  const node = document.createElement("div"); node.className = `toast ${type === "error" ? "error" : ""}`; node.textContent = message;
  document.querySelector("#toast-region").append(node); setTimeout(() => node.remove(), 4200);
}

function navigate(name) {
  if (name === "help") name = "settings";
  document.querySelectorAll(".page").forEach((page) => page.classList.toggle("active", page.id === `page-${name}`));
  document.querySelectorAll("[data-page]").forEach((button) => button.classList.toggle("active", button.dataset.page === name));
  const labels = { chat: [chatTitle, "向你的资料提问"], knowledge: ["知识库", "整理和更新 Know包"], settings: ["设置", "调整切分和检索参数"] };
  if (!labels[name]) return;
  [pageTitle.textContent, pageSubtitle.textContent] = labels[name];
  sidebar.classList.remove("open"); backdrop.classList.remove("open");
  if (name === "knowledge") knowledge.refresh();
  if (name === "settings") settings.refresh();
}

function setWeatherCard(title, detail, state = "") {
  weatherNodes.title.textContent = title;
  weatherNodes.detail.textContent = detail;
  weatherNodes.card.dataset.state = state;
  weatherNodes.card.title = `${title}\n${detail}`;
}

async function loadSidebarWeather(location = "") {
  try {
    const query = location ? `?location=${encodeURIComponent(location)}` : "";
    const weather = await getJson(`/api/weather/current${query}`);
    setWeatherCard(
      `${weather.location || "当前位置"} · ${weather.text || "天气"}`,
      `${weather.temp || "-"}℃ · 体感 ${weather.feels_like || "-"}℃ · 湿度 ${weather.humidity || "-"}%`,
      "ready"
    );
  } catch (error) {
    setWeatherCard("天气未就绪", error.message || "请在设置中配置和风天气", "error");
  }
}

function initSidebarWeather() {
  if (!navigator.geolocation) {
    loadSidebarWeather();
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (position) => {
      const { longitude, latitude } = position.coords;
      loadSidebarWeather(`${longitude.toFixed(2)},${latitude.toFixed(2)}`);
    },
    () => loadSidebarWeather(),
    { timeout: 5000, maximumAge: 1000 * 60 * 20 }
  );
}

document.querySelectorAll("[data-page]").forEach((button) => button.addEventListener("click", () => navigate(button.dataset.page)));
document.querySelector("#menu-button").addEventListener("click", () => { sidebar.classList.add("open"); backdrop.classList.add("open"); });
backdrop.addEventListener("click", () => { sidebar.classList.remove("open"); backdrop.classList.remove("open"); });
document.addEventListener("chat-title", (event) => {
  chatTitle = event.detail;
  if (document.querySelector("#page-chat").classList.contains("active")) {
    pageTitle.textContent = chatTitle;
  }
});

const knowledge = initKnowledge({ toast, onCountChange(count) {
  document.querySelector("#side-source-count").textContent = count;
  document.querySelector("#top-source-count").textContent = `${count} 份资料`;
} });
const settings = initSettings({ toast, onSettingsSaved: () => loadSidebarWeather() });
initChat({ toast, onChatRequested: () => navigate("chat") });
initSidebarWeather();
