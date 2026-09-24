import { createApp } from "vue";
import { createPinia } from "pinia";

import App from "./App.vue";
import "./styles/tokens.css";
import "./styles/base.css";
import "./styles/shell.css";
import "./styles/chat.css";
import "./styles/markdown.css";
import "./styles/knowledge.css";
import "./styles/settings.css";
import "./styles/responsive.css";
import "./styles/glass.css";

createApp(App).use(createPinia()).mount("#app");
