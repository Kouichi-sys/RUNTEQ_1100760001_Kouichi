// ライブ映像の自動更新。
// 動画ストリームではなく静止画を一定間隔で取り直すことで、通信量を抑える。
(function () {
  const image = document.getElementById("live");
  const status = document.getElementById("status");
  const toggle = document.getElementById("toggle");
  if (!image || !toggle) {
    return;
  }

  const seconds = JSON.parse(document.getElementById("refresh-seconds").textContent);
  const baseUrl = image.getAttribute("src");
  let timer = null;

  function refresh() {
    // 同じURLだとブラウザのキャッシュが使われることがあるため、時刻を付ける
    image.src = baseUrl + "?t=" + Date.now();
  }

  function start() {
    timer = setInterval(refresh, seconds * 1000);
    status.textContent = "更新中";
    toggle.textContent = "一時停止";
  }

  function stop() {
    clearInterval(timer);
    timer = null;
    status.textContent = "停止中";
    toggle.textContent = "再開";
  }

  toggle.addEventListener("click", function () {
    if (timer) {
      stop();
    } else {
      refresh();
      start();
    }
  });

  // 別のタブを見ている間は取得を止め、無駄な通信をしない
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
      if (timer) stop();
    } else if (!timer) {
      refresh();
      start();
    }
  });

  start();
})();
