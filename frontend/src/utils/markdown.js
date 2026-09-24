// Markdown 渲染：由原前端 utils.js 迁移而来，保持输出结构一致。

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderInline(value) {
  let output = escapeHtml(value);
  output = output.replace(/`([^`]+)`/g, "<code>$1</code>");
  output = output.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, href) => {
    const safeHref = href.trim();
    if (!/^(https?:\/\/|mailto:|\/)/i.test(safeHref)) return label;
    return `<a href="${safeHref}" target="_blank" rel="noopener noreferrer">${label}</a>`;
  });
  output = output.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  output = output.replace(/__([^_]+)__/g, "<strong>$1</strong>");
  return output.replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>");
}

function tableCells(line) {
  return line
    .trim()
    .replace(/^\||\|$/g, "")
    .split("|")
    .map((cell) => cell.trim());
}

export function renderMarkdown(markdown) {
  const lines = String(markdown || "")
    .replaceAll("\r\n", "\n")
    .split("\n");
  const blocks = [];
  let index = 0;
  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) {
      index += 1;
      continue;
    }
    const fence = line.match(/^```([\w+-]*)\s*$/);
    if (fence) {
      const code = [];
      for (
        index += 1;
        index < lines.length && !/^```\s*$/.test(lines[index]);
        index += 1
      )
        code.push(lines[index]);
      if (index < lines.length) index += 1;
      const language = fence[1] ? ` class="language-${fence[1]}"` : "";
      blocks.push(`<pre><code${language}>${escapeHtml(code.join("\n"))}</code></pre>`);
      continue;
    }
    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      const level = heading[1].length;
      blocks.push(`<h${level}>${renderInline(heading[2])}</h${level}>`);
      index += 1;
      continue;
    }
    const divider =
      index + 1 < lines.length &&
      /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(lines[index + 1]);
    if (line.includes("|") && divider) {
      const headers = tableCells(line);
      const rows = [];
      index += 2;
      while (index < lines.length && lines[index].includes("|") && lines[index].trim()) {
        rows.push(tableCells(lines[index]));
        index += 1;
      }
      const head = headers.map((cell) => `<th>${renderInline(cell)}</th>`).join("");
      const body = rows
        .map((row) => `<tr>${row.map((cell) => `<td>${renderInline(cell)}</td>`).join("")}</tr>`)
        .join("");
      blocks.push(
        `<div class="markdown-table-wrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`
      );
      continue;
    }
    if (/^\s*[-*+]\s+/.test(line)) {
      const items = [];
      while (index < lines.length && /^\s*[-*+]\s+/.test(lines[index])) {
        items.push(lines[index].replace(/^\s*[-*+]\s+/, ""));
        index += 1;
      }
      blocks.push(`<ul>${items.map((item) => `<li>${renderInline(item)}</li>`).join("")}</ul>`);
      continue;
    }
    if (/^\s*\d+\.\s+/.test(line)) {
      const items = [];
      while (index < lines.length && /^\s*\d+\.\s+/.test(lines[index])) {
        items.push(lines[index].replace(/^\s*\d+\.\s+/, ""));
        index += 1;
      }
      blocks.push(`<ol>${items.map((item) => `<li>${renderInline(item)}</li>`).join("")}</ol>`);
      continue;
    }
    if (/^>\s?/.test(line)) {
      const quote = [];
      while (index < lines.length && /^>\s?/.test(lines[index])) {
        quote.push(lines[index].replace(/^>\s?/, ""));
        index += 1;
      }
      blocks.push(`<blockquote>${quote.map(renderInline).join("<br>")}</blockquote>`);
      continue;
    }
    if (/^\s*([-*_])(?:\s*\1){2,}\s*$/.test(line)) {
      blocks.push("<hr>");
      index += 1;
      continue;
    }
    const paragraph = [line];
    index += 1;
    while (
      index < lines.length &&
      lines[index].trim() &&
      !/^(#{1,6})\s+|^```|^\s*[-*+]\s+|^\s*\d+\.\s+|^>\s?/.test(lines[index])
    ) {
      paragraph.push(lines[index]);
      index += 1;
    }
    blocks.push(`<p>${paragraph.map(renderInline).join("<br>")}</p>`);
  }
  return blocks.join("");
}
