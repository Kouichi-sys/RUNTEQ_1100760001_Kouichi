// ライブ映像の再生制御。
// 映像はCSSアニメーションで動き続けるため、再生・一時停止は
// 親要素のクラスを切り替えるだけでよく、通信は発生しない。
(function () {
  const stage = document.getElementById("stage");
  const toggle = document.getElementById("toggle");
  const clock = document.getElementById("clock");
  const badge = document.getElementById("badge");
  const shot = document.getElementById("screenshot");
  if (!stage || !toggle) {
    return;
  }

  const startedAt = new Date(stage.dataset.startedAt);
  const startedTick = performance.now();
  const shotBaseUrl = shot.getAttribute("href");
  let paused = false;
  // 一時停止した時刻。再生中はnull
  let pausedAt = null;

  function currentTime() {
    if (pausedAt) {
      return pausedAt;
    }
    return new Date(startedAt.getTime() + (performance.now() - startedTick));
  }

  function format(date) {
    const p = (n) => String(n).padStart(2, "0");
    return (
      date.getFullYear() + "-" + p(date.getMonth() + 1) + "-" + p(date.getDate()) +
      " " + p(date.getHours()) + ":" + p(date.getMinutes()) + ":" + p(date.getSeconds())
    );
  }

  function tick() {
    clock.textContent = format(currentTime());
    if (!paused) {
      requestAnimationFrame(tick);
    }
  }

  function pause() {
    paused = true;
    pausedAt = currentTime();
    stage.classList.add("nxv-paused");
    toggle.textContent = "再生";
    badge.textContent = "■ 一時停止";
    badge.classList.add("viewer__badge--paused");
    clock.textContent = format(pausedAt);
    // 止めた瞬間をそのまま保存できるように、時刻を渡す
    shot.setAttribute("href", shotBaseUrl + "?at=" + encodeURIComponent(pausedAt.toISOString()));
  }

  function play() {
    paused = false;
    pausedAt = null;
    stage.classList.remove("nxv-paused");
    toggle.textContent = "一時停止";
    badge.textContent = "● LIVE";
    badge.classList.remove("viewer__badge--paused");
    shot.setAttribute("href", shotBaseUrl);
    requestAnimationFrame(tick);
  }

  toggle.addEventListener("click", function () {
    if (paused) {
      play();
    } else {
      pause();
    }
  });

  tick();
})();
