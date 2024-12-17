<template>
  <div class="header">
    <p class="headline">{{ t("exchange.title") }}</p>
    <button class="body" @click="changeLocale()">
      {{ $t("exchange.language") }}
    </button>
  </div>
  <div id="exhome">
    <div class="container sub-headline">
      <div class="left-container">
        <!-- Converter -->
        <div class="converter-box content">
          <div class="sub-headline">{{ t("exchange.converter.c_title") }}</div>
          <div class="currency">
            <div class="currency-selection">
              <div class="currency-box">
                <select v-model="fromCurrency">
                  <option
                    v-for="currency in currencies"
                    :key="currency"
                    :value="currency"
                  >
                    {{ currency }}
                  </option>
                </select>
                <input
                  type="number"
                  v-model.number="fromAmount"
                  @input="convertCurrency"
                />
              </div>
              <div class="switch-icon">
                <button @click="switchCurrencies">🔁</button>
              </div>

              <div class="currency-box">
                <select v-model="toCurrency">
                  <option
                    v-for="currency in currencies"
                    :key="currency"
                    :value="currency"
                  >
                    {{ currency }}
                  </option>
                </select>
                <input type="text" :value="toAmount" readonly />
              </div>
            </div>
            <div class="date-box">
              <input
                type="date"
                v-model="selectedDate"
                :max="getToday()"
                @change="handleDateChange"
              />
            </div>
          </div>
          <div class="search-button">
            <button @click="searchClick">
              {{ t("exchange.converter.c_search") }}
            </button>
          </div>
          <p class="last-updated">
            {{ t("exchange.converter.c_date") }} {{ lastUpdated }}
          </p>
        </div>

        <!-- Chart -->
        <div class="chart-box">
          <div class="time-range-buttons">
            <button
              @click="setTimeRange('WEEK')"
              :class="{ active: timeRange === 'WEEK' }"
            >
              <p>{{ t("exchange.chart.b_week") }}</p>
            </button>
            <button
              @click="setTimeRange('MONTH')"
              :class="{ active: timeRange === 'MONTH' }"
            >
              <p>{{ t("exchange.chart.b_month") }}</p>
            </button>
            <button
              @click="setTimeRange('YEAR')"
              :class="{ active: timeRange === 'YEAR' }"
            >
              <p>{{ t("exchange.chart.b_year") }}</p>
            </button>
          </div>
          <canvas id="historyChart"></canvas>
        </div>
      </div>

      <div class="right-contaienr">
        <!-- Watchlist -->
        <div class="watchlist-box">
          <h3>{{ t("exchange.watchlist.w_title") }}</h3>
          <div
            v-for="(item, index) in watchlist"
            :key="index"
            class="watchlist-item"
          >
            <div class="currency-selection">
              <!-- 选择基础货币 -->
              <select
                v-model="item.baseCurrency"
                @change="refreshWatchlistRate(index)"
              >
                <option
                  v-for="currency in currencies"
                  :key="currency"
                  :value="currency"
                >
                  {{ currency }}
                </option>
              </select>

              <!-- 选择目标货币 -->
              <select
                v-model="item.targetCurrency"
                @change="refreshWatchlistRate(index)"
              >
                <option
                  v-for="currency in currencies"
                  :key="currency"
                  :value="currency"
                  :disabled="currency === item.baseCurrency"
                >
                  {{ currency }}
                </option>
              </select>
            </div>

            <!-- 显示汇率 -->
            <div class="currency-rate">
              {{ item.rate ? item.rate.toFixed(2) : "Loading..." }}
            </div>

            <!-- 删除按钮 -->
            <button @click="removeWatchlistItem(index)">
              {{ t("exchange.watchlist.w_remove") }}
            </button>
          </div>

          <!-- 添加新条目 -->
          <div>
            <button @click="addWatchlistItem">
              {{ t("exchange.watchlist.w_add") }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, render } from "vue";
import * as echarts from "echarts";
import { useI18n } from "vue-i18n";
import i18n from "@/i18n/index.js";
import { showSuccessToast } from "vant";
import "vant/es/toast/style";

