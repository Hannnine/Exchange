<template>
  <H5OrPC>
    <!-- PC版 -->
    <template #pc>
      <div id="exhome">
        <div class="container sub-headline">
          <div class="left-container">
            <!-- Converter -->
            <div class="converter-box content">
              <div class="sub-headline">Converter</div>
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
                    <input
                      type="text"
                      :value="toAmount"
                      readonly
                    />
                  </div>
                </div>
                <div class="date-box">
                  <input
                    type="date"
                    v-model="selectedDate"
                    @change="fetchHistoricalRate"
                  />
                </div>
              </div>
              <p class="last-updated">Last updated: {{ lastUpdated }}</p>
            </div>
            <!-- Chart -->
            <div class="chart-box">
              <div class="time-range-buttons">
                <button
                  @click="setTimeRange('WEEK')"
                  :class="{ active: timeRange === 'WEEK' }"
                >
                  WEEK
                </button>
                <button
                  @click="setTimeRange('MONTH')"
                  :class="{ active: timeRange === 'MONTH' }"
                >
                  MONTH
                </button>
                <button
                  @click="setTimeRange('YEAR')"
                  :class="{ active: timeRange === 'YEAR' }"
                >
                  YEAR
                </button>
              </div>
              <canvas id="historyChart"></canvas>
            </div>
          </div>

          <div class="right-contaienr">
            <!-- Watchlist -->
            <div class="watchlist-box">
              <h3>Exchange Rate Watchlist</h3>
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
                  {{ item.rate ? item.rate.toFixed(2) : 'Loading...' }}
                </div>

                <!-- 删除按钮 -->
                <button @click="removeFromWatchlist(index)">Remove</button>
              </div>

              <!-- 添加新条目 -->
              <div>
                <button @click="addNewWatchlistItem">Add New</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- H5版 -->
    <template #h5> </template>
  </H5OrPC>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import H5OrPC from '@/components/PC-or-H5.vue'
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

// i18n
const { t, locale } = useI18n()

// 汇率相关数据
const currencies = ref(['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CNY', 'INR'])
const fromCurrency = ref('USD')
const toCurrency = ref('EUR')
const fromAmount = ref(1)
const toAmount = ref(0)
const selectedDate = ref(new Date().toISOString().split('T')[0]) // 默认当天日期
const lastUpdated = ref('Loading...')
const historicalRates = ref([])
const latestRates = ref({}) // 存储最新汇率
const API_BASE_URL = 'http://127.0.0.1:5000'
const timeRange = ref('MONTH') // 默认时间范围为 'MONTH'
const watchlist = ref([
  { baseCurrency: 'USD', targetCurrency: 'SGD' }, // 默认示例
])

// 初始化图表实例
let chartInstance = null
let refreshInterval

// 恢复数据持久化
function restoreFromLocalStorage() {
  fromCurrency.value = localStorage.getItem('fromCurrency') || 'USD'
  toCurrency.value = localStorage.getItem('toCurrency') || 'EUR'
  selectedDate.value =
    localStorage.getItem('selectedDate') || new Date().toISOString().split('T')[0]
  timeRange.value = localStorage.getItem('timeRange') || 'MONTH' // 恢复时间范围
}

// 持久化数据到 localStorage
function saveToLocalStorage() {
  localStorage.setItem('fromCurrency', fromCurrency.value)
  localStorage.setItem('toCurrency', toCurrency.value)
  localStorage.setItem('selectedDate', selectedDate.value)
  localStorage.setItem('timeRange', timeRange.value)
}

// 获取实时汇率
async function fetchLatestRates() {
  try {
    const response = await fetch(`${API_BASE_URL}/rates?base=${fromCurrency.value}`)
    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`)
    const data = await response.json()
    if (data.error) throw new Error(data.error)

    latestRates.value = data.rates // 更新最新汇率
    lastUpdated.value = new Date().toISOString().split('T')[0]
    convertCurrency() // 使用最新的汇率更新转换值
  } catch (err) {
    console.error('Failed to fetch latest rates:', err)
    alert('Failed to fetch the latest rates. Please try again later.')
  }
}

// 获取历史汇率
async function fetchHistoricalRate() {
  try {
    let period = '1M'
    if (timeRange.value === 'WEEK') {
      period = '1W'
    } else if (timeRange.value === 'YEAR') {
      period = '1Y'
    }

    const response = await fetch(
      `${API_BASE_URL}/history?base=${fromCurrency.value}&target=${toCurrency.value}&period=${period}`,
    )
    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`)
    const data = await response.json()
    if (data.error) throw new Error(data.error)

    historicalRates.value = data.rates
    renderChart()
  } catch (err) {
    console.error('Failed to fetch historical rates:', err)
    alert('Failed to fetch historical rates. Please try again later.')
  }
}

