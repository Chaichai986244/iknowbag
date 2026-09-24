import { getJson, putJson } from "./api.js?v=20260803l";
import { encodeSeparatorLines, settingsPayloadFromForm } from "./settings-actions.mjs?v=20260803l";


export function initSettings({ toast, onSettingsSaved }) {
  const nodes = {
    form: document.querySelector("#settings-form"),
    chunkSize: document.querySelector("#setting-chunk-size"),
    chunkOverlap: document.querySelector("#setting-chunk-overlap"),
    maxSplit: document.querySelector("#setting-max-split"),
    topK: document.querySelector("#setting-top-k"),
    separators: document.querySelector("#setting-separators"),
    weatherLocation: document.querySelector("#setting-weather-location"),
    agentWeather: document.querySelector("#setting-agent-weather"),
    status: document.querySelector("#settings-status"),
    save: document.querySelector("#save-settings"),
  };
  const requiredNodes = Object.values(nodes);
  if (requiredNodes.some((node) => !node)) {
    return { refresh() {} };
  }

  function setStatus(message) {
    nodes.status.textContent = message;
  }

  function fill(settings) {
    nodes.chunkSize.value = settings.chunk_size;
    nodes.chunkOverlap.value = settings.chunk_overlap;
    nodes.maxSplit.value = settings.max_split;
    nodes.topK.value = settings.top_k;
    nodes.separators.value = encodeSeparatorLines(settings.separators);
    nodes.weatherLocation.value = settings.weather?.default_location || "北京";
    nodes.agentWeather.checked = Boolean(settings.agent_tools?.weather);
  }

  async function refresh() {
    try {
      const settings = await getJson("/api/settings");
      fill(settings);
      setStatus("当前设置已读取。");
    } catch (error) {
      setStatus("设置读取失败。");
      toast(error.message, "error");
    }
  }

  nodes.form.addEventListener("submit", async (event) => {
    event.preventDefault();
    nodes.save.disabled = true;
    setStatus("正在保存设置…");
    try {
      const payload = settingsPayloadFromForm({
        chunk_size: nodes.chunkSize.value,
        chunk_overlap: nodes.chunkOverlap.value,
        max_split: nodes.maxSplit.value,
        top_k: nodes.topK.value,
        separators: nodes.separators.value,
        weather_default_location: nodes.weatherLocation.value,
        agent_weather_enabled: nodes.agentWeather.checked,
      });
      const settings = await putJson("/api/settings", payload);
      fill(settings);
      setStatus("设置已保存；新上传资料会使用新的切分规则。");
      toast("设置已保存");
      onSettingsSaved?.();
    } catch (error) {
      setStatus(error.message);
      toast(error.message, "error");
    } finally {
      nodes.save.disabled = false;
    }
  });

  refresh();
  return { refresh };
}
