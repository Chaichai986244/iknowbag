import { deleteJson, getJson, uploadFile } from "./api.js?v=20260803l";
import { formatFileSize, validateKnowledgeFile } from "./utils.js?v=20260803l";

export function initKnowledge({ toast, onCountChange }) {
  const nodes = {
    summary: document.querySelector("#knowledge-summary"), list: document.querySelector("#source-list"), total: document.querySelector("#source-total"),
    input: document.querySelector("#file-input"), drop: document.querySelector("#drop-zone"), selected: document.querySelector("#selected-file"),
    name: document.querySelector("#file-name"), meta: document.querySelector("#file-meta"), remove: document.querySelector("#remove-file"),
    upload: document.querySelector("#upload-button"), status: document.querySelector("#upload-status"), dialog: document.querySelector("#delete-dialog"), message: document.querySelector("#delete-message"),
  };
  let selectedFile = null;
  let pendingDelete = null;

  function clearFile() {
    selectedFile = null; nodes.input.value = ""; nodes.selected.classList.add("hidden"); nodes.upload.disabled = true;
  }
  function selectFile(file) {
    const result = validateKnowledgeFile(file);
    if (!result.ok) return toast(result.message, "error");
    selectedFile = file; nodes.name.textContent = file.name; nodes.meta.textContent = `${formatFileSize(file.size)} · ${file.name.split(".").pop().toUpperCase()}`;
    nodes.selected.classList.remove("hidden"); nodes.upload.disabled = false; nodes.status.textContent = "";
  }
  function fileRow(item) {
    const row = document.createElement("article"); row.className = "source-item newly-packed";
    row.innerHTML = '<svg><use href="#i-file"></use></svg><span class="source-info"><strong></strong><small></small></span><button class="icon-button delete-source" aria-label="删除资料"><svg><use href="#i-trash"></use></svg></button>';
    row.querySelector("strong").textContent = item.source; row.querySelector("strong").title = item.source;
    row.querySelector("small").textContent = `${String(item.file_type).toUpperCase()} · ${item.chunk_count} 个内容片段`;
    row.querySelector("button").addEventListener("click", () => {
      pendingDelete = item; nodes.message.textContent = `“${item.source}”包含 ${item.chunk_count} 个内容片段，删除后无法撤销。`; nodes.dialog.showModal();
    });
    return row;
  }
  async function refresh() {
    try {
      const data = await getJson("/api/knowledge");
      nodes.summary.textContent = `${data.source_count} 份资料 · ${data.document_count} 个内容片段`;
      nodes.total.textContent = `${data.source_count} 份`; onCountChange(data.source_count);
      nodes.list.replaceChildren();
      if (!data.source_details.length) {
        const empty = document.createElement("div"); empty.className = "empty-source"; empty.textContent = "知识包还是空的，先放进一份 PDF 或 TXT。"; nodes.list.append(empty);
      } else data.source_details.forEach((item) => nodes.list.append(fileRow(item)));
    } catch (error) { toast(error.message, "error"); }
  }

  nodes.input.addEventListener("change", () => selectFile(nodes.input.files[0])); nodes.remove.addEventListener("click", clearFile);
  ["dragenter", "dragover"].forEach((name) => nodes.drop.addEventListener(name, (event) => { event.preventDefault(); nodes.drop.classList.add("dragging"); }));
  ["dragleave", "drop"].forEach((name) => nodes.drop.addEventListener(name, (event) => { event.preventDefault(); nodes.drop.classList.remove("dragging"); }));
  nodes.drop.addEventListener("drop", (event) => selectFile(event.dataTransfer.files[0]));
  nodes.upload.addEventListener("click", async () => {
    if (!selectedFile) return; nodes.upload.disabled = true; nodes.status.textContent = "正在处理资料…";
    try { const result = await uploadFile(selectedFile); toast(result.message); clearFile(); await refresh(); }
    catch (error) {
      if (error.message.includes("已存在")) {
        nodes.status.textContent = "这份资料已经在包里了。";
      } else if (error.message.includes("OCR")) {
        nodes.status.textContent = "这份 PDF 没有可提取的文字，请先进行 OCR。";
      } else {
        nodes.status.textContent = error.message;
      }
      nodes.upload.disabled = false;
    }
  });
  nodes.dialog.addEventListener("close", async () => {
    if (nodes.dialog.returnValue !== "confirm" || !pendingDelete) { pendingDelete = null; return; }
    const item = pendingDelete; pendingDelete = null;
    try { const result = await deleteJson("/api/knowledge/source", { source: item.source }); toast(result.message); await refresh(); }
    catch (error) { toast(error.message, "error"); }
  });

  refresh();
  return { refresh };
}
