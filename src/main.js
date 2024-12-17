// main.js
import { createApp } from "vue";
import App from "./App.vue";
import { Toast } from "vant";
import i18n from "@/i18n/index.js";

const app = createApp(App);

app.use(i18n);
app.use(Toast);
app.mount("#app");
