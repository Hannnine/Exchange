// main.js
import { createApp } from "vue";
import App from "./App.vue";
import { createI18n } from "vue-i18n"; // 引入 vue-i18n

// 配置国际化
const i18n = createI18n({
  locale: "en", // 默认语言
  messages: {
    en: {
      message: {
        // 这里是英语的翻译内容
        hello: "Hello",
      },
    },
    zh: {
      message: {
        // 这里是中文的翻译内容
        hello: "你好",
      },
    },
  },
});

const app = createApp(App);

app.use(i18n);

app.mount("#app");
