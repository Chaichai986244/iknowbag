export function beginNewConversation({
  abortCurrent,
  createSessionId,
  saveSessionId,
  setTitle,
  clearMessages,
  showEmpty,
  refreshSessions,
  requestChatPage,
}) {
  abortCurrent();
  const sessionId = createSessionId();
  saveSessionId(sessionId);
  setTitle("新对话");
  clearMessages();
  showEmpty();
  requestChatPage();
  refreshSessions();
  return sessionId;
}

export function shouldResetAfterSessionDelete(deletedSessionId, currentSessionId) {
  return deletedSessionId === currentSessionId;
}

export function selectConversation({
  session,
  saveSessionId,
  setTitle,
  requestChatPage,
}) {
  saveSessionId(session.session_id);
  setTitle(session.title);
  requestChatPage();
  return session.session_id;
}

export function formatDisplayTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (number) => String(number).padStart(2, "0");
  return `${pad(date.getMonth() + 1)}/${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function getThinkingStatusText(state) {
  const labels = {
    retrieving: "正在检索你的资料",
    grounding: "已找到参考资料，正在组织回答",
    writing: "正在生成回答",
  };
  return labels[state] || labels.retrieving;
}

export function normalizeRagMode(value) {
  if (value === "false") return "off";
  if (value === "true") return "force";
  return ["off", "force", "auto"].includes(value) ? value : "auto";
}