const { t, locale } = useI18n();
const API_BASE_URL = "http://127.0.0.1:5000"; // 后端 API 地址

// 数据状态
const currencies = ref([
  "USD",
  "EUR",
  "GBP",
  "JPY",
  "AUD",
  "CAD",
  "CNY",
  "INR",
]); // 支持的货币列表
const fromCurrency = ref("USD");
const toCurrency = ref("EUR");
const fromAmount = ref(1);
const toAmount = ref(0);
const historicalRates = ref([]); // 历史汇率数据
const latestRates = ref({}); // 实时汇率数据
const selectedDate = ref(new Date().toISOString().split("T")[0]);
const lastUpdated = ref("Loading...");
const timeRange = ref("MONTH"); // 当前时间范围：WEEK, MONTH, YEAR
const watchlist = ref([
  { baseCurrency: "USD", targetCurrency: "EUR", rate: null }, // 默认初始值
]);

let chartInstance = null; // 图表实例
let refreshInterval = null; // 定时器

// 数据持久化函数
function saveToLocalStorage() {
  localStorage.setItem("fromCurrency", fromCurrency.value);
  localStorage.setItem("toCurrency", toCurrency.value);
  localStorage.setItem("timeRange", timeRange.value);
}

// 切换语言
function changeLocale() {
  locale.value = locale.value === "zh_CN" ? "eng" : "zh_CN";
  localStorage.setItem("locale", locale.value);
  showSuccessToast(i18n.global.t("exchange.toast"));
}

function restoreFromLocalStorage() {
  fromCurrency.value = localStorage.getItem("fromCurrency") || "USD";
  toCurrency.value = localStorage.getItem("toCurrency") || "EUR";
  timeRange.value = localStorage.getItem("timeRange") || "MONTH";
}

// 通用 API 请求函数
async function fetchAPI(endpoint, params = {}) {
  const urlParams = new URLSearchParams(params).toString();
  const url = `${API_BASE_URL}/${endpoint}?${urlParams}`;
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
    const data = await response.json();
    if (data.status !== "success")
      throw new Error(data.error || "Unknown error");
    return data;
  } catch (err) {
    console.error(`Failed to fetch ${endpoint}:`, err);
    return null;
  }
}

// 实时汇率数据获取
async function fetchLatestRates() {
  const data = await fetchAPI("rates", { base: fromCurrency.value });
  if (data && data.rates) {
    latestRates.value = data.rates;
    lastUpdated.value = getToday();
    convertCurrency();
  } else {
    alert("Failed to fetch the latest rates. Please try again later.");
  }
}

// 获取历史汇率数据
async function fetchHistoricalRates() {
  try {
    const data = await fetchAPI("history", {
      base: fromCurrency.value,
      target: toCurrency.value,
      period: timeRange.value,
      date: selectedDate.value, // 传递选定日期到后端
    });
    if (data && data.rates) {
      historicalRates.value = data.rates;
      renderChart();
    } else {
      alert("Failed to fetch historical rates. Please try again later.");
    }
  } catch (err) {
    console.error("Failed to fetch historical rates:", err);
  }
}

// 渲染图表
function renderChart() {
  if (!chartInstance) {
    const chartElement = document.getElementById("historyChart");
    if (chartElement) {
      chartInstance = echarts.init(chartElement);
    } else {
      console.error("Chart element not found.");
      return;
    }
  }

  const rates = historicalRates.value;
  const dates = rates.map((item) => item.date); // 横坐标
  const values = rates.map((item) => item.rate); // 纵坐标

  if (values.length === 0) {
    console.error("No data available for rendering chart.");
    return;
  }

  // 获取汇率的最小值和最大值
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);

  // 动态调整纵轴范围
  const rangePadding = (maxValue - minValue) * 0.2 || 0.01; // 确保有额外的空间，即使波动很小

  chartInstance.setOption({
    title: {
      text: `Exchange Rate (${fromCurrency.value} to ${toCurrency.value} - ${timeRange.value})`,
      left: "center",
      textStyle: { fontSize: 16, fontWeight: "bold" },
    },
    tooltip: { trigger: "axis" },
    grid: { left: "10%", right: "10%", bottom: "20%", top: "15%" },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: dates,
      axisLabel: {
        rotate: 45,
        formatter: (value) => value.split("-").slice(1).join("/"), // 格式化日期为 MM/DD
      },
    },
    yAxis: {
      type: "value",
      min: minValue - rangePadding, // 在最小值基础上减去额外范围
      max: maxValue + rangePadding, // 在最大值基础上增加额外范围
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { type: "dashed", color: "#e0e0e0" } },
    },
    series: [
      {
        name: "Rate",
        type: "line",
        smooth: true,
        data: values,
        itemStyle: { color: "#007bff" },
        areaStyle: { color: "rgba(0, 123, 255, 0.2)" },
        lineStyle: { width: 2 },
      },
    ],
  });

  chartInstance.resize();
}

