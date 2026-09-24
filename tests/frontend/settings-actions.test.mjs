import assert from "node:assert/strict";
import test from "node:test";

import {
  decodeSeparatorLines,
  encodeSeparatorLines,
  settingsPayloadFromForm,
} from "../../frontend/js/settings-actions.mjs";

test("decodes visible separator tokens into real separator strings", () => {
  assert.deepEqual(decodeSeparatorLines("\\n\\n\n\\n\n空格\n\\t"), [
    "\n\n",
    "\n",
    " ",
    "\t",
  ]);
});

test("encodes separators into readable lines for the textarea", () => {
  assert.equal(encodeSeparatorLines(["\n\n", "\n", " ", "\t"]), "\\n\\n\n\\n\n空格\n\\t");
});

test("builds numeric settings payload from form values", () => {
  const payload = settingsPayloadFromForm({
    chunk_size: "900",
    chunk_overlap: "90",
    max_split: "700",
    top_k: "8",
    separators: "\\n\\n\n\\n\n空格",
    weather_default_location: " 杭州 ",
    agent_weather_enabled: false,
  });

  assert.deepEqual(payload, {
    chunk_size: 900,
    chunk_overlap: 90,
    max_split: 700,
    top_k: 8,
    separators: ["\n\n", "\n", " "],
    weather: {
      default_location: "杭州",
    },
    agent_tools: {
      weather: false,
    },
  });
});
