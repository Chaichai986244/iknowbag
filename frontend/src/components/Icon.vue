<script setup>
// 图标组件：内联 SVG path（迁移自原 index.html 的 <symbol> 精灵）
// 每个图标必须带 viewBox，否则路径坐标会超出 svg 视口被裁剪。
const paths = {
  pack: {
    viewBox: "0 0 32 32",
    d: [
      "M6 9.5 16 4l10 5.5v13L16 28 6 22.5v-13Z",
      "m6 9.5 10 5.7 10-5.7M16 15.2V28M11 7l10 5.6",
    ],
  },
  chat: { viewBox: "0 0 24 24", d: ["M4.5 5.5h15v11h-9l-5.5 3v-14Z", "M8 9h8M8 12.5h5"] },
  library: { viewBox: "0 0 24 24", d: ["M5 4h4v16H5zM10.5 4h4v16h-4zM16 5l3.5-1 3.5 14.5-3.5 1z"] },
  plus: { viewBox: "0 0 24 24", d: ["M12 5v14M5 12h14"] },
  menu: { viewBox: "0 0 24 24", d: ["M4 7h16M4 12h16M4 17h16"] },
  send: { viewBox: "0 0 24 24", d: ["m4 5 16 7-16 7 3-7-3-7ZM7 12h13"] },
  stop: { viewBox: "0 0 24 24", d: ["M7 7h10v10H7z"] },
  upload: { viewBox: "0 0 24 24", d: ["M12 15V4m0 0L8 8m4-4 4 4M5 15v4h14v-4"] },
  file: { viewBox: "0 0 24 24", d: ["M7 3.5h7l4 4v13H7zM14 3.5v4h4M10 12h5M10 15.5h5"] },
  trash: { viewBox: "0 0 24 24", d: ["M5 7h14M9 7V4h6v3m2 0-1 13H8L7 7m4 4v5m3-5v5"] },
  close: { viewBox: "0 0 24 24", d: ["m6 6 12 12M18 6 6 18"] },
  settings: {
    viewBox: "0 0 24 24",
    d: [
      "M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z",
      "m19 12.6 1.7 1.3-1.9 3.3-2-.8a7.2 7.2 0 0 1-1.5.9L15 19.5H9l-.3-2.2a7.2 7.2 0 0 1-1.5-.9l-2 .8-1.9-3.3L5 12.6a6 6 0 0 1 0-1.2L3.3 10.1l1.9-3.3 2 .8a7.2 7.2 0 0 1 1.5-.9L9 4.5h6l.3 2.2a7.2 7.2 0 0 1 1.5.9l2-.8 1.9 3.3-1.7 1.3a6 6 0 0 1 0 1.2Z",
    ],
  },
  weather: {
    viewBox: "0 0 24 24",
    d: [
      "M7 16.5h9.2a3.8 3.8 0 0 0 .4-7.6 5.6 5.6 0 0 0-10.7 1.7A3 3 0 0 0 7 16.5Z",
      "M8 20h8M5 20h.1M19 20h.1",
    ],
  },
};

const props = defineProps({
  name: { type: String, required: true },
});
</script>

<template>
  <svg :viewBox="paths[name]?.viewBox || '0 0 24 24'" aria-hidden="true">
    <path
      v-for="(d, index) in paths[name]?.d || []"
      :key="index"
      :d="d"
    />
  </svg>
</template>