// 日期切换后绘表
function handleDateChange() {
  fetchHistoricalRates();
  refreshAllCharts();
}

// 获取当天日期
function getToday() {
  const today = new Date();
  return today.toISOString().split("T")[0]; // 返回格式：YYYY-MM-DD
}

// 转换货币
function convertCurrency() {
  const rate = latestRates.value[toCurrency.value] || 0;
  const validAmount =
    isNaN(fromAmount.value) || fromAmount.value <= 0 ? 0 : fromAmount.value;
  toAmount.value = (validAmount * rate).toFixed(2);
}

// Search按钮
function searchClick() {
  convertCurrency();
  fetchHistoricalRates();
  fetchLatestRates();
  renderChart();
}

// 切换货币
function switchCurrencies() {
  [fromCurrency.value, toCurrency.value] = [
    toCurrency.value,
    fromCurrency.value,
  ];
  convertCurrency();
}

// 设置时间范围
function setTimeRange(range) {
  timeRange.value = range;
  saveToLocalStorage();
  fetchHistoricalRates();
}

// 监控列表：添加新条目
function addWatchlistItem() {
  watchlist.value.push({
    baseCurrency: "USD",
    targetCurrency: null,
    rate: null,
  });
}

// 监控列表：移除条目
function removeWatchlistItem(index) {
  watchlist.value.splice(index, 1);
}

async function refreshWatchlistRate(index) {
  const item = watchlist.value[index];
  const data = await fetchAPI("rates", { base: item.baseCurrency });

  if (data && data.rates) {
    item.rate = data.rates[item.targetCurrency] || null;
  } else {
    item.rate = null; // 请求失败时清空汇率
  }
}

// 初始化
onMounted(() => {
  restoreFromLocalStorage();
  fetchLatestRates();
  fetchHistoricalRates();
  refreshInterval = setInterval(fetchLatestRates, 60000); // 每分钟刷新一次

  // 初始化监控列表的汇率
  watchlist.value.forEach((_, index) => refreshWatchlistRate(index));
});

// 清理
onBeforeUnmount(() => {
  clearInterval(refreshInterval);
});

// 监听时间范围变化
watch(watchlist, (newList) => {
  newList.forEach((_, index) => refreshWatchlistRate(index));
});
</script>

<style scoped lang="scss">
@import "@/styles/common.scss";
@import "@/styles/variables.scss";
.header {
  width: 13.78rem;
  height: 0.7rem;
  display: flex;
  p {
    width: 13.78rem;
    text-align: center;
    margin: 0.1rem 0;
  }
  button {
    position: absolute;
    right: 0.5rem;
    top: 0.2rem;
    padding: 8px 16px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    background-color: wihite;
    color: rgb(4, 4, 4);

    &:hover {
      background-color: #007bff;
      color: white;
    }
  }
}

