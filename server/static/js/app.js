const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const levelLabels = {
  normal: "正常",
  mild: "轻度",
  moderate: "中度",
  severe: "重度",
};
const sourceLabels = { image: "图片", video: "视频", camera: "摄像头" };
const eventLabels = { eye_closed: "闭眼", yawn: "哈欠", head_down: "低头" };

function escapeHtml(value) {
  return String(value ?? "").replace(
    /[&<>'"]/g,
    (character) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[
        character
      ],
  );
}

function toast(message) {
  const node = $("#toast");
  if (!node) return;
  node.textContent = message;
  node.classList.add("show");
  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => node.classList.remove("show"), 2800);
}

async function jsonRequest(url, options) {
  const response = await fetch(url, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || "请求失败");
  return body;
}

function formatDate(value) {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function levelBadge(level) {
  return `<span class="level ${escapeHtml(level)}"><i class="level-dot"></i>${levelLabels[level] || escapeHtml(level)}</span>`;
}

function renderRiskBars(distribution) {
  const total = Object.values(distribution).reduce(
    (sum, value) => sum + value,
    0,
  );
  return Object.entries(levelLabels)
    .map(([key, label]) => {
      const count = distribution[key] || 0;
      const percentage = total ? (count / total) * 100 : 0;
      return `<div class="risk-row"><div><span><i class="risk-key ${key}"></i>${label}</span><strong>${count}</strong></div><div class="risk-track"><i class="${key}" style="width:${percentage}%"></i></div></div>`;
    })
    .join("");
}

async function loadOverview() {
  if (!$("#overview-total")) return;
  try {
    const data = await jsonRequest("/api/analytics/summary");
    $("#overview-total").textContent = data.totals.total_tasks;
    $("#overview-fatigue-rate").textContent = `${data.totals.fatigue_rate}%`;
    $("#overview-fps").textContent = data.totals.average_fps
      ? `${data.totals.average_fps} FPS`
      : "--";
    $("#overview-latency").textContent = data.totals.average_latency_ms
      ? `${data.totals.average_latency_ms} ms`
      : "--";
    $("#overview-risk-bars").innerHTML = renderRiskBars(data.risk_distribution);
    const body = $("#overview-high-risk");
    body.innerHTML = data.high_risk.length
      ? data.high_risk
          .map(
            (record) =>
              `<tr><td>${formatDate(record.created_at)}</td><td>${sourceLabels[record.source_type] || record.source_type}</td><td class="filename">${escapeHtml(record.source_name)}</td><td>${levelBadge(record.level)}</td><td><strong>${record.score}</strong></td></tr>`,
          )
          .join("")
      : '<tr class="empty-row"><td colspan="5">暂无中度或重度记录</td></tr>';
  } catch (error) {
    toast(error.message);
  }
}

let historyRecords = [];
function renderHistory() {
  const body = $("#history-body");
  if (!body) return;
  const filter = $("#history-filter")?.value || "all";
  const records =
    filter === "all"
      ? historyRecords
      : historyRecords.filter((record) => record.level === filter);
  body.innerHTML = records.length
    ? records
        .map(
          (record) =>
            `<tr><td>${formatDate(record.created_at)}</td><td><span class="source-tag"><i data-lucide="${record.source_type === "video" ? "video" : "image"}"></i>${sourceLabels[record.source_type] || record.source_type}</span></td><td class="filename">${escapeHtml(record.source_name)}</td><td>${levelBadge(record.level)}</td><td><strong>${record.score}</strong></td><td>${record.source_type === "video" ? `<a class="text-link" href="/analytics#video-${record.id}">查看分析</a>` : '<span class="muted">--</span>'}</td></tr>`,
        )
        .join("")
    : '<tr class="empty-row"><td colspan="6">当前筛选下暂无检测记录</td></tr>';
  window.lucide?.createIcons();
}

async function loadHistory() {
  if (!$("#history-body")) return;
  try {
    historyRecords = (await jsonRequest("/api/records")).records;
    renderHistory();
  } catch (error) {
    toast(error.message);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });
  $("#history-filter")?.addEventListener("change", renderHistory);
  $("#history-refresh")?.addEventListener("click", loadHistory);
  loadOverview();
  loadHistory();
});
