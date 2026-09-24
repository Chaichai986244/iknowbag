import assert from "node:assert/strict";
import test from "node:test";

import {
  beginNewConversation,
  formatDisplayTime,
  getThinkingStatusText,
  normalizeRagMode,
  selectConversation,
  shouldResetAfterSessionDelete,
} from "../../frontend/js/chat-actions.mjs";

test("new conversation requests the chat page and resets conversation state", () => {
  const calls = [];

  const newSessionId = beginNewConversation({
    abortCurrent: () => calls.push("abort"),
    createSessionId: () => "new-session",
    saveSessionId: (value) => calls.push(["save", value]),
    setTitle: (value) => calls.push(["title", value]),
    clearMessages: () => calls.push("clear"),
    showEmpty: () => calls.push("empty"),
    refreshSessions: () => calls.push("refresh"),
    requestChatPage: () => calls.push("navigate-chat"),
  });

  assert.equal(newSessionId, "new-session");
  assert.deepEqual(calls, [
    "abort",
    ["save", "new-session"],
    ["title", "新对话"],
    "clear",
    "empty",
    "navigate-chat",
    "refresh",
  ]);
});

test("deleting the current session requires a new conversation", () => {
  assert.equal(shouldResetAfterSessionDelete("current", "current"), true);
});

test("deleting another session keeps the current conversation", () => {
  assert.equal(shouldResetAfterSessionDelete("other", "current"), false);
});

test("selecting a conversation requests the chat page", () => {
  const calls = [];

  const selectedSessionId = selectConversation({
    session: { session_id: "session-123", title: "历史问题" },
    saveSessionId: (value) => calls.push(["save", value]),
    setTitle: (value) => calls.push(["title", value]),
    requestChatPage: () => calls.push("navigate-chat"),
  });

  assert.equal(selectedSessionId, "session-123");
  assert.deepEqual(calls, [
    ["save", "session-123"],
    ["title", "历史问题"],
    "navigate-chat",
  ]);
});

test("formats iso timestamp for compact display", () => {
  const result = formatDisplayTime("2026-08-03T09:08:07");

  assert.equal(result, "08/03 09:08");
});

test("maps visible thinking states to user friendly text", () => {
  assert.equal(getThinkingStatusText("retrieving"), "正在检索你的资料");
  assert.equal(getThinkingStatusText("grounding"), "已找到参考资料，正在组织回答");
  assert.equal(getThinkingStatusText("writing"), "正在生成回答");
});

test("normalizes persisted rag mode values", () => {
  assert.equal(normalizeRagMode(null), "auto");
  assert.equal(normalizeRagMode("off"), "off");
  assert.equal(normalizeRagMode("force"), "force");
  assert.equal(normalizeRagMode("auto"), "auto");
  assert.equal(normalizeRagMode("false"), "off");
  assert.equal(normalizeRagMode("true"), "force");
  assert.equal(normalizeRagMode("bad"), "auto");
});
