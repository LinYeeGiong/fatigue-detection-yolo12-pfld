document.addEventListener("DOMContentLoaded", () => {
  const severeNotifier = createSevereNotifier({
    element: $("#severe-alert"),
  });
  $("#alert-close")?.addEventListener("click", severeNotifier.dismiss);
  let showPose = false;
  const poseToggle = $("#pose-overlay-toggle");
  poseToggle?.addEventListener("click", () => {
    showPose = !showPose;
    poseToggle.setAttribute("aria-pressed", String(showPose));
    poseToggle.classList.toggle("active", showPose);
    $("#pose-overlay-toggle span").textContent = showPose
      ? "隐藏位姿"
      : "显示位姿";
  });

  $$(".segmented button").forEach((button) =>
    button.addEventListener("click", () => {
      $$(".segmented button").forEach((item) => {
        item.classList.remove("active");
        item.setAttribute("aria-selected", "false");
      });
      $$(".detect-panel").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      button.setAttribute("aria-selected", "true");
      $(`#${button.dataset.panel}`).classList.add("active");
      history.replaceState(null, "", `#${button.dataset.panel}`);
    }),
  );
  const initialTab = location.hash.slice(1);
  $(`[data-panel="${initialTab}"]`)?.click();

  const images = $("#image-files");
  images?.addEventListener("change", () => {
    $('label[for="image-files"] span').textContent = images.files.length
      ? `已选择 ${images.files.length} 张图片`
      : "支持多选，单次总大小不超过 100 MB";
  });
  $("#image-submit")?.addEventListener("click", async () => {
    if (!images.files.length) return toast("请先选择图片");
    severeNotifier.reset("images");
    const button = $("#image-submit");
    button.disabled = true;
    button.innerHTML = '<span class="spinner"></span>正在检测';
    const data = new FormData();
    [...images.files].forEach((file) => data.append("files", file));
    data.append("show_pose", String(showPose));
    try {
      const body = await jsonRequest("/api/detect/images", {
        method: "POST",
        body: data,
      });
      $("#image-empty").hidden = true;
      $("#image-results").innerHTML = body.results
        .map(
          (item, index) =>
            `<article class="result-card"><img src="${item.processed_image || URL.createObjectURL(images.files[index])}" alt="${escapeHtml(item.filename)} 检测结果"><div><div class="result-card-head">${levelBadge(item.level)}<strong>${item.score} 分</strong></div><h3>${escapeHtml(item.filename)}</h3><dl><div><dt>EAR</dt><dd>${item.metrics.ear.toFixed(3)}</dd></div><div><dt>MAR</dt><dd>${item.metrics.mar.toFixed(3)}</dd></div><div><dt>Pitch</dt><dd>${(item.metrics.pitch ?? 0).toFixed(1)}°</dd></div><div><dt>Roll</dt><dd>${(item.metrics.roll ?? 0).toFixed(1)}°</dd></div><div><dt>Yaw</dt><dd>${(item.metrics.yaw ?? 0).toFixed(1)}°</dd></div></dl></div></article>`,
        )
        .join("");
      severeNotifier.update("images", body.alert ? "severe" : "normal");
    } catch (error) {
      toast(error.message);
    } finally {
      button.disabled = false;
      button.innerHTML = '<i data-lucide="scan-line"></i>开始检测';
      window.lucide?.createIcons();
    }
  });

  const videoFile = $("#video-file");
  let videoJob = null;
  let videoEvents = null;
  videoFile?.addEventListener("change", () => {
    $("#video-name").textContent = videoFile.files[0]?.name || "尚未选择文件";
  });
  $("#video-submit")?.addEventListener("click", async () => {
    if (!videoFile.files.length) return toast("请先选择视频");
    severeNotifier.reset("video");
    resetVideoView();
    const data = new FormData();
    data.append("file", videoFile.files[0]);
    data.append("show_pose", String(showPose));
    setVideoBusy(true, "正在上传");
    try {
      videoJob = await jsonRequest("/api/detect/video", {
        method: "POST",
        body: data,
      });
      $("#video-frame-count").textContent =
        `0 / ${videoJob.total_frames || "?"} 帧`;
      $("#video-phase").textContent = "逐帧分析中";
      $("#video-cancel").disabled = false;
      videoEvents = new EventSource(videoJob.stream_url);
      videoEvents.addEventListener("frame", (event) =>
        updateVideoFrame(JSON.parse(event.data)),
      );
      videoEvents.addEventListener("complete", (event) =>
        finishVideo(JSON.parse(event.data)),
      );
      videoEvents.addEventListener("cancelled", () => finishVideoCancelled());
      videoEvents.addEventListener("error", (event) => {
        if (event.data) failVideo(JSON.parse(event.data).message);
        else if (videoEvents?.readyState === EventSource.CLOSED)
          failVideo("视频连接已中断");
      });
    } catch (error) {
      failVideo(error.message);
    }
  });
  $("#video-cancel")?.addEventListener("click", async () => {
    if (!videoJob) return;
    try {
      await jsonRequest(`/api/detect/video/${videoJob.job_id}`, {
        method: "DELETE",
      });
    } catch (error) {
      toast(error.message);
    }
    finishVideoCancelled();
  });

  function updateVideoFrame(frame) {
    const image = $("#video-processed");
    image.src = frame.processed_image;
    image.hidden = false;
    $("#video-empty").hidden = true;
    const progress = frame.progress ?? 0;
    $("#video-progress").value = progress;
    $("#video-progress-text").textContent = `${progress.toFixed(1)}%`;
    $("#video-frame-count").textContent =
      `${frame.frame_index} / ${frame.total_frames || "?"} 帧`;
    const values = $$("#video-metrics strong");
    [
      frame.metrics.ear.toFixed(3),
      frame.metrics.mar.toFixed(3),
      `${frame.metrics.pitch.toFixed(1)}°`,
      `${(frame.metrics.roll ?? 0).toFixed(1)}°`,
      `${(frame.metrics.yaw ?? 0).toFixed(1)}°`,
      `${frame.processing_fps.toFixed(1)} FPS`,
      `${frame.latency_ms.toFixed(0)} ms`,
      `${frame.media_time.toFixed(1)} s`,
    ].forEach((value, index) => (values[index].textContent = value));
    updateLevel($("#video-level"), frame.level);
    $("#video-status strong").textContent = frame.events.length
      ? `检测到：${frame.events.map((name) => eventLabels[name]).join("、")}`
      : "当前画面状态正常";
    $("#video-status small").textContent = `正在处理第 ${frame.frame_index} 帧`;
    severeNotifier.update("video", frame.level);
  }

  function finishVideo(data) {
    videoEvents?.close();
    videoEvents = null;
    videoJob = null;
    setVideoBusy(false, "分析完成");
    $("#video-progress").value = 100;
    $("#video-progress-text").textContent = "100%";
    $("#video-phase").textContent = "分析完成";
    $("#video-status").innerHTML =
      `<span>${levelBadge(data.level)}<strong>已完成 ${data.processed_frames} 帧</strong></span><small>平均 ${data.average_fps} FPS · ${data.average_latency_ms} ms/帧 · 记录 #${data.record.id}</small>`;
  }

  function finishVideoCancelled() {
    videoEvents?.close();
    videoEvents = null;
    videoJob = null;
    setVideoBusy(false, "任务已停止");
    $("#video-phase").textContent = "任务已停止";
    $("#video-status strong").textContent = "视频分析已停止";
    $("#video-status small").textContent = "已完成的临时数据不会写入历史记录";
  }

  function failVideo(message) {
    videoEvents?.close();
    videoEvents = null;
    videoJob = null;
    setVideoBusy(false, "处理失败");
    $("#video-phase").textContent = "处理失败";
    toast(message || "视频处理失败");
  }

  function setVideoBusy(busy, label) {
    $("#video-submit").disabled = busy;
    $("#video-file").disabled = busy;
    $("#video-cancel").disabled = !busy;
    $("#video-submit").innerHTML = busy
      ? '<span class="spinner"></span>处理中'
      : '<i data-lucide="play"></i>重新分析';
    $("#video-status strong").textContent = label;
    window.lucide?.createIcons();
  }

  function resetVideoView() {
    $("#video-progress").value = 0;
    $("#video-progress-text").textContent = "0%";
    $("#video-level").hidden = true;
  }

  let cameraStream = null;
  let cameraTimer = null;
  let cameraSession = null;
  let cameraBusy = false;
  $("#camera-start")?.addEventListener("click", async () => {
    try {
      severeNotifier.reset("camera");
      cameraSession = crypto.randomUUID();
      cameraStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      $("#camera-preview").srcObject = cameraStream;
      $("#camera-preview").classList.add("active");
      $("#camera-start").disabled = true;
      $("#camera-stop").disabled = false;
      cameraTimer = setInterval(processCameraFrame, 160);
      processCameraFrame();
    } catch (error) {
      toast("无法打开摄像头，请检查系统权限");
    }
  });
  $("#camera-stop")?.addEventListener("click", stopCamera);

  async function processCameraFrame() {
    if (cameraBusy || !cameraStream) return;
    const preview = $("#camera-preview");
    if (!preview.videoWidth) return;
    cameraBusy = true;
    const canvas = $("#camera-canvas");
    canvas.width = preview.videoWidth;
    canvas.height = preview.videoHeight;
    canvas.getContext("2d").drawImage(preview, 0, 0);
    try {
      const body = await jsonRequest("/api/detect/frame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          frame: canvas.toDataURL("image/jpeg", 0.82),
          session_id: cameraSession,
          show_pose: showPose,
        }),
      });
      const result = body.result;
      const image = $("#camera-processed");
      image.src =
        result.processed_image || canvas.toDataURL("image/jpeg", 0.82);
      image.hidden = false;
      $("#camera-empty").hidden = true;
      const values = $$("#camera-metrics strong");
      [
        result.metrics.ear.toFixed(3),
        result.metrics.mar.toFixed(3),
        `${result.metrics.pitch.toFixed(1)}°`,
        `${(result.metrics.roll ?? 0).toFixed(1)}°`,
        `${(result.metrics.yaw ?? 0).toFixed(1)}°`,
      ].forEach((value, index) => (values[index].textContent = value));
      updateLevel($("#camera-level"), result.level);
      severeNotifier.update("camera", result.level);
    } catch (error) {
      toast(error.message);
    } finally {
      cameraBusy = false;
    }
  }

  function stopCamera() {
    clearInterval(cameraTimer);
    cameraTimer = null;
    cameraStream?.getTracks().forEach((track) => track.stop());
    cameraStream = null;
    cameraSession = null;
    severeNotifier.reset("camera");
    $("#camera-preview")?.classList.remove("active");
    if ($("#camera-start")) $("#camera-start").disabled = false;
    if ($("#camera-stop")) $("#camera-stop").disabled = true;
  }

  function updateLevel(node, level) {
    node.hidden = false;
    node.className = `level ${level}`;
    node.innerHTML = `<i class="level-dot"></i>${levelLabels[level]}`;
  }
  window.addEventListener("beforeunload", () => {
    if (videoJob)
      fetch(`/api/detect/video/${videoJob.job_id}`, {
        method: "DELETE",
        keepalive: true,
      });
    stopCamera();
  });
});
