const state = {
  activeView: "overview",
  sgeRange: "1D",
  reversalRange: "1D",
  us10yRange: "1D",
  us10yActiveTenor: "10y",
  eventFilter: "all",
  status: null,
  reversalStatus: null,
  us10yStatus: null,
  notificationLogs: [],
  sgeHistory: [],
  reversalHistory: [],
  us10yHistory: [],
  charts: {},
  pagers: {},
  updateLogs: [],
  sgeYAxisRange: { min: 800, max: 1200 },
  isLoading: false,
  loadingTasks: new Set(),
};

const UPDATE_LOG_STORAGE_KEY = "sge-monitor-update-logs";
const APP_VERSION = "1.0.1";
const PRESET_UPDATE_LOGS = [
  "2026-03-29:⚡ 优化分页显示：当页数超过10页时，智能显示页码，避免显示过多按钮。",
  "2026-03-29:🎉 项目完成整理，发布 v1.0.0 正式版！",
  "2026-03-29:📁 重构项目结构：新增 docs/、scripts/ 目录，分类管理文档和脚本。",
  "2026-03-29:📚 新增 CONTRIBUTING.md 贡献指南，规范开发流程和代码提交标准。",
  "2026-03-29:📋 新增 CHANGELOG.md 更新日志，记录所有版本变更。",
  "2026-03-29:🔧 新增 .gitignore 配置，排除虚拟环境和数据库文件。",
  "2026-03-29:🗂️ 文档归档：将 46 个文档分类到设计/指南/问题/历史等目录。",
  "2026-03-29:🛠️ 脚本整理：删除临时脚本，将工具脚本分类到 check/analyze/utils。",
  "2026-03-28:优化SGE采集策略：休市时降低采集频率（5分钟/次），开市时恢复正常频率（60秒/次）。",
  "2026-03-28:优化SGE图表Y轴自动适配数据范围，放大细微差异，解决三条线看起来一样的问题。",
  "2026-03-28:修复X轴零点日期显示，改为只显示日期数字（如28）而非完整格式。",
  "2026-03-28:优化X轴刻度为固定1小时间隔，与原系统保持一致（一个钟为一个刻度）。",
  "2026-03-28:优化黄金反转监控采集频率，从每10分钟改为每1分钟，曲线更加平滑连续。",
  "2026-03-28:优化所有图表X轴时间显示，零点位置显示日期（MM-DD），避免混乱标签。",
  "2026-03-28:修复SGE溢价Y轴范围，改为根据实际溢价数据自动调整，不再从0开始。",
  "2026-03-28:调整SGE图表配色为蓝/绿/橙黄，与原系统保持一致，三条曲线均添加渐变填充。",
  "2026-03-23:\u65b0\u589e\u53f3\u4e0a\u89d2\u201c\u66f4\u65b0\u8bb0\u5f55\u201d\u6309\u94ae\u4e0e\u5f39\u7a97\uff0c\u53ef\u6301\u7eed\u8bb0\u5f55\u6bcf\u6b21\u6539\u52a8\u3002",
  "2026-03-23:\u63a8\u9001\u8bbe\u7f6e\u9875\u65b0\u589e\u201c\u63a8\u9001\u8bb0\u5f55\u201d\u8868\u683c\uff0c\u5c55\u793a\u65f6\u95f4\u3001\u76ee\u6807\u3001\u7ed3\u679c\u4e0e\u5185\u5bb9\u3002",
  "2026-03-23:\u9ec4\u91d1\u53cd\u8f6c\u56db\u7ea7\u4fe1\u53f7\u89c4\u5219\uff08\u542b us10y \u6761\u4ef6\uff09\u4e0a\u7ebf\uff0c\u4ec5 1/2 \u7ea7\u63a8\u9001\u3002",
  "2026-03-23:\u83dc\u5355\u6539\u4e3a\u516d\u4e2a\u4e3b\u83dc\u5355\uff0c\u9ec4\u91d1\u53cd\u8f6c\u9884\u8b66\u4e0b\u65b0\u589e\u201c\u5341\u5e74\u671f\u7f8e\u503a\u53cd\u8f6c\u201d\u5b50\u83dc\u5355\u3002",
  "2026-03-23:\u5c06 SGE\u6ea2\u4ef7\u653e\u5165\u201c\u9ec4\u91d1\u53cd\u8f6c\u9884\u8b66\u201d\u5b50\u83dc\u5355\uff0c\u5e76\u5c06\u201c\u9ec4\u91d1\u53cd\u8f6c\u201d\u66f4\u540d\u4e3a\u201c\u76d8\u9762\u9884\u8b66\u201d\u3002",
  "2026-03-23:\u9875\u9762\u53f3\u4e0a\u65b0\u589e\u7248\u672c\u53f7\u663e\u793a\uff0c\u5f53\u524d\u7248\u672c 0.2\u3002",
  "2026-03-23:\u672c\u6b21\u6539\u52a8\u5e45\u5ea6\u8f83\u5927\uff0c\u7248\u672c\u53f7\u4ece 0.2 \u8c03\u6574\u4e3a 0.23\u3002",
  "2026-03-23:\u7f8e\u503a\u9884\u8b66\u65b0\u589e\u53ef\u914d\u7f6e\u89c4\u5219\uff1aNh\u56de\u843dNbp\uff0c\u53ef\u914d\u91c7\u6837\u9891\u7387(\u79d2)\u548c\u591a\u9009\u9650\u671f(5Y/10Y/20Y)\uff0c\u4ec5\u89e6\u53d1\u65f6\u63a8\u9001\u3002",
  "2026-03-23:\u9ec4\u91d1\u9884\u8b66\u4e0b\u65b0\u589e\u201c\u653f\u6cbb\u4e0e\u6218\u4e89\u9884\u8b66\u201d\u5b50\u83dc\u5355\uff0c\u590d\u7528RSS\u4e8b\u4ef6\u6d41\u5e76\u65b0\u589e\u201c\u9ec4\u91d1\u4e0a\u6da8\u98ce\u9669\u6253\u5206\u201d\u3002",
  "2026-03-23:\u4e8b\u4ef6\u6253\u5206\u6539\u4e3a 1-10 \u5206\u4f53\u7cfb\uff0c\u4f8b\u5982\\\"\u505c\u706b+\u964d\u606f\\\"=10\u5206\uff0c\\\"\u6218\u4e89\u5347\u7ea7+\u52a0\u606f\\\"=1\u5206\uff0c\u5e76\u8c03\u6574\u9875\u9762\u5c55\u793a\u3002",
  "2026-03-23:\u5bf9\u5df2\u5165\u5e93\u7684RSS\u4e8b\u4ef6\u6d41\u6267\u884c\u91cd\u65b0\u6253\u5206\u5e76\u56de\u5199\u6570\u636e\u5e93\u3002",
  "2026-03-23:\u6253\u5206\u65b9\u5411\u4fee\u6b63\u4e3a\\\"\u5730\u7f18\u7f13\u548c\u9ad8\u5206\uff0c\u7d27\u5f20\u5347\u7ea7\u4f4e\u5206\\\"\uff0c\u5e76\u5bf9\u5b58\u91cf\u4e8b\u4ef6\u91cd\u65b0\u6253\u5206\u3002",
  "2026-03-23:\u7248\u672c\u53f7\u66f4\u65b0\u4e3a 0.24.3\u3002",
  "2026-03-23:\u4fee\u590d\\\"\u6700\u540e\u901a\u7252/\u6700\u540e\u671f\u9650/\u7d27\u5f20\u5c40\u52bf\u52a0\u5267\\\"\u573a\u666f\u4f4e\u5206\u89c4\u5219\uff0c\u5e76\u91cd\u65b0\u56de\u5199\u5b58\u91cf\u4e8b\u4ef6\u8bc4\u5206\u3002",
  "2026-03-23:\u7248\u672c\u53f7\u66f4\u65b0\u4e3a 0.24.4\u3002",
  "2026-03-23:\u65b0\u589e\u7f8e\u503a10Y\u72ec\u7acb\u6570\u636e\u6e90\u7ef4\u62a4\uff08Sina\u4f18\u5148\uff0cFRED\u56de\u9000\uff09\uff0c\u5e76\u4e0e\u9ec4\u91d1\u8054\u52a8\u56fe\u8868\u5206\u6790\u3002",
  "2026-03-23:\u4fee\u590d\u9875\u9762\u591a\u5904\u4e71\u7801\u4e0e\u5b57\u7b26\u663e\u793a\u4e0d\u5168\u95ee\u9898\u3002",
];

