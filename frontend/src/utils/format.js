// 通用格式化与校验工具（迁移自原前端 utils.js / chat-actions.mjs）。

export const MAX_FILE_SIZE = 30 * 1024 * 1024;

export function validateKnowledgeFile(file) {
  const suffix = String(file?.name || "").split(".").pop().toLowerCase();
  if (!["pdf", "txt"].includes(suffix)) {
    return { ok: false, message: "只能放入 PDF 或 TXT 文件。" };
  }
  if (Number(file.size) > MAX_FILE_SIZE) {
    return { ok: false, message: "文件不能超过 30 MB。" };
  }
  return { ok: true, message: "" };
}

export function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

export function formatDisplayTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (number) => String(number).padStart(2, "0");
  return `${pad(date.getMonth() + 1)}/${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function normalizeRagMode(value) {
  if (value === "false") return "off";
  if (value === "true") return "force";
  return ["off", "force", "auto"].includes(value) ? value : "auto";
}

// 生成会话 UUID。
// 说明：crypto.randomUUID 仅在 HTTPS 或 localhost 的安全上下文中可用，
// 公网纯 HTTP 访问时必须降级为本地随机生成，否则应用无法初始化。
export function createSessionId() {
  if (
    typeof crypto !== "undefined" &&
    typeof crypto.randomUUID === "function"
  ) {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (char) => {
    const random = (Math.random() * 16) | 0;
    const value = char === "x" ? random : (random & 0x3) | 0x8;
    return value.toString(16);
  });
}

export const RAG_MODE_HINTS = {
  off: "不调用知识库，按普通对话回答",
  force: "检索后强制参考资料回答",
  auto: "先检索，再由 Agent 筛选资料",
};

export function getThinkingStatusText(state) {
  const labels = {
    retrieving: "正在检索你的资料",
    grounding: "已找到参考资料，正在组织回答",
    writing: "正在生成回答",
  };
  return labels[state] || labels.retrieving;
}
