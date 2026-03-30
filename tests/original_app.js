  % Total    % Received % Xferd  Average Speed  Time    Time    Time   Current
                                 Dload  Upload  Total   Spent   Left   Speed

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
};

const UPDATE_LOG_STORAGE_KEY = "sge-monitor-update-logs";
const APP_VERSION = "0.24.4";
const PRESET_UPDATE_LOGS = [
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
    0: "鏃犱俊鍙?,
    1: "涓€绾?,
    2: "浜岀骇",
    3: "涓夌骇",
    4: "鍥涚骇",
  };
  return map[level] || "鏃犱俊鍙?;
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
  if (!error) return "璇锋眰澶辫触";
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
  buttons.push(`<button class="pager-btn" data-pager="${key}" data-page="${page - 1}" ${page <= 1 ? "disabled" : ""}>涓婁竴椤?/button>`);
  for (let i = 1; i <= totalPages; i += 1) {
    buttons.push(`<button class="pager-btn ${i === page ? "active" : ""}" data-pager="${key}" data-page="${i}">${i}</button>`);
  }
  buttons.push(`<button class="pager-btn" data-pager="${key}" data-page="${page + 1}" ${page >= totalPages ? "disabled" : ""}>涓嬩竴椤?/button>`);
  node.innerHTML = `<span class="pager-meta">绗?${page} / ${totalPages} 椤碉紝鍏?${totalItems} 鏉?/span>${buttons.join("")}`;
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

  setText("schedulerBadge", state.status.scheduler?.running ? "杩愯涓? : "宸插仠姝?);
  setText("nextRunText", formatTime(state.status.scheduler?.next_run_time));
  setText("overviewPremiumValue", latest?.premium_cny_per_g != null ? `${formatNumber(latest.premium_cny_per_g, 4)} 鍏?鍏媊 : "鏃犳暟鎹?);
  setText("overviewPremiumMeta", latest ? `${formatTime(latest.fetched_at)} | ${latest.note || ""}` : "绛夊緟鏁版嵁");
  setText("overviewSignalValue", formatLevel(reversalLatest?.signal_level ?? 0));
  setText("overviewSignalMeta", reversalLatest ? `${formatTime(reversalLatest.fetched_at)} | ${reversalLatest.note || ""}` : "绛夊緟鏁版嵁");
  setText("overviewConditionsValue", reversalLatest?.triggered_conditions || "--");
  setText("overviewConditionsMeta", reversalLatest?.note || "price / political / war / us10y");
  setText("overviewFeedCount", String((settings.rss_feed_urls || []).length));
  setText("overviewFeedMeta", `RSS \u9891\u7387 ${settings.rss_poll_interval_seconds ?? "--"} \u79d2`);
  setText("overviewTargetCount", String(activeTargets.length));
  setText("overviewTargetMeta", activeTargets.length ? activeTargets.map((item) => item.name).join(" / ") : "鏈厤缃?);
  setText("overviewRssValue", lastRssRun ? `${lastRssRun.item_count} 鏉 : "--");
  setText("overviewRssMeta", lastRssRun ? `${formatTime(lastRssRun.fetched_at)} | ${lastRssRun.success ? "鎴愬姛" : lastRssRun.error_message || "澶辫触"}` : "绛夊緟鏁版嵁");
  setText("systemSgeState", marketState.sge?.label || "--");
  setText("systemSgeMeta", marketState.sge?.detail || "\u7b49\u5f85\u6570\u636e");
  setText("systemReversalState", marketState.reversal?.label || "--");
  setText("systemReversalMeta", marketState.reversal?.detail || "\u7b49\u5f85\u6570\u636e");
  setText("systemRssState", marketState.rss?.label || "--");
  setText("systemRssMeta", marketState.rss?.detail || "\u7b49\u5f85\u6570\u636e");

  setText("reversalLevelValue", formatLevel(reversalLatest?.signal_level ?? 0));
  setText("reversalLevelMeta", reversalLatest ? `${formatTime(reversalLatest.fetched_at)} | ${reversalLatest.note || ""}` : "绛夊緟鏁版嵁");
  setText("reversalGoldValue", formatNumber(reversalLatest?.gold_price_usd_per_oz, 2));
  setText("reversalFxValue", formatNumber(reversalLatest?.usdcny_rate, 4));
  setText("reversalConditionsValue", reversalLatest?.triggered_conditions || "--");
  setText("us10ySignalValue", latestUs10y?.yield_signal ? "瑙﹀彂" : "鏃犱俊鍙?);
  setText("us10ySignalMeta", latestUs10y ? `${formatTime(latestUs10y.fetched_at)} | ${latestUs10y.note || ""}` : "绛夊緟鏁版嵁");
  setText("us10yYieldValue", latestUs10y?.yield_pct != null ? `${formatNumber(latestUs10y.yield_pct, 3)}%` : "--");
  setText("us10ySourceValue", latestUs10y?.source || "--");
  setText("us10ySourceMeta", latestUs10y?.note || "绛夊緟鏁版嵁");
  setText("us10yLinkValue", `${state.us10yActiveTenor.toUpperCase()} ${(latestUs10y?.yield_signal ? "鍋忓己" : "涓€?)}`);

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
      <td>${item.premium_cny_per_g != null ? `${formatNumber(item.premium_cny_per_g, 4)} 鍏?鍏媊 : "--"}</td>
      <td>${item.alert_triggered ? "宸茶Е鍙? : item.note || "姝ｅ父"}</td>
    </tr>
  `).join("");
  }
  const alertsBody = document.getElementById("alertsBody");
  if (alertsBody) {
    alertsBody.innerHTML = alertsPage.items.map((item) => `
    <tr>
      <td>${formatTime(item.sent_at)}</td>
      <td>${formatNumber(item.premium_cny_per_g, 4)} 鍏?鍏?/td>
      <td>${formatNumber(item.threshold_cny_per_g, 4)} 鍏?鍏?/td>
      <td>${item.success ? "鎴愬姛" : "澶辫触"}</td>
    </tr>
  `).join("");
  }
  document.getElementById("overviewSgeAlerts").innerHTML = overviewAlertsPage.items.map((item) => `
    <tr>
      <td>${formatTime(item.sent_at)}</td>
      <td>${formatNumber(item.premium_cny_per_g, 4)} 鍏?鍏?/td>
      <td>${item.success ? "鎴愬姛" : "澶辫触"}</td>
    </tr>
  `).join("") || `<tr><td colspan="3" class="muted">鏆傛棤璁板綍</td></tr>`;
  renderPager("samplesPager", "samples", samples.length);
  renderPager("alertsPager", "alerts", alerts.length);
  renderPager("overviewSgeAlertsPager", "overviewSgeAlerts", alerts.length);
}

