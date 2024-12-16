import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "PageView",
    redirect: "/exchange",
    component: () => import("@/view/PageView.vue"),
    children: [
      {
        path: "/exchange",
        name: "ExChange",
        component: () => import("@/view/index.vue"),
        meta: {
          title: "Exchange",
        },
      },
    ],
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes: routes,
});

// 添加全局前置守卫
router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title}`;
  next(); // 必须调用next()来resolve这个钩子
});

// 全局导航收尾
router.afterEach((to, from) => {
  GoTop();
});

function GoTop() {
  (function smoothscroll() {
    var currentScroll =
      document.documentElement.scrollTop || document.body.scrollTop;
    if (currentScroll > 0) {
      window.requestAnimationFrame(smoothscroll);
      window.scrollTo(0, currentScroll - currentScroll / 10);
    }
  })();
}