function isLikelyGarbledText(text) {
  if (!text) return false;
  return /[?]{2,}|[\ufffd\uE000-\uF8FF]/.test(text);
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// ==================== Loading 状态管理 ====================
function showLoading(taskName = 'default') {
  state.loadingTasks.add(taskName);
  state.isLoading = true;
  updateLoadingUI();
}

function hideLoading(taskName = 'default') {
  state.loadingTasks.delete(taskName);
  if (state.loadingTasks.size === 0) {
    state.isLoading = false;
  }
  updateLoadingUI();
}

function updateLoadingUI() {
  const badge = document.getElementById('schedulerBadge');
  if (badge) {
    if (state.isLoading) {
      badge.textContent = '数据加载中...';
      badge.style.color = '#c57b18';
    } else {
      badge.textContent = '运行中';
      badge.style.color = '#197c58';
    }
  }
}

// ==================== Toast 提示系统 ====================
function showToast(message, type = 'info') {
  // 创建toast容器（如果不存在）
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 10000;
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-width: 400px;
    `;
    document.body.appendChild(container);
  }
  
  // 创建toast元素
  const toast = document.createElement('div');
  const typeColors = {
    'success': '#197c58',
    'error': '#bc4837',
    'warning': '#c57b18',
    'info': '#13796b'
  };
  
  toast.style.cssText = `
    background: ${typeColors[type] || typeColors['info']};
    color: white;
    padding: 14px 18px;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    font-size: 14px;
    animation: slideIn 0.3s ease-out;
    cursor: pointer;
  `;
  
  toast.innerHTML = `
    <div style="display: flex; align-items: center; gap: 10px;">
      <span style="font-size: 18px;">${type === 'success' ? '✓' : type === 'error' ? '✗' : type === 'warning' ? '⚠' : 'ℹ'}</span>
      <span>${escapeHtml(message)}</span>
    </div>
  `;
  
  // 点击关闭
  toast.onclick = () => {
    toast.style.animation = 'slideOut 0.3s ease-in';
    setTimeout(() => toast.remove(), 300);
  };
  
  // 添加到容器
  container.appendChild(toast);
  
  // 3秒后自动关闭
  setTimeout(() => {
    if (toast.parentNode) {
      toast.style.animation = 'slideOut 0.3s ease-in';
      setTimeout(() => toast.remove(), 300);
    }
  }, 3000);
}

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(400px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(400px);
      opacity: 0;
    }
  }
  
  .loading-spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255,255,255,0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;
document.head.appendChild(style);

function loadUpdateLogs() {
  try {
    const raw = localStorage.getItem(UPDATE_LOG_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((item) => item && item.text && item.created_at)
      .filter((item) => !isLikelyGarbledText(String(item.text)));
  } catch (error) {
    return [];
  }
}

function saveUpdateLogs() {
  localStorage.setItem(UPDATE_LOG_STORAGE_KEY, JSON.stringify(state.updateLogs));
}

function appendUpdateLog(text) {
  const content = String(text || "").trim();
  if (!content) return;
  state.updateLogs.unshift({
    text: content,
    created_at: new Date().toISOString(),
  });
  saveUpdateLogs();
  renderUpdateLogList();
}

function ensurePresetUpdateLogs() {
  const existingTexts = new Set((state.updateLogs || []).map((item) => String(item.text || "").trim()));
  let changed = false;
  for (const text of PRESET_UPDATE_LOGS) {
    if (existingTexts.has(text)) continue;
    state.updateLogs.unshift({
      text,
      created_at: new Date().toISOString(),
    });
    changed = true;
  }
  if (changed) {
    saveUpdateLogs();
  }
}

function renderUpdateLogList() {
  const list = document.getElementById("updateLogList");
  if (!list) return;
  if (!state.updateLogs.length) {
    list.innerHTML = `<div class="empty-state">\u6682\u65e0\u66f4\u65b0\u8bb0\u5f55</div>`;
    return;
  }
  list.innerHTML = state.updateLogs
    .map(
      (item) => `
    <article class="update-log-item">
      <span class="update-log-time">${formatTime(item.created_at)}</span>
      <div class="update-log-text">${escapeHtml(item.text)}</div>
    </article>
  `,
    )
    .join("");
}

function openUpdateLogModal() {
  const modal = document.getElementById("updateLogModal");
  if (!modal) return;
  renderUpdateLogList();
  modal.classList.remove("hidden");
}

function closeUpdateLogModal() {
  const modal = document.getElementById("updateLogModal");
  if (!modal) return;
  modal.classList.add("hidden");
}

const pageSizes = {
  overviewSgeAlerts: 4,
  overviewReversalAlerts: 4,
  overviewEvents: 4,
  samples: 6,
  alerts: 6,
  reversalSamples: 6,
  reversalAlerts: 6,
  feedEvents: 5,
  rssFetchRuns: 6,
  notificationLogs: 6,
  fetchRuns: 6,
  reversalRuns: 6,
  us10ySamples: 8,
  us10yRuns: 8,
  geoEvents: 8,
};

const viewMeta = {
  overview: {
    title: "\u603b\u89c8",
    desc: "\u540c\u65f6\u67e5\u770b SGE \u6ea2\u4ef7\u3001\u9ec4\u91d1\u53cd\u8f6c\u7b49\u7ea7\u3001RSS \u547d\u4e2d\u548c\u63a8\u9001\u72b6\u6001\u3002",
  },
  goldWarning: {
    title: "\u9ec4\u91d1\u53cd\u8f6c\u9884\u8b66",
    desc: "\u4e0b\u7ea7\u83dc\u5355\u5305\u542b\u9ec4\u91d1\u53cd\u8f6c\u4e0e\u5341\u5e74\u671f\u7f8e\u503a\u53cd\u8f6c\u8054\u52a8\u5206\u6790\u3002",
  },
  sge: {
    title: "SGE\u6ea2\u4ef7",
    desc: "\u76d1\u63a7\u4eba\u6c11\u5e01\u91d1\u4ef7\u4e0e\u56fd\u9645\u91d1\u6298\u7b97\u4ef7\u5dee\uff0c\u5e76\u89e6\u53d1\u9608\u503c\u9884\u8b66\u3002",
  },
  reversal: {
    title: "\u76d8\u9762\u9884\u8b66",
    desc: "\u76d8\u9762 + RSS + us10y \u8054\u5408\u6253\u5206\uff0c\u8f93\u51fa 1 / 2 / 3 / 4 \u7ea7\u4fe1\u53f7\u3002",
  },
  us10y: {
    title: "\u5341\u5e74\u671f\u7f8e\u503a\u53cd\u8f6c",
    desc: "\u72ec\u7acb\u6570\u636e\u6e90\u7ef4\u62a4\uff0c\u4e0e\u9ec4\u91d1\u4ef7\u683c\u8054\u52a8\u5206\u6790\u3002",
  },
  geoWarning: {
    title: "\u653f\u6cbb\u4e0e\u6218\u4e89\u9884\u8b66",
    desc: "\u57fa\u4e8e RSS \u4e8b\u4ef6\u6d41\u5bf9\u9ec4\u91d1\u4e0a\u6da8\u98ce\u9669\u8fdb\u884c\u6253\u5206\u3002",
  },
  otherWarning: {
    title: "\u5176\u4ed6\u9884\u8b66",
    desc: "\u9884\u7559\u6a21\u5757\uff0c\u540e\u7eed\u53ef\u6269\u5c55\u3002",
  },
  feeds: {
    title: "RSS \u6e90",
    desc: "\u914d\u7f6e\u65b0\u95fb\u6e90\u5e76\u67e5\u770b\u4e8b\u4ef6\u5206\u7c7b\u548c\u6293\u53d6\u8d28\u91cf\u3002",
  },
  push: {
    title: "\u63a8\u9001\u8bbe\u7f6e",
    desc: "\u7ba1\u7406 webhook + secret \u63a8\u9001\u76ee\u6807\u5e76\u8bb0\u5f55\u63a8\u9001\u7ed3\u679c\u3002",
  },
  system: {
    title: "\u7cfb\u7edf\u72b6\u6001",
    desc: "\u67e5\u770b SGE\u3001\u53cd\u8f6c\u4e0e RSS \u8c03\u5ea6\u8fd0\u884c\u72b6\u6001\u3002",
  },
};

function initCharts() {
  const chartIds = ["sgeChart", "sgeDetailChart", "reversalChart", "reversalDetailChart", "us10yLinkChart"];
  chartIds.forEach((id) => {
    const node = document.getElementById(id);
    if (!node) return;
    state.charts[id] = echarts.init(node, null, { renderer: "canvas" });
  });
  bindSgeYAxisZoom(state.charts.sgeChart);
  bindSgeYAxisZoom(state.charts.sgeDetailChart);
}

function resetSgeYAxisRange() {
  state.sgeYAxisRange = { min: 800, max: 1200 };
}

function clampSgeYAxisRange(min, max) {
  const safeMin = Number.isFinite(min) ? min : 800;
  const safeMax = Number.isFinite(max) ? max : 1200;
  const span = Math.max(20, safeMax - safeMin);
  return {
    min: Number(safeMin.toFixed(2)),
    max: Number((safeMin + span).toFixed(2)),
  };
}

function renderSgeChartsOnly() {
  renderSgeChart(state.charts.sgeChart);
  renderSgeChart(state.charts.sgeDetailChart);
}

function zoomSgeYAxisByWheel(delta, anchorRatio = 0.5) {
  const current = state.sgeYAxisRange || { min: 800, max: 1200 };
  const span = Math.max(20, current.max - current.min);
  const factor = delta > 0 ? 0.9 : 1.1;
  const newSpan = Math.min(4000, Math.max(20, span * factor));
  const ratio = Math.min(1, Math.max(0, anchorRatio));
  const center = current.min + span * ratio;
  const nextMin = center - newSpan * ratio;
  const nextMax = center + newSpan * (1 - ratio);
  state.sgeYAxisRange = clampSgeYAxisRange(nextMin, nextMax);
  renderSgeChartsOnly();
}

function bindSgeYAxisZoom(chart) {
  if (!chart || chart.__sgeYAxisWheelBound) return;
  chart.__sgeYAxisWheelBound = true;
  chart.getZr().on("mousewheel", (params) => {
    const nativeEvent = params?.event?.event;
    const wheelDelta = params?.event?.wheelDelta ?? (nativeEvent ? -nativeEvent.deltaY : 0);
    if (!wheelDelta) return;
    const height = Math.max(1, chart.getHeight());
    const offsetY = Number(params?.offsetY ?? height / 2);
    const anchorRatio = 1 - Math.min(1, Math.max(0, offsetY / height));
    zoomSgeYAxisByWheel(wheelDelta, anchorRatio);
    if (nativeEvent && typeof nativeEvent.preventDefault === "function") {
      nativeEvent.preventDefault();
    }
  });
  chart.getZr().on("dblclick", () => {
    resetSgeYAxisRange();
    renderSgeChartsOnly();
  });
}

function formatNumber(value, digits = 4) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "--";
  }
  return Number(value).toFixed(digits);
}

function formatTime(iso) {
  if (!iso) return "--";
  return new Date(iso).toLocaleString("zh-CN", { hour12: false });
}

function formatLevel(level) {
  const map = {
    0: "无信号",
    1: "一级",
    2: "二级",
    3: "三级",
    4: "四级",
  };
  return map[level] || "无信号";
}

function levelClass(level) {
  return `level-${level ?? 0}`;
}

function getActiveTargets(settings = {}) {
  const targets = settings.notification_targets || [];
  return targets.filter((item) => item.enabled);
}

function setText(id, text) {
  const node = document.getElementById(id);
  if (node) node.textContent = text;
}

function getToastHost() {
  let host = document.getElementById("toastHost");
  if (!host) {
    host = document.createElement("div");
    host.id = "toastHost";
    host.className = "toast-host";
    document.body.appendChild(host);
  }
  return host;
}

function showToast(title, message, tone = "success") {
  const host = getToastHost();
  const toast = document.createElement("div");
  toast.className = `toast ${tone}`;
  toast.innerHTML = `<span class="toast-title">${title}</span><span>${message}</span>`;
  host.appendChild(toast);
  window.setTimeout(() => {
    toast.remove();
  }, 3200);
}

function formatErrorMessage(error) {
  if (!error) return "请求失败";
  return String(error.message || error).slice(0, 180);
}

function getCurrentPage(key, totalItems, pageSize) {
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const current = state.pagers[key] || 1;
  if (current > totalPages) {
    state.pagers[key] = totalPages;
    return totalPages;
  }
  return current;
}

function getPagedItems(items, key) {
  const pageSize = pageSizes[key] || 6;
  const page = getCurrentPage(key, items.length, pageSize);
  const start = (page - 1) * pageSize;
  return {
    items: items.slice(start, start + pageSize),
    page,
    pageSize,
    totalPages: Math.max(1, Math.ceil(items.length / pageSize)),
    totalItems: items.length,
  };
}

function renderPager(pagerId, key, totalItems) {
  const node = document.getElementById(pagerId);
  if (!node) return;
  const pageSize = pageSizes[key] || 6;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  if (totalItems <= pageSize) {
    node.innerHTML = "";
    return;
  }
  const page = getCurrentPage(key, totalItems, pageSize);
  const buttons = [];
  
  // 上一页按钮
  buttons.push(`<button class="pager-btn" data-pager="${key}" data-page="${page - 1}" ${page <= 1 ? "disabled" : ""}>上一页</button>`);
  
  // 智能分页：只显示当前页附近的页码
  const maxVisiblePages = 7; // 最多显示7个页码按钮
  const sidePages = 2; // 当前页两侧各显示2页
  
  if (totalPages <= maxVisiblePages + 2) {
    // 总页数较少，显示所有页码
    for (let i = 1; i <= totalPages; i += 1) {
      buttons.push(`<button class="pager-btn ${i === page ? "active" : ""}" data-pager="${key}" data-page="${i}">${i}</button>`);
    }
  } else {
    // 总页数较多，智能显示
    // 始终显示第一页
    buttons.push(`<button class="pager-btn ${page === 1 ? "active" : ""}" data-pager="${key}" data-page="1">1</button>`);
    
    let startPage = Math.max(2, page - sidePages);
    let endPage = Math.min(totalPages - 1, page + sidePages);
    
    // 调整显示范围，确保显示足够的页码
    if (page <= sidePages + 2) {
      endPage = Math.min(totalPages - 1, maxVisiblePages);
    } else if (page >= totalPages - sidePages - 1) {
      startPage = Math.max(2, totalPages - maxVisiblePages);
    }
    
    // 如果开始页不是第2页，显示省略号
    if (startPage > 2) {
      buttons.push(`<span class="pager-ellipsis">...</span>`);
    }
    
    // 显示中间页码
    for (let i = startPage; i <= endPage; i += 1) {
      buttons.push(`<button class="pager-btn ${i === page ? "active" : ""}" data-pager="${key}" data-page="${i}">${i}</button>`);
    }
    
    // 如果结束页不是倒数第2页，显示省略号
    if (endPage < totalPages - 1) {
      buttons.push(`<span class="pager-ellipsis">...</span>`);
    }
    
    // 始终显示最后一页
    buttons.push(`<button class="pager-btn ${page === totalPages ? "active" : ""}" data-pager="${key}" data-page="${totalPages}">${totalPages}</button>`);
  }
  
  // 下一页按钮
  buttons.push(`<button class="pager-btn" data-pager="${key}" data-page="${page + 1}" ${page >= totalPages ? "disabled" : ""}>下一页</button>`);
  
  node.innerHTML = `<span class="pager-meta">第 ${page} / ${totalPages} 页，共 ${totalItems} 条</span>${buttons.join("")}`;
}

async function fetchJson(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res.json();
}

async function fetchJsonOptional(url, options = {}, fallback = {}) {
  try {
    return await fetchJson(url, options);
  } catch (error) {
    return fallback;
  }
}

async function refreshAll() {
  showLoading('refreshAll');
  
  try {
    const [status, sgeHistory, reversalStatus, reversalHistory, us10yStatus, us10yHistory, notificationLogs] = await Promise.all([
      fetchJson("/api/status"),
      fetchJson(`/api/history?range=${state.sgeRange}`),
      fetchJson("/api/reversal/status"),
      fetchJson(`/api/reversal/history?range=${state.reversalRange}`),
      fetchJson("/api/us10y/status"),
      fetchJson(`/api/us10y/history?range=${state.us10yRange}`),
      fetchJsonOptional("/api/notification/logs?limit=120", {}, { items: [] }),
    ]);
    state.status = status;
  state.reversalStatus = reversalStatus;
  state.us10yStatus = us10yStatus;
  state.sgeHistory = sgeHistory.items || [];
  state.reversalHistory = reversalHistory.items || [];
  state.us10yHistory = us10yHistory.items || [];
  state.notificationLogs = notificationLogs.items || [];
  renderAll();
  } catch (error) {
    console.error('数据刷新失败:', error);
    showToast('数据刷新失败: ' + formatErrorMessage(error), 'error');
  } finally {
    hideLoading('refreshAll');
  }
}

function renderAll() {
  if (!state.status || !state.reversalStatus || !state.us10yStatus) return;
  const settings = state.status.settings || {};
  const marketState = state.status.market_state || {};
  const reversalLatest = state.reversalStatus.latest_sample;
  const latest = state.status.latest_sample;
  const activeTargets = getActiveTargets(settings);
  const rssRuns = state.reversalStatus.recent_rss_fetch_runs || [];
  const lastRssRun = rssRuns[0];
  const us10yTenors = settings.us10y_tenors || ["10y"];
  state.us10yActiveTenor = us10yTenors.includes("10y") ? "10y" : us10yTenors[0];
  const latestSamples = state.us10yStatus.latest_samples || {};
  const latestUs10y = latestSamples[state.us10yActiveTenor] || state.us10yStatus.latest_sample;

  setText("schedulerBadge", state.status.scheduler?.running ? "运行中" : "已停止");
  setText("nextRunText", formatTime(state.status.scheduler?.next_run_time));
  setText("overviewPremiumValue", latest?.premium_cny_per_g != null ? `${formatNumber(latest.premium_cny_per_g, 4)} 元/克` : "无数据");
  setText("overviewPremiumMeta", latest ? `${formatTime(latest.fetched_at)} | ${latest.note || ""}` : "等待数据");
  setText("overviewSignalValue", formatLevel(reversalLatest?.signal_level ?? 0));
  setText("overviewSignalMeta", reversalLatest ? `${formatTime(reversalLatest.fetched_at)} | ${reversalLatest.note || ""}` : "等待数据");
  setText("overviewConditionsValue", reversalLatest?.triggered_conditions || "--");
  setText("overviewConditionsMeta", reversalLatest?.note || "price / political / war / us10y");
  const activeFeedsCount = (settings.rss_feed_sources || []).filter(f => f.enabled !== false).length;
  setText("overviewFeedCount", String(activeFeedsCount));
  setText("overviewFeedMeta", `RSS \u9891\u7387 ${settings.rss_poll_interval_seconds ?? "--"} \u79d2`);
  setText("overviewTargetCount", String(activeTargets.length));
  setText("overviewTargetMeta", activeTargets.length ? activeTargets.map((item) => item.name).join(" / ") : "未配置");
  setText("overviewRssValue", lastRssRun ? `${lastRssRun.item_count} 条` : "--");
  setText("overviewRssMeta", lastRssRun ? `${formatTime(lastRssRun.fetched_at)} | ${lastRssRun.success ? "成功" : lastRssRun.error_message || "失败"}` : "等待数据");
  setText("systemSgeState", marketState.sge?.label || "--");
  setText("systemSgeMeta", marketState.sge?.detail || "\u7b49\u5f85\u6570\u636e");
  setText("systemReversalState", marketState.reversal?.label || "--");
  setText("systemReversalMeta", marketState.reversal?.detail || "\u7b49\u5f85\u6570\u636e");
  setText("systemRssState", marketState.rss?.label || "--");
  setText("systemRssMeta", marketState.rss?.detail || "\u7b49\u5f85\u6570\u636e");

  setText("reversalLevelValue", formatLevel(reversalLatest?.signal_level ?? 0));
  setText("reversalLevelMeta", reversalLatest ? `${formatTime(reversalLatest.fetched_at)} | ${reversalLatest.note || ""}` : "等待数据");
  setText("reversalGoldValue", formatNumber(reversalLatest?.gold_price_usd_per_oz, 2));
  setText("reversalFxValue", formatNumber(reversalLatest?.usdcny_rate, 4));
  setText("reversalConditionsValue", reversalLatest?.triggered_conditions || "--");
  setText("us10ySignalValue", latestUs10y?.yield_signal ? "触发" : "无信号");
  setText("us10ySignalMeta", latestUs10y ? `${formatTime(latestUs10y.fetched_at)} | ${latestUs10y.note || ""}` : "等待数据");
  setText("us10yYieldValue", latestUs10y?.yield_pct != null ? `${formatNumber(latestUs10y.yield_pct, 3)}%` : "--");
  setText("us10ySourceValue", latestUs10y?.source || "--");
  setText("us10ySourceMeta", latestUs10y?.note || "等待数据");
  setText("us10yLinkValue", `${state.us10yActiveTenor.toUpperCase()} ${(latestUs10y?.yield_signal ? "偏强" : "中性")}`);

  const signalBadge = document.getElementById("signalBadge");
  signalBadge.textContent = formatLevel(reversalLatest?.signal_level ?? 0);
  signalBadge.className = `signal-pill ${levelClass(reversalLatest?.signal_level ?? 0)}`;

  renderSgeTables();
  renderReversalTables();
  renderEvents();
  renderRuns();
  renderKeywordBoard();
  renderUs10yTables();
  renderNotificationLogs();
  if (!isEditingForm()) {
    fillForms(settings);
  }
  renderCharts();
}

function renderSgeTables() {
  const status = state.status;
  const samples = status.recent_samples || [];
  const alerts = status.recent_alerts || [];
  const samplesPage = getPagedItems(samples, "samples");
  const alertsPage = getPagedItems(alerts, "alerts");
  const overviewAlertsPage = getPagedItems(alerts, "overviewSgeAlerts");
  const samplesBody = document.getElementById("samplesBody");
  if (samplesBody) {
    samplesBody.innerHTML = samplesPage.items.map((item) => `
    <tr>
      <td>${formatTime(item.fetched_at)}</td>
      <td>${formatNumber(item.shfe_price_cny_per_g, 4)}</td>
      <td>${formatNumber(item.london_price_cny_per_g, 4)}</td>
      <td>${item.premium_cny_per_g != null ? `${formatNumber(item.premium_cny_per_g, 4)} 元/克` : "--"}</td>
      <td>${item.alert_triggered ? "已触发" : item.note || "正常"}</td>
    </tr>
  `).join("");
  }
  const alertsBody = document.getElementById("alertsBody");
  if (alertsBody) {
    alertsBody.innerHTML = alertsPage.items.map((item) => `
    <tr>
      <td>${formatTime(item.sent_at)}</td>
      <td>${formatNumber(item.premium_cny_per_g, 4)} 元/克</td>
      <td>${formatNumber(item.threshold_cny_per_g, 4)} 元/克</td>
      <td>${item.success ? "成功" : "失败"}</td>
    </tr>
  `).join("");
  }
  document.getElementById("overviewSgeAlerts").innerHTML = overviewAlertsPage.items.map((item) => `
    <tr>
      <td>${formatTime(item.sent_at)}</td>
      <td>${formatNumber(item.premium_cny_per_g, 4)} 元/克</td>
      <td>${item.success ? "成功" : "失败"}</td>
    </tr>
  `).join("") || `<tr><td colspan="3" class="muted">暂无记录</td></tr>`;
  renderPager("samplesPager", "samples", samples.length);
  renderPager("alertsPager", "alerts", alerts.length);
  renderPager("overviewSgeAlertsPager", "overviewSgeAlerts", alerts.length);
}

function renderReversalTables() {
  const reversalStatus = state.reversalStatus;
  const alerts = reversalStatus.recent_alerts || [];
  const history = state.reversalHistory.slice(0, 20);
  const samplesPage = getPagedItems(history, "reversalSamples");
  const alertsPage = getPagedItems(alerts, "reversalAlerts");
  const overviewAlertsPage = getPagedItems(alerts, "overviewReversalAlerts");
  document.getElementById("reversalSamplesBody").innerHTML = samplesPage.items.map((item) => `
    <tr>
      <td>${formatTime(item.fetched_at)}</td>
      <td>${formatNumber(item.gold_price_usd_per_oz, 2)}</td>
      <td><span class="tag ${levelClass(item.signal_level)}">${formatLevel(item.signal_level)}</span></td>
      <td>${item.triggered_conditions || "--"}</td>
      <td>${item.note || "--"}</td>
    </tr>
  `).join("");
  document.getElementById("reversalAlertsBody").innerHTML = alertsPage.items.map((item) => `
    <tr>
      <td>${formatTime(item.sent_at)}</td>
      <td><span class="tag ${levelClass(item.signal_level)}">${formatLevel(item.signal_level)}</span></td>
      <td>${item.triggered_conditions || "--"}</td>
      <td>${item.success ? "成功" : "失败"}</td>
    </tr>
  `).join("");
  document.getElementById("overviewReversalAlerts").innerHTML = overviewAlertsPage.items.map((item) => `
    <tr>
      <td>${formatTime(item.sent_at)}</td>
      <td>${formatLevel(item.signal_level)}</td>
      <td>${item.triggered_conditions || "--"}</td>
      <td>${item.success ? "成功" : "失败"}</td>
    </tr>
  `).join("") || `<tr><td colspan="4" class="muted">暂无记录</td></tr>`;
  renderPager("reversalSamplesPager", "reversalSamples", history.length);
  renderPager("reversalAlertsPager", "reversalAlerts", alerts.length);
  renderPager("overviewReversalAlertsPager", "overviewReversalAlerts", alerts.length);
}

function renderEvents() {
  const events = filterEvents(state.reversalStatus.recent_events || []);
  const overviewPage = getPagedItems(events, "overviewEvents");
  const feedPage = getPagedItems(events, "feedEvents");
  const geoPage = getPagedItems(events, "geoEvents");
  const scoreClass = (level) => {
    if (level === "高") return "high";
    if (level === "中") return "mid";
    return "low";
  };
  const buildHtml = (items, withScore = false) => items.length ? items.map((item) => {
    const eventType = item.event_type || "all";
    const keywords = (item.matched_keywords || "").split(",").filter(Boolean);
    return `
      <article class="event-card">
        <div class="event-meta">
          <span class="tag ${eventType}">${eventType === "political" ? "政治缓和" : "战争进度"}</span>
          <span class="tag">${item.source || "未知来源"}</span>
          <span class="tag">📥 采集: ${formatTime(item.fetched_at)}</span>
          <span class="tag">📰 发布: ${formatTime(item.published_at || item.fetched_at)}</span>
          ${withScore ? `<span class="tag risk-score ${scoreClass(item.impact_level)}">缓和评分 ${item.impact_score ?? "--"}/10 (${item.impact_level || "低"})</span>` : ""}
        </div>
        <h4>${item.title || "暂无标题"}</h4>
        <p>${item.summary || "暂无摘要"}</p>
        <div class="event-meta">
          ${keywords.map((keyword) => `<span class="tag">${keyword}</span>`).join("")}
          ${withScore ? `<span class="tag">${item.impact_note || "无评分说明"}</span>` : ""}
          ${item.link ? `<a href="${item.link}" target="_blank" rel="noreferrer">查看原文</a>` : ""}
        </div>
      </article>
    `;
  }).join("") : `<div class="empty-state">暂无命中反转条件的 RSS 事件</div>`;
  document.getElementById("overviewEvents").innerHTML = buildHtml(overviewPage.items, false);
  document.getElementById("feedEventList").innerHTML = buildHtml(feedPage.items, false);
  const geoList = document.getElementById("geoEventList");
  if (geoList) geoList.innerHTML = buildHtml(geoPage.items, true);
  renderPager("overviewEventsPager", "overviewEvents", events.length);
  renderPager("feedEventsPager", "feedEvents", events.length);
  renderPager("geoEventsPager", "geoEvents", events.length);
}

function renderRuns() {
  const marketState = state.status.market_state || {};
  const fetchRuns = state.status.recent_fetch_runs || [];
  const reversalRuns = state.reversalStatus.recent_runs || [];
  const rssFetchRuns = state.reversalStatus.recent_rss_fetch_runs || [];
  const rssRunsPage = getPagedItems(rssFetchRuns, "rssFetchRuns");

  if (marketState.sge?.active) {
    const fetchRunsPage = getPagedItems(fetchRuns, "fetchRuns");
    document.getElementById("fetchRunsList").innerHTML = fetchRunsPage.items.length ? fetchRunsPage.items.map((item) => `
      <li>
        <span>${formatTime(item.fetched_at)}</span>
        <span>${item.poll_interval_seconds}s / ${item.duration_ms}ms / ${item.success ? "成功" : item.error_message || "失败"}</span>
      </li>
    `).join("") : `<li class="muted">\u6682\u65e0\u8bb0\u5f55</li>`;
    renderPager("fetchRunsPager", "fetchRuns", fetchRuns.length);
  } else {
    document.getElementById("fetchRunsList").innerHTML = `<li class="muted">当前非 SGE 开盘时段，抓取任务暂不执行。</li>`;
    renderPager("fetchRunsPager", "fetchRuns", 0);
  }

  if (marketState.reversal?.active) {
    const reversalRunsPage = getPagedItems(reversalRuns, "reversalRuns");
    document.getElementById("reversalRunsList").innerHTML = reversalRunsPage.items.length ? reversalRunsPage.items.map((item) => `
      <li>
        <span>${formatTime(item.fetched_at)}</span>
        <span>${item.poll_interval_seconds}s / ${item.duration_ms}ms / RSS异常 ${item.rss_error_count}</span>
        <span>${item.success ? "\u6210\u529f" : item.error_message || "\u5931\u8d25"}</span>
      </li>
    `).join("") : `<li class="muted">\u6682\u65e0\u8bb0\u5f55</li>`;
    renderPager("reversalRunsPager", "reversalRuns", reversalRuns.length);
  } else {
    document.getElementById("reversalRunsList").innerHTML = `<li class="muted">当前未满足反转监控时段，任务暂不执行。</li>`;
    renderPager("reversalRunsPager", "reversalRuns", 0);
  }

  document.getElementById("rssFetchRunsList").innerHTML = rssRunsPage.items.length ? rssRunsPage.items.map((item) => `
    <li>
      <span>${formatTime(item.fetched_at)}</span>
      <span>${item.duration_ms}ms / 条目 ${item.item_count} / 异常 ${item.error_count}</span>
      <span>${item.success ? "\u6210\u529f" : item.error_message || "\u5931\u8d25"}</span>
    </li>
  `).join("") : `<li class="muted">\u6682\u65e0\u8bb0\u5f55</li>`;
  renderPager("rssFetchRunsPager", "rssFetchRuns", rssFetchRuns.length);
}

function renderNotificationLogs() {
  const logs = state.notificationLogs || [];
  const page = getPagedItems(logs, "notificationLogs");
  const rows = page.items.map((item) => `
    <tr>
      <td>${formatTime(item.sent_at)}</td>
      <td>${item.event_type || item.channel || "--"}</td>
      <td>${item.target_name || "--"}</td>
      <td>${item.success ? "成功" : "失败"}</td>
      <td title="${escapeHtml(item.response_text || item.content || "")}">${escapeHtml(item.content || item.response_text || "--")}</td>
    </tr>
  `).join("") || `<tr><td colspan="5" class="muted">暂无推送记录</td></tr>`;
  const body = document.getElementById("notificationLogsBody");
  if (body) body.innerHTML = rows;
  renderPager("notificationLogsPager", "notificationLogs", logs.length);
}

function renderUs10yTables() {
  const samples = state.us10yHistory || [];
  const runs = state.us10yStatus?.recent_runs || [];
  const samplesPage = getPagedItems([...samples].reverse(), "us10ySamples");
  const runsPage = getPagedItems(runs, "us10yRuns");

  const sampleBody = document.getElementById("us10ySamplesBody");
  if (sampleBody) {
    sampleBody.innerHTML = samplesPage.items.map((item) => `
      <tr>
        <td>${formatTime(item.fetched_at)}</td>
        <td>${(item.tenor || "--").toUpperCase()}</td>
        <td>${formatNumber(item.yield_pct, 3)}%</td>
        <td>${item.yield_signal ? "触发" : "无信号"}</td>
        <td>${item.note || "--"}</td>
      </tr>
    `).join("") || `<tr><td colspan="5" class="muted">暂无记录</td></tr>`;
  }

  const runsList = document.getElementById("us10yRunsList");
  if (runsList) {
    runsList.innerHTML = runsPage.items.map((item) => `
      <li>
        <span>${formatTime(item.fetched_at)}</span>
        <span>${item.duration_ms}ms / ${item.success ? "成功" : item.error_message || "失败"}</span>
      </li>
    `).join("") || `<li class="muted">暂无记录</li>`;
  }

  renderPager("us10ySamplesPager", "us10ySamples", samples.length);
  renderPager("us10yRunsPager", "us10yRuns", runs.length);
  renderUs10ySourcesStatus();
}

function renderUs10ySourcesStatus() {
  const latestUs10y = state.us10yStatus?.latest_sample;
  const sources = [
    { name: '东方财富', status: 'unknown', priority: 1 },
    { name: '新浪财经', status: latestUs10y?.source === 'Sina' ? 'healthy' : 'unknown', priority: 2 },
    { name: 'FRED API', status: latestUs10y?.source === 'FRED' ? 'healthy' : 'unknown', priority: 3 }
  ];
  
  if (latestUs10y?.source === 'Sina') {
    sources[0].status = 'error';
    sources[1].status = 'healthy';
  } else if (latestUs10y?.source === 'FRED') {
    sources[0].status = 'error';
    sources[1].status = 'error';
    sources[2].status = 'healthy';
  } else if (latestUs10y?.source === 'EastMoney') {
    sources[0].status = 'healthy';
  }
  
  const container = document.getElementById('us10ySourcesStatus');
  if (container) {
    container.innerHTML = sources.map(src => `
      <div class="source-status-item">
        <span class="source-name">${src.name}</span>
        <div class="source-meta">
          <span class="source-status-badge ${src.status}">${getSourceStatusLabel(src.status)}</span>
          <span class="muted">优先级 ${src.priority}</span>
        </div>
      </div>
    `).join('') || `<div class="empty-state">暂无数据源信息</div>`;
  }
}

function getSourceStatusLabel(status) {
  const labels = {
    'healthy': '正常',
    'degraded': '降级',
    'error': '失败',
    'unknown': '未知'
  };
  return labels[status] || '未知';
}

function renderKeywordBoard() {
  const events = state.reversalStatus.recent_events || [];
  
  // 统计关键词及其命中次数
  const keywordCounts = {};
  events.forEach((item) => {
    const keywords = (item.matched_keywords || "").split(",").filter(Boolean);
    keywords.forEach((keyword) => {
      const cleanKeyword = keyword.trim().replace(/^\[.*?\]/, '');  // 移除前缀标记如[否定]
      if (cleanKeyword) {
        keywordCounts[cleanKeyword] = (keywordCounts[cleanKeyword] || 0) + 1;
      }
    });
  });
  
  // 按命中次数排序
  const sortedKeywords = Object.entries(keywordCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 30);  // 最多显示30个关键词
  
  const container = document.getElementById("eventKeywordList");
  if (container) {
    if (sortedKeywords.length === 0) {
      container.innerHTML = `<div class="empty-state">暂无关键词</div>`;
    } else {
      container.innerHTML = sortedKeywords.map(([keyword, count]) => {
        // 根据命中次数确定权重样式
        let weightClass = '';
        if (count >= 5) {
          weightClass = 'high-frequency';
        } else if (count >= 3) {
          weightClass = 'medium-frequency';
        }
        
        return `<span class="tag ${weightClass}" title="命中 ${count} 次">${escapeHtml(keyword)} <span class="keyword-count">${count}</span></span>`;
      }).join("");
    }
  }
}

function fillForms(settings) {
  const setValue = (id, value) => {
    const node = document.getElementById(id);
    if (node) node.value = value;
  };
  setValue("thresholdInput", settings.premium_threshold ?? 20);
  setValue("intervalInput", settings.poll_interval_seconds ?? 60);
  setValue("cooldownInput", settings.alert_cooldown_seconds ?? 900);
  setValue("timeoutInput", settings.request_timeout_seconds ?? 10);

  setValue("rssIntervalInput", settings.rss_poll_interval_seconds ?? 3600);
  setValue("reversalCooldownInput", settings.reversal_cooldown_seconds ?? 1800);
  setValue("reversalLookbackInput", settings.reversal_price_lookback_minutes ?? 360);
  setValue("reversalReboundInput", settings.reversal_price_rebound_pct ?? 1.2);
  setValue("reversalMaInput", settings.reversal_price_ma_window ?? 15);
  setValue("reversalSignalWindowInput", settings.reversal_signal_window_minutes ?? 180);
  setValue("us10yPollIntervalInput", settings.us10y_poll_interval_seconds ?? 60);
  setValue("us10yDropLookbackHoursInput", settings.us10y_drop_lookback_hours ?? 24);
  setValue("us10yDropThresholdBpInput", settings.us10y_drop_threshold_bp ?? 1.0);
  setValue("us10yCooldownInput", settings.us10y_cooldown_seconds ?? 900);
  const tenors = settings.us10y_tenors || ["10y"];
  const t5 = document.getElementById("us10yTenor5");
  const t10 = document.getElementById("us10yTenor10");
  const t20 = document.getElementById("us10yTenor20");
  if (t5) t5.checked = tenors.includes("5y");
  if (t10) t10.checked = tenors.includes("10y");
  if (t20) t20.checked = tenors.includes("20y");

  renderFeedRows(settings.rss_feed_sources || []);
  renderTargetRows(settings.notification_targets || []);
}

function isEditingForm() {
  const active = document.activeElement;
  return active instanceof HTMLElement && Boolean(active.closest("form"));
}

function renderFeedRows(items) {
  const container = document.getElementById("feedRows");
  container.innerHTML = "";
  const feeds = items.length ? items : [{ name: "", url: "", enabled: true }];
  feeds.forEach((feed) => container.appendChild(createFeedRow(feed)));
}

function createFeedRow(feed = {}) {
  const node = document.getElementById("feedRowTemplate").content.firstElementChild.cloneNode(true);
  node.querySelector(".feed-name-input").value = feed.name || "";
  node.querySelector(".feed-url-input").value = feed.url || "";
  node.querySelector(".feed-enabled-input").checked = feed.enabled !== false;
  node.querySelector(".remove-feed-btn").addEventListener("click", () => {
    if (document.querySelectorAll("#feedRows .editor-row").length > 1) {
      node.remove();
    } else {
      node.querySelector(".feed-name-input").value = "";
      node.querySelector(".feed-url-input").value = "";
      node.querySelector(".feed-enabled-input").checked = true;
    }
  });
  return node;
}

function renderTargetRows(items) {
  const container = document.getElementById("targetRows");
  container.innerHTML = "";
  const targets = items.length ? items : [{ name: "默认推送组", webhook: "", secret: "", enabled: true }];
  targets.forEach((target) => container.appendChild(createTargetRow(target)));
}

function createTargetRow(target = {}) {
  const node = document.getElementById("targetRowTemplate").content.firstElementChild.cloneNode(true);
  node.querySelector(".target-name-input").value = target.name || "默认推送组";
  node.querySelector(".target-webhook-input").value = target.webhook || "";
  node.querySelector(".target-secret-input").value = target.secret || "";
  node.querySelector(".target-enabled-input").checked = target.enabled !== false;
  node.querySelector(".remove-target-btn").addEventListener("click", () => {
    if (document.querySelectorAll("#targetRows .editor-row").length > 1) {
      node.remove();
    } else {
      node.querySelector(".target-name-input").value = "默认推送组";
      node.querySelector(".target-webhook-input").value = "";
      node.querySelector(".target-secret-input").value = "";
      node.querySelector(".target-enabled-input").checked = true;
    }
  });
  return node;
}

function renderCharts() {
  renderSgeChart(state.charts.sgeChart);
  renderSgeChart(state.charts.sgeDetailChart);
  renderReversalChart(state.charts.reversalChart);
  renderReversalChart(state.charts.reversalDetailChart);
  renderUs10yLinkChart(state.charts.us10yLinkChart);
}

function renderSgeChart(chart) {
  if (!chart) return;
  const items = state.sgeHistory;
  if (!items || items.length === 0) return;
  
  const times = items.map((item) => item.fetched_at);
  
  // 计算溢价的合理范围
  const premiums = items.map(item => item.premium_cny_per_g).filter(v => v != null);
  let premiumMin = 0;
  let premiumMax = 5;
  if (premiums.length > 0) {
    const minPremium = Math.min(...premiums);
    const maxPremium = Math.max(...premiums);
    const range = maxPremium - minPremium;
    const padding = Math.max(0.5, range * 0.15);
    premiumMin = Math.max(0, minPremium - padding);
    premiumMax = maxPremium + padding;
  }
  
  // 计算价格轴的合理范围（自动适配数据，放大细微差异）
  const prices = items.flatMap(item => [item.shfe_price_cny_per_g, item.london_price_cny_per_g]).filter(v => v != null);
  let yMin = 800;
  let yMax = 1200;
  if (prices.length > 0 && !state.sgeYAxisRange) {
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const range = maxPrice - minPrice;
    const padding = Math.max(5, range * 0.2);  // 至少留5元/克边距
    yMin = Math.floor(minPrice - padding);
    yMax = Math.ceil(maxPrice + padding);
  } else if (state.sgeYAxisRange) {
    // 用户手动缩放后使用用户设置
    yMin = state.sgeYAxisRange.min;
    yMax = state.sgeYAxisRange.max;
  }
  
  // 计算时间范围并生成每小时刻度
  const timestamps = times.map(t => new Date(t).getTime());
  const minTime = Math.min(...timestamps);
  const maxTime = Math.max(...timestamps);
  
  // 将开始时间向下取整到整点，结束时间向上取整到整点
  const startHour = new Date(minTime);
  startHour.setMinutes(0, 0, 0);
  const endHour = new Date(maxTime);
  endHour.setMinutes(0, 0, 0);
  if (endHour.getTime() < maxTime) {
    endHour.setHours(endHour.getHours() + 1);
  }
  
  // 固定使用1小时刻度间隔
  const tickInterval = 3600000;  // 1小时 = 3600000毫秒
  
  chart.setOption({
    backgroundColor: "transparent",
    tooltip: { 
      trigger: "axis",
      formatter: function(params) {
        const time = new Date(params[0].value[0]).toLocaleString('zh-CN', { 
          month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false 
        });
        let html = `<div style="margin-bottom:4px;font-weight:500;">${time}</div>`;
        params.forEach(param => {
          html += `<div>${param.marker} ${param.seriesName}: ${param.value[1]?.toFixed(4) ?? '--'}</div>`;
        });
        return html;
      }
    },
    legend: { top: 6, textStyle: { color: "#5f6b7c" }, data: ["溢价", "人民币金价(现货)", "国际金折算"] },
    grid: { left: 50, right: 50, top: 52, bottom: 56 },
    xAxis: { 
      type: "time",
      min: startHour.getTime(),
      max: endHour.getTime(),
      interval: tickInterval,  // 根据时间跨度动态调整刻度间隔
      axisLabel: { 
        color: "#5f6b7c",
        showMinLabel: true,
        showMaxLabel: true,
        formatter: function(value) {
          const date = new Date(value);
          const hours = date.getHours();
          const minutes = date.getMinutes();
          // 如果是00:00，只显示日期的"日"部分
          if (hours === 0 && minutes === 0) {
            return String(date.getDate());
          }
          // 否则只显示时间
          return `${String(hours).padStart(2, '0')}:00`;
        }
      },
      axisTick: {
        alignWithLabel: true
      },
      axisLine: { lineStyle: { color: "#b8c1cb" } },
      splitLine: { show: true, lineStyle: { color: "rgba(18,32,51,0.05)", type: "dashed" } },
      minorTick: { show: false }
    },
    yAxis: [
      {
        type: "value",
        name: "元/克",
        nameTextStyle: { color: "#5f6b7c", padding: [0, 40, 0, 0] },
        min: yMin,
        max: yMax,
        axisLabel: { color: "#5f6b7c" },
        splitLine: { lineStyle: { color: "rgba(18,32,51,0.08)" } },
      },
      {
        type: "value",
        name: "溢价",
        nameTextStyle: { color: "#5f6b7c", padding: [0, 0, 0, 40] },
        min: premiumMin,
        max: premiumMax,
        axisLabel: { 
          color: "#5f6b7c",
          formatter: '{value}'
        },
        splitLine: { show: false },
      },
    ],
    dataZoom: [{ type: "inside", filterMode: "none", zoomOnMouseWheel: false }],
    series: [
      {
        name: "溢价",
        type: "line",
        yAxisIndex: 1,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2, color: "#5470c6" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(84,112,198,0.20)" },
            { offset: 1, color: "rgba(84,112,198,0.02)" },
          ]),
        },
        data: times.map((time, index) => [time, items[index].premium_cny_per_g]),
      },
      {
        name: "人民币金价(现货)",
        type: "line",
        yAxisIndex: 0,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2, color: "#91cc75" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(145,204,117,0.15)" },
            { offset: 1, color: "rgba(145,204,117,0.02)" },
          ]),
        },
        data: times.map((time, index) => [time, items[index].shfe_price_cny_per_g]),
      },
      {
        name: "国际金折算",
        type: "line",
        yAxisIndex: 0,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2, color: "#fac858" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(250,200,88,0.15)" },
            { offset: 1, color: "rgba(250,200,88,0.02)" },
          ]),
        },
        data: times.map((time, index) => [time, items[index].london_price_cny_per_g]),
      },
    ],
  });
}

function renderReversalChart(chart) {
  if (!chart) return;
  const allItems = state.reversalHistory;
  if (!allItems || allItems.length === 0) return;
  
  console.log(`[反转图表] 原始数据数量: ${allItems.length}`);
  
  // 根据时间范围动态调整采样间隔
  const range = state.reversalRange;
  let samplingMinutes;
  let tickIntervalMs;
  
  if (range === "1H") {
    samplingMinutes = 5;  // 1小时范围：每5分钟1个点
    tickIntervalMs = 15 * 60 * 1000;  // X轴显示：每15分钟一个刻度
  } else if (range === "1D") {
    samplingMinutes = 15;  // 1天范围：每15分钟1个点
    tickIntervalMs = 60 * 60 * 1000;  // X轴显示：每1小时一个刻度
  } else {  // 1W
    samplingMinutes = 60;  // 1周范围：每1小时1个点
    tickIntervalMs = 4 * 60 * 60 * 1000;  // X轴显示：每4小时一个刻度
  }
  
  // 降采样：按指定时间间隔保留数据点
  const samplingMap = new Map();
  allItems.forEach(item => {
    const date = new Date(item.fetched_at);
    const timeSlot = Math.floor(date.getTime() / (samplingMinutes * 60 * 1000));
    const slotKey = timeSlot.toString();
    
    if (!samplingMap.has(slotKey)) {
      samplingMap.set(slotKey, item);
    } else {
      // 如果该时间槽已有数据，选择更接近槽起点的那个
      const existing = samplingMap.get(slotKey);
      const existingTime = new Date(existing.fetched_at).getTime();
      const currentTime = date.getTime();
      const slotStartTime = timeSlot * samplingMinutes * 60 * 1000;
      
      if (Math.abs(currentTime - slotStartTime) < Math.abs(existingTime - slotStartTime)) {
        samplingMap.set(slotKey, item);
      }
    }
  });
  
  // 提取降采样后的数据并按时间排序
  const items = Array.from(samplingMap.values()).map(item => {
    // 将数据点的时间戳调整到时间槽起点
    const date = new Date(item.fetched_at);
    const timeSlot = Math.floor(date.getTime() / (samplingMinutes * 60 * 1000));
    const alignedTime = new Date(timeSlot * samplingMinutes * 60 * 1000);
    
    return {
      ...item,
      fetched_at: alignedTime.toISOString()
    };
  }).sort((a, b) => 
    new Date(a.fetched_at).getTime() - new Date(b.fetched_at).getTime()
  );
  
  console.log(`[反转图表] 降采样后数量: ${items.length} (间隔: ${samplingMinutes}分钟)`);
  console.log(`[反转图表] 降采样后的时间点:`, items.map(item => item.fetched_at));
  
  const times = items.map((item) => item.fetched_at);
  const mapSignalToY = (level) => {
    if (level === 1) return 4;
    if (level === 2) return 3;
    if (level === 3) return 2;
    if (level === 4) return 1;
    return 0.2;
  };

  // 计算时间范围并动态调整刻度间隔
  const timestamps = times.map(t => new Date(t).getTime());
  const minTime = Math.min(...timestamps);
  const maxTime = Math.max(...timestamps);
  
  // 根据采样间隔调整时间范围边界
  let startTime, endTime;
  if (samplingMinutes === 15) {
    // 15分钟间隔：向下/向上取整到15分钟
    startTime = new Date(Math.floor(minTime / (15 * 60 * 1000)) * 15 * 60 * 1000);
    endTime = new Date(Math.ceil(maxTime / (15 * 60 * 1000)) * 15 * 60 * 1000);
  } else if (samplingMinutes === 60) {
    // 1小时间隔：向下/向上取整到整点
    startTime = new Date(minTime);
    startTime.setMinutes(0, 0, 0);
    endTime = new Date(maxTime);
    endTime.setMinutes(0, 0, 0);
    if (endTime.getTime() < maxTime) {
      endTime.setHours(endTime.getHours() + 1);
    }
  } else {
    // 4小时间隔：向下/向上取整到4小时
    startTime = new Date(Math.floor(minTime / (4 * 60 * 60 * 1000)) * 4 * 60 * 60 * 1000);
    endTime = new Date(Math.ceil(maxTime / (4 * 60 * 60 * 1000)) * 4 * 60 * 60 * 1000);
  }

  chart.setOption({
    backgroundColor: "transparent",
    tooltip: { 
      trigger: "axis",
      formatter: function(params) {
        const time = new Date(params[0].value[0]).toLocaleString('zh-CN', { 
          month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false 
        });
        let html = `<div style="margin-bottom:4px;font-weight:500;">${time}</div>`;
        params.forEach(param => {
          if (param.seriesName === '反转信号') {
            const level = param.value[1];
            const levelMap = { 4: '一级', 3: '二级', 2: '三级', 1: '四级', 0: '无信号' };
            const levelText = levelMap[Math.round(level)] || level.toFixed(1);
            html += `<div>${param.marker} ${param.seriesName}: ${levelText}</div>`;
          } else {
            html += `<div>${param.marker} ${param.seriesName}: ${param.value[1]?.toFixed(2) ?? '--'}</div>`;
          }
        });
        return html;
      }
    },
    legend: { top: 6, textStyle: { color: "#5f6b7c" }, data: ["现货金", "反转信号"] },
    grid: { left: 50, right: 50, top: 52, bottom: 56 },
    xAxis: { 
      type: "time",
      min: startTime.getTime(),
      max: endTime.getTime(),
      minInterval: tickIntervalMs,
      maxInterval: tickIntervalMs,
      axisLabel: { 
        color: "#5f6b7c",
        showMinLabel: true,
        showMaxLabel: true,
        hideOverlap: true,
        formatter: function(value) {
          const date = new Date(value);
          const hours = date.getHours();
          const minutes = date.getMinutes();
          
          if (samplingMinutes === 15) {
            // 15分钟间隔：显示 HH:MM
            return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
          } else if (hours === 0 && minutes === 0) {
            // 跨天：显示日期
            return `${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
          } else if (samplingMinutes === 60) {
            // 1小时间隔：显示 HH:00
            return `${String(hours).padStart(2, '0')}:00`;
          } else {
            // 4小时间隔：显示 HH:00
            return `${String(hours).padStart(2, '0')}:00`;
          }
        }
      },
      axisTick: {
        alignWithLabel: true
      },
      axisLine: { lineStyle: { color: "#b8c1cb" } },
      splitLine: { show: true, lineStyle: { color: "rgba(18,32,51,0.05)", type: "dashed" } },
      minorTick: { show: false }
    },
    yAxis: [
      {
        type: "value",
        name: "美元/盎司",
        nameTextStyle: { color: "#5f6b7c", padding: [0, 40, 0, 0] },
        scale: true,
        axisLabel: { color: "#5f6b7c" },
        splitLine: { lineStyle: { color: "rgba(18,32,51,0.08)" } },
      },
      {
        type: "value",
        name: "反转等级",
        nameTextStyle: { color: "#5f6b7c", padding: [0, 0, 0, 40] },
        min: 0,
        max: 4.2,
        interval: 1,
        axisLabel: {
          color: "#5f6b7c",
          formatter: (value) => {
            if (value === 4) return "一级";
            if (value === 3) return "二级";
            if (value === 2) return "三级";
            if (value === 1) return "四级";
            if (value === 0) return "无信号";
            return "";
          },
        },
        splitLine: { show: false },
      },
    ],
    dataZoom: [{ type: "inside", filterMode: "none" }],
    series: [
      {
        name: "现货金",
        type: "line",
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 3, color: "#13796b" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(19,121,107,0.24)" },
            { offset: 1, color: "rgba(19,121,107,0.02)" },
          ]),
        },
        data: times.map((time, index) => [time, items[index].gold_price_usd_per_oz]),
      },
      {
        name: "反转信号",
        type: "line",
        yAxisIndex: 1,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2, color: "#bc4837" },
        itemStyle: { color: "#bc4837" },
        data: times.map((time, index) => [time, mapSignalToY(items[index].signal_level)]),
      },
    ],
  });
}

