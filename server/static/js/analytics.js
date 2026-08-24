document.addEventListener("DOMContentLoaded", async () => {
  if (!$("#risk-chart")) return;
  Chart.defaults.font.family = '"Segoe UI", "Microsoft YaHei", sans-serif';
  Chart.defaults.color = "#667085";
  Chart.defaults.borderColor = "#eaecf0";
  const charts = new Map();
  const palette = {
    normal: "#16a36a",
    mild: "#d99a19",
    moderate: "#ea6a20",
    severe: "#dc3c4d",
    blue: "#2563eb",
    violet: "#7c5ce7",
  };
  try {
    const data = await jsonRequest("/api/analytics/summary");
    $("#analytics-total").textContent = data.totals.total_tasks;
    $("#analytics-rate").textContent = `${data.totals.fatigue_rate}%`;
    $("#analytics-fps").textContent = data.totals.average_fps
      ? `${data.totals.average_fps} FPS`
      : "--";
    $("#analytics-latency").textContent = data.totals.average_latency_ms
      ? `${data.totals.average_latency_ms} ms`
      : "--";
    charts.set(
      "risk-chart",
      doughnut(
        "risk-chart",
        ["正常", "轻度", "中度", "重度"],
        ChartData.orderedValues(data.risk_distribution, [
          "normal",
          "mild",
          "moderate",
          "severe",
        ]),
        [palette.normal, palette.mild, palette.moderate, palette.severe],
      ),
    );
    charts.set(
      "event-chart",
      bar(
        "event-chart",
        ["闭眼", "哈欠", "低头"],
        ChartData.orderedValues(data.event_distribution, [
          "eye_closed",
          "yawn",
          "head_down",
        ]),
        [palette.blue, palette.mild, palette.violet],
      ),
    );
    charts.set(
      "source-chart",
      doughnut(
        "source-chart",
        ["图片", "视频", "摄像头"],
        ChartData.orderedValues(data.source_distribution, [
          "image",
          "video",
          "camera",
        ]),
        ["#2563eb", "#7c5ce7", "#16a36a"],
      ),
    );
    charts.set(
      "trend-chart",
      line(
        "trend-chart",
        data.daily_trend.map((item) => item.date),
        [
          {
            label: "全部任务",
            data: data.daily_trend.map((item) => item.tasks),
            borderColor: palette.blue,
          },
          {
            label: "疲劳任务",
            data: data.daily_trend.map((item) => item.fatigue),
            borderColor: palette.severe,
          },
        ],
      ),
    );
    charts.set(
      "metric-chart",
      line(
        "metric-chart",
        data.metric_trend.map((item) => item.date),
        [
          {
            label: "EAR",
            data: data.metric_trend.map((item) => item.ear),
            borderColor: palette.blue,
          },
          {
            label: "MAR",
            data: data.metric_trend.map((item) => item.mar),
            borderColor: palette.mild,
          },
          {
            label: "俯仰角",
            data: data.metric_trend.map((item) => item.pitch),
            borderColor: palette.violet,
            yAxisID: "y1",
          },
        ],
        true,
      ),
    );
    renderExperiments(data.video_experiments);
    const target = location.hash.match(/^#video-(\d+)$/)?.[1];
    if (target) openVideoDetail(target);
  } catch (error) {
    toast(error.message);
  }

  function commonOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: matchMedia("(prefers-reduced-motion: reduce)").matches
          ? 0
          : 300,
      },
      plugins: {
        legend: {
          position: "bottom",
          labels: { usePointStyle: true, padding: 18 },
        },
        tooltip: { displayColors: true },
      },
    };
  }
  function doughnut(id, labels, data, colors) {
    return new Chart($(`#${id}`), {
      type: "doughnut",
      data: {
        labels,
        datasets: [
          { data, backgroundColor: colors, borderWidth: 0, spacing: 2 },
        ],
      },
      options: { ...commonOptions(), cutout: "65%" },
    });
  }
  function bar(id, labels, data, colors) {
    return new Chart($(`#${id}`), {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "出现次数",
            data,
            backgroundColor: colors,
            borderRadius: 3,
            maxBarThickness: 42,
          },
        ],
      },
      options: {
        ...commonOptions(),
        scales: {
          y: { beginAtZero: true, ticks: { precision: 0 } },
          x: { grid: { display: false } },
        },
      },
    });
  }
  function line(id, labels, datasets, secondAxis = false) {
    datasets.forEach((dataset) =>
      Object.assign(dataset, {
        tension: 0.28,
        pointRadius: 3,
        pointHoverRadius: 5,
        borderWidth: 2,
        backgroundColor: dataset.borderColor,
      }),
    );
    const scales = {
      x: { grid: { display: false } },
      y: { beginAtZero: true },
    };
    if (secondAxis)
      scales.y1 = { position: "right", grid: { drawOnChartArea: false } };
    return new Chart($(`#${id}`), {
      type: "line",
      data: { labels, datasets },
      options: {
        ...commonOptions(),
        interaction: { mode: "index", intersect: false },
        scales,
      },
    });
  }
  function renderExperiments(items) {
    $("#experiment-body").innerHTML = items.length
      ? items
          .map(
            (item) =>
              `<tr id="video-${item.id}"><td class="filename">${escapeHtml(item.source_name)}</td><td>${item.processed_frames} / ${item.total_frames}</td><td>${item.average_fps.toFixed(2)} FPS</td><td>${item.average_latency_ms.toFixed(1)} ms</td><td>${item.event_counts.eye_closed || 0} / ${item.event_counts.yawn || 0} / ${item.event_counts.head_down || 0}</td><td><strong>${item.warning_count}</strong></td><td><button class="text-button video-detail" data-id="${item.id}">查看详情</button></td></tr>`,
          )
          .join("")
      : '<tr class="empty-row"><td colspan="7">暂无已完成的视频分析记录</td></tr>';
    $$(".video-detail").forEach((button) =>
      button.addEventListener("click", () =>
        openVideoDetail(button.dataset.id),
      ),
    );
  }
  async function openVideoDetail(id) {
    try {
      const { video } = await jsonRequest(`/api/analytics/videos/${id}`);
      $("#detail-title").textContent = video.source_name;
      $("#detail-subtitle").textContent =
        `${formatDate(video.created_at)} · ${levelLabels[video.level]}`;
      charts.get("video-detail-chart")?.destroy();
      const timeline = video.details.timeline || [];
      charts.set(
        "video-detail-chart",
        line(
          "video-detail-chart",
          timeline.map((point) => `${point.media_time}s`),
          [
            {
              label: "EAR",
              data: timeline.map((point) => point.ear),
              borderColor: palette.blue,
            },
            {
              label: "MAR",
              data: timeline.map((point) => point.mar),
              borderColor: palette.mild,
            },
            {
              label: "俯仰角",
              data: timeline.map((point) => point.pitch),
              borderColor: palette.violet,
              yAxisID: "y1",
            },
          ],
          true,
        ),
      );
      const details = video.details;
      $("#detail-summary").innerHTML =
        `<span><small>处理帧数</small><strong>${details.processed_frames}</strong></span><span><small>平均帧率</small><strong>${details.average_fps} FPS</strong></span><span><small>单帧延迟</small><strong>${details.average_latency_ms} ms</strong></span><span><small>重度预警</small><strong>${details.warning_count}</strong></span>`;
      $("#video-detail-dialog").showModal();
    } catch (error) {
      toast(error.message);
    }
  }
  function downloadChart(id) {
    const canvas = $(`#${id}`);
    const link = document.createElement("a");
    link.download = `${id}-${new Date().toISOString().slice(0, 10)}.png`;
    link.href = canvas.toDataURL("image/png", 1);
    link.click();
  }
  $$(".chart-download").forEach((button) =>
    button.addEventListener("click", () => downloadChart(button.dataset.chart)),
  );
  $("#export-charts").addEventListener("click", () => {
    [
      "risk-chart",
      "event-chart",
      "source-chart",
      "trend-chart",
      "metric-chart",
    ].forEach((id, index) => setTimeout(() => downloadChart(id), index * 180));
  });
  $("#print-report").addEventListener("click", () => window.print());
  $("#detail-close").addEventListener("click", () =>
    $("#video-detail-dialog").close(),
  );
});