#exhome {
  display: flex;
  justify-content: center;
  .container {
    width: 13.78rem;
    height: 7rem;
    display: flex;
    justify-content: center;
    gap: 20px;
    padding: 20px;
    background-color: #f5f5f5;
    border-radius: 12px; // 整体圆角

    .left-container {
      flex: 3;
      display: flex;
      flex-direction: column;
      gap: 20px;

      .converter-box {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 10px; // 子元素之间的间距

        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);

        .currency {
          margin: auto;
          .currency-selection {
            display: flex;
            align-items: center;
            gap: 20px;

            .currency-box {
              display: flex;
              flex-direction: column;
              gap: 5px;

              select,
              input[type="number"],
              input[type="text"] {
                width: 4rem;
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 8px;
                box-sizing: border-box;
              }
            }

            .switch-icon {
              display: flex;
              align-items: center;
              justify-content: center;

              button {
                width: 0.5rem;
                height: 0.5rem;
                border: none;
                background-color: #fff;
                border-radius: 50%;
                cursor: pointer;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                display: flex;
                align-items: center;
                justify-content: center;
              }
            }
          }

          .date-box {
            display: flex;
            align-items: center;
            gap: 10px;

            input[type="date"] {
              width: 2rem;
              padding: 8px;
              border: 1px solid #ccc;
              border-radius: 8px;
              box-sizing: border-box;
            }
          }
        }

        .search-button {
          display: flex;
          justify-content: center;
          margin-top: 10px;

          button {
            padding: 8px 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            background-color: wihite;
            color: rgb(4, 4, 4);

            &:hover {
              background-color: #007bff;
              color: white;
            }
          }
        }

        .last-updated {
          color: #777;
          text-align: right;
        }
      }

      .chart-box {
        flex: 2;
        width: 10rem;
        height: 2.5rem;
        #historyChart {
          width: 10rem;
          height: 2.5rem;
        }
        p {
          text-align: center;
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
      }

      .time-range-buttons {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin-bottom: 10px;

        button {
          padding: 6px 16px;
          border: none;
          border-radius: 5px;
          cursor: pointer;
          background-color: #f0f0f0;
          font-size: 14px;
          transition: background-color 0.3s ease;

          &.active {
            background-color: #007bff;
            color: white;
          }

          &:hover {
            background-color: #007bff;
            color: white;
          }
        }
      }
    }
    .right-contaienr {
      flex: 1;
      display: flex;
      .watchlist-box {
        .watchlist-item {
          display: flex;
          align-items: center;
          justify-content: space-between; /* Remove 按钮右对齐 */
          padding: 15px; /* 增加上下间距 */
          border-bottom: 1px solid #ddd;

          .currency-selection {
            display: flex;
            align-items: center;
            gap: 15px; /* 增加货币选择框间距 */

            select {
              width: 90px; /* 调整选择框宽度 */
              padding: 8px;
              border-radius: 5px;
              border: 1px solid #ccc;
            }
          }

          .currency-rate {
            font-weight: bold;
            color: green;
            margin: 0 15px; /* 调整与选择框及按钮的间距 */
            min-width: 80px; /* 保证固定宽度，防止布局问题 */
            text-align: center; /* 数字居中对齐 */
          }

          button {
            background-color: #f0f0f0; /* 默认背景色 */
            color: black;
            border: none;
            border-radius: 4px;
            padding: 8px 15px; /* 调整按钮大小 */
            cursor: pointer;
            margin-left: auto;
            text-align: center;
            transition: background-color 0.3s ease, color 0.3s ease;

            &:hover {
              background-color: #007bff; /* 悬停背景色 */
              color: white; /* 悬停文字颜色 */
            }
          }
        }

        button {
          margin-top: 10px;
          padding: 8px 15px;
          border-radius: 5px;
          border: none;
          background-color: #f0f0f0; /* 默认背景色 */
          color: black; /* 默认文字颜色 */
          cursor: pointer;
          text-align: center;
          transition: background-color 0.3s ease, color 0.3s ease;

          &:hover {
            background-color: #007bff; /* 悬停背景色 */
            color: white; /* 悬停文字颜色 */
          }
        }
      }
    }

    .converter-box,
    .chart-box,
    .watchlist-box {
      background-color: white;
      border-radius: 12px;
      box-shadow: 0 5px 5px rgba(0, 0, 0, 0.1);
      padding: 20px;
    }
  }
}
</style>