// 转换货币
function convertCurrency() {
  const rate = latestRates.value[toCurrency.value] || 0 // 使用最新的汇率
  const validAmount = isNaN(fromAmount.value) || fromAmount.value <= 0 ? 0 : fromAmount.value // 校验金额
  toAmount.value = (validAmount * rate).toFixed(2) // 计算目标值
}

// 交换货币逻辑
function switchCurrencies() {
  const temp = fromCurrency.value
  fromCurrency.value = toCurrency.value
  toCurrency.value = temp

  // 更新转换值
  convertCurrency()
}

// 渲染图表
function renderChart() {
  if (!chartInstance) {
    chartInstance = echarts.init(document.getElementById('historyChart'))
  }

  const dates = historicalRates.value.map((rate) => rate.date)
  const values = historicalRates.value.map((rate) => rate.rate)

  if (values.length === 0) {
    console.error('No data available to render chart.')
    return
  }

  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)

  chartInstance.setOption({
    title: {
      text: `${fromCurrency.value} to ${toCurrency.value} (${timeRange.value})`,
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%',
      top: '15%',
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
    },
    yAxis: {
      type: 'value',
      min: minValue - (maxValue - minValue) * 0.1,
      max: maxValue + (maxValue - minValue) * 0.1,
    },
    series: [
      {
        name: 'Rate',
        type: 'line',
        smooth: true,
        data: values,
      },
    ],
  })

  chartInstance.resize()
}

// 销毁图标
function resetChartInstance() {
  if (chartInstance) {
    chartInstance.dispose() // 销毁图表实例
    chartInstance = null
  }
  chartInstance = echarts.init(document.getElementById('historyChart')) // 重新初始化
}

// 添加新条目
function addNewWatchlistItem() {
  watchlist.value.push({ baseCurrency: 'USD', targetCurrency: 'SGD', rate: null })
  refreshWatchlistRate(watchlist.value.length - 1) // 初始化汇率
}

// 删除条目
function removeFromWatchlist(index) {
  watchlist.value.splice(index, 1)
}

// 刷新汇率
async function refreshWatchlistRate(index) {
  const item = watchlist.value[index]
  if (!item.baseCurrency || !item.targetCurrency) return

  try {
    const response = await fetch(`${API_BASE_URL}/rates?base=${item.baseCurrency}`)
    const data = await response.json()
    if (data.status === 'success') {
      item.rate = data.rates[item.targetCurrency] || 0 // 更新汇率
    }
  } catch (error) {
    console.error(`Failed to fetch rate for ${item.baseCurrency} to ${item.targetCurrency}:`, error)
    item.rate = null // 设置为 null 以显示 'Loading...'
  }
}

// 设置时间范围
function setTimeRange(range) {
  timeRange.value = range // 更新时间范围
  saveToLocalStorage() // 持久化选择的时间范围
  fetchHistoricalRate() // 重新获取数据并绘制图表
}

// 监听货币切换和金额变化
watch([fromAmount, toCurrency, fromCurrency, selectedDate], () => {
  saveToLocalStorage() // 每次变化时持久化数据
  convertCurrency()
})

// 监听时间范围切换
watch(timeRange, () => {
  saveToLocalStorage() // 持久化时间范围
  fetchHistoricalRate() // 重新加载图表数据
})

// 监听货币切换
watch([fromCurrency, toCurrency, timeRange], async () => {
  await fetchHistoricalRate() // 获取新数据
  renderChart() // 重新绘制图表
})

// 监听 Watchlist 变化
onMounted(() => {
  refreshInterval = setInterval(fetchLatestRates, 60000) // 每分钟刷新一次
})

onBeforeUnmount(() => {
  clearInterval(refreshInterval) // 组件销毁时清除定时器
})

// 初始加载
restoreFromLocalStorage()
fetchLatestRates()
fetchHistoricalRate()
</script>

<style scoped lang="scss">
@import '../../styles/common.scss';
@import '../../styles/variables.scss';

#exhome {
  width: 100%;

  display: flex;
  justify-content: center;

  .container {
    width: 20rem;
    height: 6rem;
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
              input[type='number'],
              input[type='text'] {
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

            input[type='date'] {
              width: 2rem;
              padding: 8px;
              border: 1px solid #ccc;
              border-radius: 8px;
              box-sizing: border-box;
            }
          }
        }

        .last-updated {
          color: #777;
          text-align: right;
        }
      }

      .chart-box {
        flex: 3;
        width: 10rem;
        height: 2.5rem;
        #historyChart {
          width: 10rem;
          height: 2.5rem;
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
            transition:
              background-color 0.3s ease,
              color 0.3s ease;

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
          transition:
            background-color 0.3s ease,
            color 0.3s ease;

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
