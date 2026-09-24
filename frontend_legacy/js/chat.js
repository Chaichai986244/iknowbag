import { deleteJson, getJson, streamChat } from "./api.js?v=20260803l";
import { renderMarkdown } from "./utils.js?v=20260803l";
import {
  beginNewConversation,
  formatDisplayTime,
  getThinkingStatusText,
  normalizeRagMode,
  selectConversation,
  shouldResetAfterSessionDelete,
} from "./chat-actions.mjs?v=20260803l";

function messageNode(role, content = "", createdAt = new Date().toISOString()) {
  const article = document.createElement("article");
  article.className = `message ${role}`;
  const contentNode = document.createElement("div");
  contentNode.className = role === "assistant" ? "answer-paper" : "message-content";
  const textNode = document.createElement("div");
  textNode.className = "message-text";
  if (role === "assistant") textNode.innerHTML = renderMarkdown(content);
  else textNode.textContent = content;
  const timeNode = document.createElement("time");
  timeNode.className = "message-time";
  timeNode.dateTime = createdAt || "";
  timeNode.textContent = formatDisplayTime(createdAt);
  contentNode.append(textNode);
  contentNode.append(timeNode);
  article.append(contentNode);
  return { article, contentNode, textNode };
}

export function initChat({ toast, onChatRequested }) {
  const nodes = {
    messages: document.querySelector("#messages"),
    empty: document.querySelector("#chat-empty"),
    scroll: document.querySelector("#chat-scroll"),
    form: document.querySelector("#composer"),
    input: document.querySelector("#chat-input"),
    send: document.querySelector("#send-button"),
    stop: document.querySelector("#stop-button"),
    ragModes: document.querySelectorAll('input[name="rag-mode"]'),
    ragHint: document.querySelector("#rag-hint"),
    conversations: document.querySelector("#conversation-list"),
    newChat: document.querySelector("#new-chat"),
    title: document.querySelector("#page-title"),
    deleteDialog: document.querySelector("#delete-chat-dialog"),
    deleteMessage: document.querySelector("#delete-chat-message"),
  };
  let sessionId = localStorage.getItem("knowbao-session") || crypto.randomUUID();
  let ragMode = normalizeRagMode(localStorage.getItem("knowbao-rag-mode"));
  let controller = null;
  let pendingDeleteSession = null;

  function syncRagToggle() {
    nodes.ragModes.forEach((node) => {
      node.checked = node.value === ragMode;
    });
    const hints = {
      off: "不调用知识库，按普通对话回答",
      force: "检索后强制参考资料回答",
      auto: "先检索，再由 Agent 筛选资料",
    };
    nodes.ragHint.textContent = hints[ragMode];
  }

  function scrollBottom() { nodes.scroll.scrollTop = nodes.scroll.scrollHeight; }
  function setBusy(value) {
    nodes.send.disabled = value;
    nodes.stop.classList.toggle("hidden", !value);
    nodes.send.classList.toggle("hidden", value);
  }
  function showEmpty(value) { nodes.empty.classList.toggle("hidden", !value); }

  function append(role, content, createdAt) {
    const item = messageNode(role, content, createdAt);
    nodes.messages.append(item.article);
    showEmpty(false);
    scrollBottom();
    return item;
  }

  function startNewConversation() {
    sessionId = beginNewConversation({
      abortCurrent: () => controller?.abort(),
      createSessionId: () => crypto.randomUUID(),
      saveSessionId: (value) => localStorage.setItem("knowbao-session", value),
      setTitle: (value) => {
        nodes.title.textContent = value;
        document.dispatchEvent(new CustomEvent("chat-title", { detail: value }));
      },
      clearMessages: () => nodes.messages.replaceChildren(),
      showEmpty: () => showEmpty(true),
      requestChatPage: onChatRequested,
      refreshSessions: loadSessions,
    });
  }

  async function loadHistory() {
    nodes.messages.replaceChildren();
    try {
      const messages = await getJson(`/api/history?session_id=${encodeURIComponent(sessionId)}`);
      messages.forEach((item) => append(item.role, item.content, item.created_at));
      showEmpty(messages.length === 0);
    } catch (error) {
      showEmpty(true);
      toast(error.message, "error");
    }
  }

  async function loadSessions() {
    try {
      const sessions = await getJson("/api/sessions");
      nodes.conversations.replaceChildren();
      const currentSession = sessions.find(
        (session) => session.session_id === sessionId
      );
      if (currentSession) {
        nodes.title.textContent = currentSession.title;
        document.dispatchEvent(
          new CustomEvent("chat-title", { detail: currentSession.title })
        );
      }
      sessions.forEach((session) => {
        const row = document.createElement("div");
        row.className = "conversation-row";
        const button = document.createElement("button");
        button.className = `conversation-item${session.session_id === sessionId ? " active" : ""}`;
        const updatedTime = formatDisplayTime(session.updated_at);
        button.innerHTML = "<span></span><time></time>";
        button.querySelector("span").textContent = session.title;
        button.querySelector("time").dateTime = session.updated_at || "";
        button.querySelector("time").textContent = updatedTime ? `更新于 ${updatedTime}` : "";
        button.title = updatedTime ? `${session.title}\n更新于 ${updatedTime}` : session.title;
        button.addEventListener("click", async () => {
          sessionId = selectConversation({
            session,
            saveSessionId: (value) => localStorage.setItem("knowbao-session", value),
            setTitle: (value) => {
              nodes.title.textContent = value;
              document.dispatchEvent(new CustomEvent("chat-title", { detail: value }));
            },
            requestChatPage: onChatRequested,
          });
          await loadHistory();
          await loadSessions();
        });
        const deleteButton = document.createElement("button");
        deleteButton.className = "icon-button delete-conversation";
        deleteButton.type = "button";
        deleteButton.title = `删除对话：${session.title}`;
        deleteButton.setAttribute("aria-label", `删除对话：${session.title}`);
        deleteButton.innerHTML = '<svg aria-hidden="true"><use href="#i-trash"></use></svg>';
        deleteButton.addEventListener("click", (event) => {
          event.stopPropagation();
          pendingDeleteSession = session;
          nodes.deleteMessage.textContent = `确定删除“${session.title}”吗？删除后无法恢复。`;
          nodes.deleteDialog.showModal();
        });
        row.append(button, deleteButton);
        nodes.conversations.append(row);
      });
    } catch (error) { toast(error.message, "error"); }
  }

  function renderSources(container, sources) {
    if (!sources?.length) return;
    let block = container.querySelector(".source-block");
    if (!block) {
      block = document.createElement("div");
      block.className = "source-block";
      block.innerHTML = '<div class="source-summary"><span></span><button type="button"></button></div><div class="source-tags hidden"></div>';
      container.append(block);
    }
    const summary = block.querySelector(".source-summary span");
    const toggle = block.querySelector(".source-summary button");
    const tags = block.querySelector(".source-tags");
    summary.textContent = `已参考 ${sources.length} 个片段`;
    toggle.textContent = tags.classList.contains("hidden") ? "查看来源" : "收起来源";
    toggle.onclick = () => {
      tags.classList.toggle("hidden");
      toggle.textContent = tags.classList.contains("hidden") ? "查看来源" : "收起来源";
      scrollBottom();
    };
    tags.replaceChildren();
    sources.forEach((source) => {
      const tag = document.createElement("span");
      tag.className = "source-tag";
      tag.textContent = source.page ? `${source.source} · 第 ${source.page} 页` : source.source;
      tags.append(tag);
    });
  }

  function placeThinkingState(answer, state) {
    const sourceBlock = answer.contentNode.querySelector(".source-block");
    const timeNode = answer.contentNode.querySelector(".message-time");
    if (sourceBlock) {
      sourceBlock.after(state);
    } else {
      answer.contentNode.insertBefore(state, timeNode);
    }
  }

  function setThinkingState(stateNode, state) {
    stateNode.dataset.state = state;
    stateNode.querySelector("span").textContent = getThinkingStatusText(state);
  }

  async function send(question, addUser = true) {
    const input = question.trim();
    if (!input || controller) return;
    if (addUser) append("user", input);
    nodes.input.value = "";
    nodes.input.style.height = "auto";

    const answer = append("assistant", "");
    const state = document.createElement("div");
    state.className = "message-state thinking-state";
    state.innerHTML = '<span></span><i></i><i></i><i></i>';
    setThinkingState(state, ragMode === "off" ? "writing" : "retrieving");
    placeThinkingState(answer, state);
    controller = new AbortController();
    setBusy(true);
    let fullText = "";

    try {
      await streamChat({
        input,
        sessionId,
        ragMode,
        signal: controller.signal,
        onEvent(event) {
          if (event.type === "status") {
            state.querySelector("span").textContent = event.content;
          }
          if (event.type === "sources") {
            renderSources(answer.contentNode, event.sources);
            if (state.isConnected) placeThinkingState(answer, state);
          }
          if (event.type === "chunk") {
            if (state.isConnected) setThinkingState(state, "writing");
            state.remove();
            fullText += event.content;
            answer.textNode.innerHTML = renderMarkdown(fullText);
            scrollBottom();
          }
          if (event.type === "error") throw new Error(event.content);
        },
      });
      await loadSessions();
    } catch (error) {
      state.remove();
      if (error.name === "AbortError") {
        if (!fullText) answer.textNode.textContent = "已停止生成。";
      } else {
        answer.textNode.textContent = fullText || `未能生成回答：${error.message}`;
        const retry = document.createElement("button");
        retry.className = "retry-button";
        retry.textContent = "重新生成";
        retry.addEventListener("click", () => { answer.article.remove(); send(input, false); });
        answer.contentNode.append(retry);
      }
    } finally {
      controller = null;
      setBusy(false);
      nodes.input.focus();
    }
  }

  nodes.form.addEventListener("submit", (event) => { event.preventDefault(); send(nodes.input.value); });
  nodes.input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); nodes.form.requestSubmit(); }
  });
  nodes.input.addEventListener("input", () => {
    nodes.input.style.height = "auto";
    nodes.input.style.height = `${Math.min(nodes.input.scrollHeight, 140)}px`;
  });
  nodes.stop.addEventListener("click", () => controller?.abort());
  nodes.newChat.addEventListener("click", startNewConversation);
  nodes.ragModes.forEach((node) => node.addEventListener("change", () => {
    ragMode = normalizeRagMode(node.value);
    localStorage.setItem("knowbao-rag-mode", ragMode);
    syncRagToggle();
  }));
  nodes.deleteDialog.addEventListener("close", async () => {
    if (nodes.deleteDialog.returnValue !== "confirm" || !pendingDeleteSession) {
      pendingDeleteSession = null;
      return;
    }
    const deletedSession = pendingDeleteSession;
    pendingDeleteSession = null;
    try {
      const result = await deleteJson(
        `/api/history/${encodeURIComponent(deletedSession.session_id)}`
      );
      toast(result.message);
      if (shouldResetAfterSessionDelete(deletedSession.session_id, sessionId)) {
        startNewConversation();
      } else {
        await loadSessions();
      }
    } catch (error) {
      toast(error.message, "error");
    }
  });
  document.querySelectorAll("#suggestions button").forEach((button) => button.addEventListener("click", () => send(button.textContent)));

  loadHistory();
  loadSessions();
  syncRagToggle();
  return { refreshSessions: loadSessions };
}