function renderReversalTables() {
  const reversalStatus = state.reversalStatus;
  const alerts = reversalStatus.recent_alerts || [];
  const history = [...state.reversalHistory].reverse().slice(0, 20);
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
      <td>${item.success ? "鎴愬姛" : "澶辫触"}</td>
    </tr>
  `).join("");
  document.getElementById("overviewReversalAlerts").innerHTML = overviewAlertsPage.items.map((item) => `
    <tr>
      <td>${formatTime(item.sent_at)}</td>
      <td>${formatLevel(item.signal_level)}</td>
      <td>${item.triggered_conditions || "--"}</td>
      <td>${item.success ? "鎴愬姛" : "澶辫触"}</td>
    </tr>
  `).join("") || `<tr><td colspan="4" class="muted">鏆傛棤璁板綍</td></tr>`;
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
    if (level === "楂?) return "high";
    if (level === "涓?) return "mid";
    return "low";
  };
  const buildHtml = (items, withScore = false) => items.length ? items.map((item) => {
    const eventType = item.event_type || "all";
    const keywords = (item.matched_keywords || "").split(",").filter(Boolean);
    return `
      <article class="event-card">
        <div class="event-meta">
          <span class="tag ${eventType}">${eventType === "political" ? "鏀挎不缂撳拰" : "鎴樹簤杩涘害"}</span>
          <span class="tag">${item.source || "鏈煡鏉ユ簮"}</span>
          <span class="tag">${formatTime(item.published_at || item.fetched_at)}</span>
          ${withScore ? `<span class="tag risk-score ${scoreClass(item.impact_level)}">缂撳拰璇勫垎 ${item.impact_score ?? "--"}/10 (${item.impact_level || "浣?})</span>` : ""}
        </div>
        <h4>${item.title || "鏆傛棤鏍囬"}</h4>
        <p>${item.summary || "鏆傛棤鎽樿"}</p>
        <div class="event-meta">
          ${keywords.map((keyword) => `<span class="tag">${keyword}</span>`).join("")}
          ${withScore ? `<span class="tag">${item.impact_note || "鏃犺瘎鍒嗚鏄?}</span>` : ""}
          ${item.link ? `<a href="${item.link}" target="_blank" rel="noreferrer">鏌ョ湅鍘熸枃</a>` : ""}
        </div>
      </article>
    `;
  }).join("") : `<div class="empty-state">鏆傛棤鍛戒腑鍙嶈浆鏉′欢鐨?RSS 浜嬩欢</div>`;
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
        <span>${item.poll_interval_seconds}s / ${item.duration_ms}ms / ${item.success ? "鎴愬姛" : item.error_message || "澶辫触"}</span>
      </li>
    `).join("") : `<li class="muted">\u6682\u65e0\u8bb0\u5f55</li>`;
    renderPager("fetchRunsPager", "fetchRuns", fetchRuns.length);
  } else {
    document.getElementById("fetchRunsList").innerHTML = `<li class="muted">褰撳墠闈?SGE 寮€鐩樻椂娈碉紝鎶撳彇浠诲姟鏆備笉鎵ц銆?/li>`;
    renderPager("fetchRunsPager", "fetchRuns", 0);
  }

  if (marketState.reversal?.active) {
    const reversalRunsPage = getPagedItems(reversalRuns, "reversalRuns");
    document.getElementById("reversalRunsList").innerHTML = reversalRunsPage.items.length ? reversalRunsPage.items.map((item) => `
      <li>
        <span>${formatTime(item.fetched_at)}</span>
        <span>${item.poll_interval_seconds}s / ${item.duration_ms}ms / RSS寮傚父 ${item.rss_error_count}</span>
        <span>${item.success ? "\u6210\u529f" : item.error_message || "\u5931\u8d25"}</span>
      </li>
    `).join("") : `<li class="muted">\u6682\u65e0\u8bb0\u5f55</li>`;
    renderPager("reversalRunsPager", "reversalRuns", reversalRuns.length);
  } else {
    document.getElementById("reversalRunsList").innerHTML = `<li class="muted">褰撳墠鏈弧瓒冲弽杞洃鎺ф椂娈碉紝浠诲姟鏆備笉鎵ц銆?/li>`;
    renderPager("reversalRunsPager", "reversalRuns", 0);
  }

  document.getElementById("rssFetchRunsList").innerHTML = rssRunsPage.items.length ? rssRunsPage.items.map((item) => `
    <li>
      <span>${formatTime(item.fetched_at)}</span>
      <span>${item.duration_ms}ms / 鏉＄洰 ${item.item_count} / 寮傚父 ${item.error_count}</span>
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
      <td>${item.success ? "鎴愬姛" : "澶辫触"}</td>
      <td title="${escapeHtml(item.response_text || item.content || "")}">${escapeHtml(item.content || item.response_text || "--")}</td>
    </tr>
  `).join("") || `<tr><td colspan="5" class="muted">鏆傛棤鎺ㄩ€佽褰?/td></tr>`;
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
        <td>${item.yield_signal ? "瑙﹀彂" : "鏃犱俊鍙?}</td>
        <td>${item.note || "--"}</td>
      </tr>
    `).join("") || `<tr><td colspan="5" class="muted">鏆傛棤璁板綍</td></tr>`;
  }

  const runsList = document.getElementById("us10yRunsList");
  if (runsList) {
    runsList.innerHTML = runsPage.items.map((item) => `
      <li>
        <span>${formatTime(item.fetched_at)}</span>
        <span>${item.duration_ms}ms / ${item.success ? "鎴愬姛" : item.error_message || "澶辫触"}</span>
      </li>
    `).join("") || `<li class="muted">鏆傛棤璁板綍</li>`;
  }

  renderPager("us10ySamplesPager", "us10ySamples", samples.length);
  renderPager("us10yRunsPager", "us10yRuns", runs.length);
}

function renderKeywordBoard() {
  const events = state.reversalStatus.recent_events || [];
  const keywords = [...new Set(events.flatMap((item) => (item.matched_keywords || "").split(",").filter(Boolean)))];
  document.getElementById("eventKeywordList").innerHTML = keywords.length
    ? keywords.map((keyword) => `<span class="tag">${keyword}</span>`).join("")
    : `<div class="empty-state">鏆傛棤鍏抽敭璇?/div>`;
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
  const tenors = settings.us10y_tenors || ["10y"];
  const t5 = document.getElementById("us10yTenor5");
  const t10 = document.getElementById("us10yTenor10");
  const t20 = document.getElementById("us10yTenor20");
  if (t5) t5.checked = tenors.includes("5y");
  if (t10) t10.checked = tenors.includes("10y");
  if (t20) t20.checked = tenors.includes("20y");

  renderFeedRows(settings.rss_feed_urls || []);
  renderTargetRows(settings.notification_targets || []);
}

function isEditingForm() {
  const active = document.activeElement;
  return active instanceof HTMLElement && Boolean(active.closest("form"));
}

function renderFeedRows(items) {
  const container = document.getElementById("feedRows");
  container.innerHTML = "";
  const feeds = items.length ? items : [""];
  feeds.forEach((url) => container.appendChild(createFeedRow(url)));
}

function createFeedRow(url = "") {
  const node = document.getElementById("feedRowTemplate").content.firstElementChild.cloneNode(true);
  node.querySelector(".feed-url-input").value = url;
  node.querySelector(".remove-feed-btn").addEventListener("click", () => {
    if (document.querySelectorAll("#feedRows .editor-row").length > 1) {
      node.remove();
    } else {
      node.querySelector(".feed-url-input").value = "";
    }
  });
  return node;
}

function renderTargetRows(items) {
  const container = document.getElementById("targetRows");
  container.innerHTML = "";
  const targets = items.length ? items : [{ name: "榛樿鎺ㄩ€佺粍", webhook: "", secret: "", enabled: true }];
  targets.forEach((target) => container.appendChild(createTargetRow(target)));
}

function createTargetRow(target = {}) {
  const node = document.getElementById("targetRowTemplate").content.firstElementChild.cloneNode(true);
  node.querySelector(".target-name-input").value = target.name || "榛樿鎺ㄩ€佺粍";
  node.querySelector(".target-webhook-input").value = target.webhook || "";
  node.querySelector(".target-secret-input").value = target.secret || "";
  node.querySelector(".target-enabled-input").checked = target.enabled !== false;
  node.querySelector(".remove-target-btn").addEventListener("click", () => {
    if (document.querySelectorAll("#targetRows .editor-row").length > 1) {
      node.remove();
    } else {
      node.querySelector(".target-name-input").value = "榛樿鎺ㄩ€佺粍";
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
  const times = items.map((item) => item.fetched_at);
  const yMin = state.sgeYAxisRange?.min ?? 800;
  const yMax = state.sgeYAxisRange?.max ?? 1200;
  chart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "axis" },
    legend: { top: 6, textStyle: { color: "#5f6b7c" }, data: ["婧环", "浜烘皯甯侀噾浠?, "鍥介檯閲戞姌绠?] },
    grid: { left: 42, right: 18, top: 52, bottom: 56 },
    xAxis: { type: "time", axisLabel: { color: "#5f6b7c" }, axisLine: { lineStyle: { color: "#b8c1cb" } } },
    yAxis: [
      {
        type: "value",
        min: yMin,
        max: yMax,
        axisLabel: { color: "#5f6b7c" },
        splitLine: { lineStyle: { color: "rgba(18,32,51,0.08)" } },
      },
      {
        type: "value",
        axisLabel: { color: "#5f6b7c" },
        splitLine: { show: false },
      },
    ],
    dataZoom: [{ type: "inside", filterMode: "none", zoomOnMouseWheel: false }],
    series: [
      {
        name: "婧环",
        type: "line",
        yAxisIndex: 1,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 3, color: "#c04f2d" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(192,79,45,0.28)" },
            { offset: 1, color: "rgba(192,79,45,0.02)" },
          ]),
        },
        data: times.map((time, index) => [time, items[index].premium_cny_per_g]),
      },
      {
        name: "浜烘皯甯侀噾浠?,
        type: "line",
        yAxisIndex: 0,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2, color: "#13796b" },
        data: times.map((time, index) => [time, items[index].shfe_price_cny_per_g]),
      },
      {
        name: "鍥介檯閲戞姌绠?,
        type: "line",
        yAxisIndex: 0,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2, color: "#d3a132" },
        data: times.map((time, index) => [time, items[index].london_price_cny_per_g]),
      },
    ],
  });
}

function renderReversalChart(chart) {
  if (!chart) return;
  const items = state.reversalHistory;
  const times = items.map((item) => item.fetched_at);
  const mapSignalToY = (level) => {
    if (level === 1) return 4;
    if (level === 2) return 3;
    if (level === 3) return 2;
    if (level === 4) return 1;
    return 0.2;
  };

  chart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "axis" },
    legend: { top: 6, textStyle: { color: "#5f6b7c" }, data: ["鐜拌揣閲戜环鏍?, "鍙嶈浆淇″彿"] },
    grid: { left: 42, right: 18, top: 52, bottom: 56 },
    xAxis: { type: "time", axisLabel: { color: "#5f6b7c" }, axisLine: { lineStyle: { color: "#b8c1cb" } } },
    yAxis: [
      {
        type: "value",
        name: "缇庡厓/鐩庡徃",
        axisLabel: { color: "#5f6b7c" },
        splitLine: { lineStyle: { color: "rgba(18,32,51,0.08)" } },
      },
      {
        type: "value",
        name: "鍙嶈浆绛夌骇",
        min: 0,
        max: 4.2,
        interval: 1,
        axisLabel: {
          color: "#5f6b7c",
          formatter: (value) => {
            if (value === 4) return "涓€绾?;
            if (value === 3) return "浜岀骇";
            if (value === 2) return "涓夌骇";
            if (value === 1) return "鍥涚骇";
            if (value === 0) return "鏃犱俊鍙?;
            return "";
          },
        },
        splitLine: { show: false },
      },
    ],
    dataZoom: [{ type: "inside", filterMode: "none" }],
    series: [
      {
        name: "鐜拌揣閲?,
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
        name: "鍙嶈浆淇″彿",
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
  chart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "axis" },
    legend: { top: 6, textStyle: { color: "#5f6b7c" }, data: ["鐜拌揣閲?, `缇庡€?{activeTenor.toUpperCase()}`] },
    grid: { left: 42, right: 18, top: 52, bottom: 56 },
    xAxis: { type: "time", axisLabel: { color: "#5f6b7c" }, axisLine: { lineStyle: { color: "#b8c1cb" } } },
    yAxis: [
      {
        type: "value",
        name: "缇庡厓/鐩庡徃",
        axisLabel: { color: "#5f6b7c" },
        splitLine: { lineStyle: { color: "rgba(18,32,51,0.08)" } },
      },
      {
        type: "value",
        name: "%",
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
        name: "鐜拌揣閲?,
        type: "line",
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2.5, color: "#13796b" },
        data: goldItems.map((item) => [item.fetched_at, item.gold_price_usd_per_oz]),
      },
      {
        name: `缇庡€?{activeTenor.toUpperCase()}`,
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
    showToast("淇濆瓨鎴愬姛", `宸叉洿鏂?SGE 璁剧疆锛氶槇鍊?${payload.premium_threshold} 鍏?鍏嬶紝棰戠巼 ${payload.poll_interval_seconds}s銆俙);
  } catch (error) {
    showToast("淇濆瓨澶辫触", `SGE 璁剧疆鏇存柊澶辫触锛?{formatErrorMessage(error)}`, "error");
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
    showToast("淇濆瓨鎴愬姛", "鍙嶈浆鍙傛暟宸叉洿鏂般€?);
  } catch (error) {
    showToast("鎵ц澶辫触", `鎵ц鍙嶈浆鐩戞帶澶辫触锛?{formatErrorMessage(error)}`, "error");
  }
}

