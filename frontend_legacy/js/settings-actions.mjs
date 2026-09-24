const visibleSeparatorLabels = new Map([
  ["\\n\\n", "\n\n"],
  ["\\n", "\n"],
  ["\\t", "\t"],
  ["空格", " "],
]);

export function decodeSeparatorLines(value) {
  return String(value || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => visibleSeparatorLabels.get(line) ?? line);
}

export function encodeSeparatorLines(separators) {
  const labels = new Map([
    ["\n\n", "\\n\\n"],
    ["\n", "\\n"],
    ["\t", "\\t"],
    [" ", "空格"],
  ]);
  return (separators || [])
    .map((separator) => labels.get(separator) ?? separator)
    .join("\n");
}

export function settingsPayloadFromForm(values) {
  return {
    chunk_size: Number.parseInt(values.chunk_size, 10),
    chunk_overlap: Number.parseInt(values.chunk_overlap, 10),
    max_split: Number.parseInt(values.max_split, 10),
    top_k: Number.parseInt(values.top_k, 10),
    separators: decodeSeparatorLines(values.separators),
    weather: {
      default_location: String(values.weather_default_location || "").trim(),
    },
    agent_tools: {
      weather: Boolean(values.agent_weather_enabled),
    },
  };
}