function renderUs10yLinkChart(chart) {
  if (!chart) return;
  const goldItems = state.reversalHistory || [];
  const activeTenor = state.us10yActiveTenor || "10y";
  const us10yItems = (state.us10yHistory || []).filter((item) => (item.tenor || "10y") === activeTenor);
  
  if (goldItems.length === 0 && us10yItems.length === 0) return;
  chart.setOption({
    backgroundColor: "transparent",
    tooltip: { 
      trigger: "axis",
      formatter: function(params) {
        const time = new Date(params[0].value[0]).toLocaleString('zh-CN', { 
          month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false 
        });
        let html = `<div style="margin-bottom:4px;font-weight:500;">${time}</div>`;
        params.forEach(param => {
          const value = param.value[1];
          const formatted = param.seriesName.includes('美债') ? value?.toFixed(3) : value?.toFixed(2);
          html += `<div>${param.marker} ${param.seriesName}: ${formatted ?? '--'}</div>`;
        });
        return html;
      }
    },
    legend: { top: 6, textStyle: { color: "#5f6b7c" }, data: ["现货金", `美债${activeTenor.toUpperCase()}`] },
    grid: { left: 50, right: 50, top: 52, bottom: 56 },
    xAxis: { 
      type: "time",
      minInterval: 3600000,
      axisLabel: { 
        color: "#5f6b7c",
        hideOverlap: true,
        showMinLabel: true,
        showMaxLabel: true,
        formatter: function(value) {
          const date = new Date(value);
          const hours = date.getHours();
          const minutes = date.getMinutes();
          if (hours === 0 && minutes === 0) {
            return `${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
          }
          return `${String(hours).padStart(2, '0')}:00`;
        }
      },
      axisTick: {
        alignWithLabel: true
      },
      axisLine: { lineStyle: { color: "#b8c1cb" } },
      splitLine: { show: true, lineStyle: { color: "rgba(18,32,51,0.05)", type: "dashed" } },
      minorTick: { show: false }
    },
    yAxis: [
      {
        type: "value",
        name: "美元/盎司",
        nameTextStyle: { color: "#5f6b7c", padding: [0, 40, 0, 0] },
        scale: true,
        axisLabel: { color: "#5f6b7c" },
        splitLine: { lineStyle: { color: "rgba(18,32,51,0.08)" } },
      },
      {
        type: "value",
        name: "%",
        nameTextStyle: { color: "#5f6b7c", padding: [0, 0, 0, 40] },
        scale: true,
        axisLabel: { color: "#5f6b7c" },
        splitLine: { show: false },
      },
    ],
    dataZoom: [
      { type: "inside", filterMode: "none" },
      { type: "inside", filterMode: "none", yAxisIndex: [0, 1], zoomOnMouseWheel: true },
    ],
    series: [
      {
        name: "现货金",
        type: "line",
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2.5, color: "#13796b" },
        data: goldItems.map((item) => [item.fetched_at, item.gold_price_usd_per_oz]),
      },
      {
        name: `美债${activeTenor.toUpperCase()}`,
        type: "line",
        yAxisIndex: 1,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2, color: "#c04f2d" },
        data: us10yItems.map((item) => [item.fetched_at, item.yield_pct]),
      },
    ],
  });
}

function filterEvents(events) {
  if (state.eventFilter === "all") return events;
  return events.filter((item) => item.event_type === state.eventFilter);
}

function switchView(view) {
  state.activeView = view;
  document.querySelectorAll(".menu-btn").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
  document.querySelectorAll(".view").forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.viewPanel === view);
  });
  const meta = viewMeta[view] || viewMeta.overview;
  setText("heroTitle", meta.title);
  setText("heroDesc", meta.desc);
  window.dispatchEvent(new Event("resize"));
}

function syncRangeButtons() {
  document.querySelectorAll(".range-btn").forEach((button) => {
    const chart = button.dataset.chart;
    const activeRange = chart === "reversal"
      ? state.reversalRange
      : chart === "us10y"
        ? state.us10yRange
        : state.sgeRange;
    button.classList.toggle("active", button.dataset.range === activeRange);
  });
}

function syncEventFilterButtons() {
  document.querySelectorAll(".filter-btn").forEach((button) => {
    button.classList.toggle("active", button.dataset.eventFilter === state.eventFilter);
  });
}

async function saveSgeSettings(event) {
  event.preventDefault();
  const payload = {
    premium_threshold: Number(document.getElementById("thresholdInput").value),
    poll_interval_seconds: Number(document.getElementById("intervalInput").value),
    alert_cooldown_seconds: Number(document.getElementById("cooldownInput").value),
    request_timeout_seconds: Number(document.getElementById("timeoutInput").value),
  };
  try {
    await fetchJson("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await refreshAll();
    showToast("保存成功", `已更新 SGE 设置：阈值 ${payload.premium_threshold} 元/克，频率 ${payload.poll_interval_seconds}s。`);
  } catch (error) {
    showToast("保存失败", `SGE 设置更新失败：${formatErrorMessage(error)}`, "error");
  }
}

async function saveReversalSettings(event) {
  event.preventDefault();
  const payload = {
    reversal_cooldown_seconds: Number(document.getElementById("reversalCooldownInput").value),
    reversal_price_lookback_minutes: Number(document.getElementById("reversalLookbackInput").value),
    reversal_price_rebound_pct: Number(document.getElementById("reversalReboundInput").value),
    reversal_price_ma_window: Number(document.getElementById("reversalMaInput").value),
    reversal_signal_window_minutes: Number(document.getElementById("reversalSignalWindowInput").value),
  };
  try {
    await fetchJson("/api/reversal/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await refreshAll();
    showToast("保存成功", "反转参数已更新。");
  } catch (error) {
    showToast("执行失败", `执行反转监控失败：${formatErrorMessage(error)}`, "error");
  }
}

async function saveFeedSettings(event) {
  event.preventDefault();
  const rssFeedSources = [...document.querySelectorAll("#feedRows .editor-row")].map((row) => ({
    name: row.querySelector(".feed-name-input").value.trim() || "未命名RSS源",
    url: row.querySelector(".feed-url-input").value.trim(),
    enabled: row.querySelector(".feed-enabled-input").checked,
  })).filter((item) => item.url);
  const payload = {
    rss_feed_sources: rssFeedSources,
    rss_poll_interval_seconds: Number(document.getElementById("rssIntervalInput").value),
  };
  try {
    await fetchJson("/api/reversal/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await refreshAll();
    showToast("保存成功", `已保存 ${rssFeedSources.length} 个 RSS 源。`);
  } catch (error) {
    showToast("保存失败", `RSS 配置更新失败：${formatErrorMessage(error)}`, "error");
  }
}

async function saveNotificationSettings(event) {
  event.preventDefault();
  const targets = [...document.querySelectorAll("#targetRows .editor-row")].map((row) => ({
    name: row.querySelector(".target-name-input").value.trim() || "\u9ed8\u8ba4\u63a8\u9001\u7ec4",
    webhook: row.querySelector(".target-webhook-input").value.trim(),
    secret: row.querySelector(".target-secret-input").value.trim(),
    enabled: row.querySelector(".target-enabled-input").checked,
  })).filter((item) => item.webhook);

  const firstTarget = targets[0] || { webhook: "", secret: "" };
  try {
    await fetchJson("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        notification_targets: targets,
        dingtalk_webhook: firstTarget.webhook,
        dingtalk_secret: firstTarget.secret,
      }),
    });
    await refreshAll();
    showToast("保存成功", `已保存 ${targets.length} 个推送组。`);
  } catch (error) {
    showToast("保存失败", `参数更新失败：${formatErrorMessage(error)}`, "error");
  }
}

async function saveUs10ySettings(event) {
  event.preventDefault();
  const tenors = [];
  if (document.getElementById("us10yTenor5")?.checked) tenors.push("5y");
  if (document.getElementById("us10yTenor10")?.checked) tenors.push("10y");
  if (document.getElementById("us10yTenor20")?.checked) tenors.push("20y");
  if (!tenors.length) tenors.push("10y");
  const payload = {
    us10y_poll_interval_seconds: Number(document.getElementById("us10yPollIntervalInput").value),
    us10y_drop_lookback_hours: Number(document.getElementById("us10yDropLookbackHoursInput").value),
    us10y_drop_threshold_bp: Number(document.getElementById("us10yDropThresholdBpInput").value),
    us10y_cooldown_seconds: Number(document.getElementById("us10yCooldownInput").value),
    us10y_tenors: tenors,
  };
  try {
    await fetchJson("/api/reversal/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await refreshAll();
    showToast("保存成功", `已保存美债参数：${tenors.join(", ").toUpperCase()} / ${payload.us10y_drop_lookback_hours}h / ${payload.us10y_drop_threshold_bp}bp`);
  } catch (error) {
    showToast("保存失败", `美债参数保存失败：${formatErrorMessage(error)}`, "error");
  }
}

async function runUs10yMonitor() {
  try {
    await fetchJson("/api/us10y/run-once", { method: "POST" });
    await refreshAll();
    showToast("执行成功", "已立即采样并评估美债收益率。");
  } catch (error) {
    showToast("执行失败", `美债采样失败：${formatErrorMessage(error)}`, "error");
  }
}

async function runAllMonitors() {
  try {
    await fetchJson("/api/run-once", { method: "POST" });
    await refreshAll();
    showToast("执行成功", "已立即执行 SGE + 反转 + RSS。");
  } catch (error) {
    showToast("执行失败", `执行 SGE + 反转 + RSS 失败：${formatErrorMessage(error)}`, "error");
  }
}

async function runReversalMonitor() {
  try {
    await fetchJson("/api/reversal/run-once", { method: "POST" });
    await refreshAll();
    showToast("执行成功", "已立即执行反转监控。");
  } catch (error) {
    showToast("执行失败", `执行反转监控失败：${formatErrorMessage(error)}`, "error");
  }
}

async function runRssMonitor() {
  try {
    await fetchJson("/api/reversal/rss-run-once", { method: "POST" });
    await refreshAll();
    showToast("执行成功", "已立即执行 RSS 抓取。");
  } catch (error) {
    showToast("执行失败", `RSS 抓取失败：${formatErrorMessage(error)}`, "error");
  }
}

async function sendTestAlert() {
  const level = Number(document.getElementById("testAlertLevel").value);
  const note = document.getElementById("testAlertNote").value.trim();
  try {
    const result = await fetchJson("/api/reversal/test-alert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ level, note }),
    });
    showToast(
      result.success ? "推送成功" : "推送失败",
      result.success ? `已发送${formatLevel(level)}测试推送` : result.response_text,
      result.success ? "success" : "error",
    );
  } catch (error) {
    showToast("推送失败", `测试推送失败：${formatErrorMessage(error)}`, "error");
  }
}

function bindEvents() {
  const bindClick = (id, handler) => {
    const node = document.getElementById(id);
    if (node) node.addEventListener("click", handler);
  };
  const bindSubmit = (id, handler) => {
    const node = document.getElementById(id);
    if (node) node.addEventListener("submit", handler);
  };
  document.addEventListener("click", (event) => {
    const button = event.target.closest(".pager-btn[data-pager]");
    if (!button || button.disabled) return;
    const key = button.dataset.pager;
    const page = Number(button.dataset.page);
    if (!key || Number.isNaN(page) || page < 1) return;
    state.pagers[key] = page;
    renderAll();
  });

  document.querySelectorAll(".menu-btn").forEach((button) => {
    button.addEventListener("click", () => {
      const view = button.dataset.view;
      if (view === "goldWarning") {
        switchView("sge");
        return;
      }
      switchView(view);
    });
  });

  // 使用事件委托处理range按钮点击
  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".range-btn");
    if (!button) return;
    
    console.log(`[范围按钮点击] Chart: ${button.dataset.chart}, Range: ${button.dataset.range}`);
    
    if (button.dataset.chart === "reversal") {
      state.reversalRange = button.dataset.range;
      console.log(`[范围更新] reversalRange 已更新为: ${state.reversalRange}`);
    } else if (button.dataset.chart === "us10y") {
      state.us10yRange = button.dataset.range;
    } else {
      state.sgeRange = button.dataset.range;
    }
    syncRangeButtons();
    console.log(`[开始刷新] 即将调用 refreshAll()...`);
    await refreshAll();
    console.log(`[刷新完成] refreshAll() 执行完毕`);
  });

  document.querySelectorAll(".filter-btn").forEach((button) => {
    button.addEventListener("click", () => {
      state.eventFilter = button.dataset.eventFilter;
      syncEventFilterButtons();
      renderEvents();
    });
  });

  bindSubmit("sgeSettingsForm", saveSgeSettings);
  bindSubmit("reversalSettingsForm", saveReversalSettings);
  bindSubmit("us10ySettingsForm", saveUs10ySettings);
  bindSubmit("feedSettingsForm", saveFeedSettings);
  bindSubmit("notificationSettingsForm", saveNotificationSettings);

  bindClick("runAllBtn", runAllMonitors);
  bindClick("runReversalBtn", runReversalMonitor);
  bindClick("runUs10yBtn", runUs10yMonitor);
  bindClick("fetchRssBtn", runRssMonitor);
  bindClick("refreshBtn", refreshAll);
  bindClick("testAlertBtn", sendTestAlert);
  bindClick("updateLogBtn", openUpdateLogModal);
  bindClick("closeUpdateLogBtn", closeUpdateLogModal);
  bindClick("addUpdateLogEntryBtn", () => {
    const text = window.prompt("请输入更新记录内容");
    if (!text || !text.trim()) return;
    appendUpdateLog(text.trim());
  });
  bindClick("clearUpdateLogBtn", () => {
    const confirmed = window.confirm("\u786e\u8ba4\u6e05\u7a7a\u66f4\u65b0\u8bb0\u5f55\u5417\uff1f");
    if (!confirmed) return;
    state.updateLogs = [];
    saveUpdateLogs();
    renderUpdateLogList();
  });
  document.querySelectorAll("[data-close-update-log]").forEach((node) => {
    node.addEventListener("click", closeUpdateLogModal);
  });

  bindClick("addFeedBtn", () => {
    document.getElementById("feedRows").appendChild(createFeedRow({ name: "", url: "", enabled: true }));
  });
  bindClick("addTargetBtn", () => {
    document.getElementById("targetRows").appendChild(createTargetRow({ name: "默认推送组", enabled: true }));
  });

  window.addEventListener("resize", () => {
    Object.values(state.charts).forEach((chart) => chart.resize());
  });
}

state.updateLogs = loadUpdateLogs();
ensurePresetUpdateLogs();
renderUpdateLogList();
setText("appVersionText", APP_VERSION);

initCharts();
bindEvents();
syncRangeButtons();
syncEventFilterButtons();
switchView("overview");

refreshAll().catch((error) => {
  setText("heroDesc", error.message);
  showToast('初始加载失败', 'error');
});

setInterval(() => {
  refreshAll().catch((error) => {
    console.error('定时刷新失败:', error);
  });
}, 15000);
