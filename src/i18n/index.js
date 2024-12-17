import { createI18n, useI18n } from "vue-i18n";
import en from "@/locales/en.js";
import zh_CN from "@/locales/zh_CN.js";
export default new createI18n({
  legacy: false,
  locale: localStorage.getItem("locale") || "en",
  fallbackLocale: "en",
  warnHtmlMessage: false,
  messages: {
    en,
    zh_CN,
  },
});
