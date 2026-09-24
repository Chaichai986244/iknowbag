// API 客户端：与后端 FastAPI 保持原 aiohttp 协议一致。
// 流式接口使用 NDJSON（application/x-ndjson）。

export const MAX_FILE_SIZE = 30 * 1024 * 1024;

export function parseNdjsonBuffer(buffer) {
  const lines = buffer.split("\n");
  const remainder = lines.pop() || "";
  const events = lines
    .filter((line) => line.trim())
    .map((line) => JSON.parse(line));
  return { events, remainder };
}

async function parseJson(response) {
  const payload = await response.json();
  if (!response.ok || !payload.ok) {
    throw new Error(payload.message || "请求失败。");
  }
  return payload.data ?? payload;
}

export async function getJson(url) {
  return parseJson(await fetch(url));
}

export async function deleteJson(url, body) {
  return parseJson(
    await fetch(url, {
      method: "DELETE",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
  );
}

export async function putJson(url, body) {
  return parseJson(
    await fetch(url, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
  );
}

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  return parseJson(
    await fetch("/api/knowledge/upload", {
      method: "POST",
      body: formData,
    })
  );
}

export async function streamChat({ input, sessionId, ragMode, signal, onEvent }) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input, session_id: sessionId, rag_mode: ragMode }),
    signal,
  });
  if (!response.ok) {
    const payload = await response.json();
    throw new Error(payload.message || "无法生成回答。");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const parsed = parseNdjsonBuffer(buffer);
    buffer = parsed.remainder;
    parsed.events.forEach(onEvent);
    if (done) break;
  }
}