async function saveFeedSettings(event) {
  event.preventDefault();
  const rssFeedUrls = [...document.querySelectorAll(".feed-url-input")]
    .map((input) => input.value.trim())
    .filter(Boolean);
  const payload = {
    rss_feed_urls: rssFeedUrls,
    rss_poll_interval_seconds: Number(document.getElementById("rssIntervalInput").value),
  };
  try {
    await fetchJson("/api/reversal/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await refreshAll();
    showToast("淇濆瓨鎴愬姛", `宸蹭繚瀛?${rssFeedUrls.length} 涓?RSS 婧愩€俙);
  } catch (error) {
    showToast("淇濆瓨澶辫触", `RSS 閰嶇疆鏇存柊澶辫触锛?{formatErrorMessage(error)}`, "error");
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
    showToast("淇濆瓨鎴愬姛", `宸蹭繚瀛?${targets.length} 涓帹閫佺粍銆俙);
  } catch (error) {
    showToast("淇濆瓨澶辫触", `鍙傛暟鏇存柊澶辫触锛?{formatErrorMessage(error)}`, "error");
  }
}

async function saveUs10ySettings(event) {
  event.preventDefault();
  const tenors = [];
  if (document.getElementById("us10yTenor5")?.checked) tenors.push("5y");
  0      0   0      0   0      0      0      0                              0
  if (document.getElementById("us10yTenor10")?.checked) tenors.push("10y");
  if (document.getElementById("us10yTenor20")?.checked) tenors.push("20y");
  if (!tenors.length) tenors.push("10y");
  const payload = {
    us10y_poll_interval_seconds: Number(document.getElementById("us10yPollIntervalInput").value),
    us10y_drop_lookback_hours: Number(document.getElementById("us10yDropLookbackHoursInput").value),
    us10y_drop_threshold_bp: Number(document.getElementById("us10yDropThresholdBpInput").value),
    us10y_tenors: tenors,
  };
  try {
    await fetchJson("/api/reversal/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    await refreshAll();
    showToast("淇濆瓨鎴愬姛", `宸蹭繚瀛樼編鍊哄弬鏁帮細${tenors.join(", ").toUpperCase()} / ${payload.us10y_drop_lookback_hours}h / ${payload.us10y_drop_threshold_bp}bp`);
  } catch (error) {
    showToast("淇濆瓨澶辫触", `缇庡€哄弬鏁颁繚瀛樺け璐ワ細${formatErrorMessage(error)}`, "error");
  }
}

async function runUs10yMonitor() {
  try {
    await fetchJson("/api/us10y/run-once", { method: "POST" });
    await refreshAll();
    showToast("鎵ц鎴愬姛", "宸茬珛鍗抽噰鏍峰苟璇勪及缇庡€烘敹鐩婄巼銆?);
  } catch (error) {
    showToast("鎵ц澶辫触", `缇庡€洪噰鏍峰け璐ワ細${formatErrorMessage(error)}`, "error");
  }
}

async function runAllMonitors() {
  try {
    await fetchJson("/api/run-once", { method: "POST" });
    await refreshAll();
    showToast("鎵ц鎴愬姛", "宸茬珛鍗虫墽琛?SGE + 鍙嶈浆 + RSS銆?);
  } catch (error) {
    showToast("鎵ц澶辫触", `鎵ц SGE + 鍙嶈浆 + RSS 澶辫触锛?{formatErrorMessage(error)}`, "error");
  }
}

async function runReversalMonitor() {
  try {
    await fetchJson("/api/reversal/run-once", { method: "POST" });
    await refreshAll();
    showToast("鎵ц鎴愬姛", "宸茬珛鍗虫墽琛屽弽杞洃鎺с€?);
  } catch (error) {
    showToast("鎵ц澶辫触", `鎵ц鍙嶈浆鐩戞帶澶辫触锛?{formatErrorMessage(error)}`, "error");
  }
}

async function runRssMonitor() {
  try {
    await fetchJson("/api/reversal/rss-run-once", { method: "POST" });
    await refreshAll();
    showToast("鎵ц鎴愬姛", "宸茬珛鍗虫墽琛?RSS 鎶撳彇銆?);
  } catch (error) {
    showToast("鎵ц澶辫触", `RSS 鎶撳彇澶辫触锛?{formatErrorMessage(error)}`, "error");
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
      result.success ? "鎺ㄩ€佹垚鍔? : "鎺ㄩ€佸け璐?,
      result.success ? `宸插彂閫?{formatLevel(level)}娴嬭瘯鎺ㄩ€乣 : result.response_text,
      result.success ? "success" : "error",
    );
  } catch (error) {
    showToast("鎺ㄩ€佸け璐?, `娴嬭瘯鎺ㄩ€佸け璐ワ細${formatErrorMessage(error)}`, "error");
  }
}

100  52873 100  52873   0      0 179.9k      0                              0
100  52873 100  52873   0      0 179.9k      0                              0
100  52873 100  52873   0      0 179.8k      0                              0
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

  document.querySelectorAll(".range-btn").forEach((button) => {
    button.addEventListener("click", async () => {
      if (button.dataset.chart === "reversal") {
        state.reversalRange = button.dataset.range;
      } else if (button.dataset.chart === "us10y") {
        state.us10yRange = button.dataset.range;
      } else {
        state.sgeRange = button.dataset.range;
      }
      syncRangeButtons();
      await refreshAll();
    });
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
    const text = window.prompt("璇疯緭鍏ユ洿鏂拌褰曞唴瀹?);
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
    document.getElementById("feedRows").appendChild(createFeedRow(""));
  });
  bindClick("addTargetBtn", () => {
    document.getElementById("targetRows").appendChild(createTargetRow({ name: "榛樿鎺ㄩ€佺粍", enabled: true }));
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
});

setInterval(() => {
  refreshAll().catch(() => {});
}, 15000);
