// 映像の再生制御。ライブ画面と過去映像画面の両方で使う。
//
// 映像はCSSアニメーションで動き続けるため、再生・一時停止・速度変更では
// 通信が発生しない。再生位置を飛ばしたときだけ、その時刻から始まる映像を
// サーバーから取り直す。
(function () {
  const stage = document.getElementById("stage");
  const toggle = document.getElementById("toggle");
  const clock = document.getElementById("clock");
  const badge = document.getElementById("badge");
  const shot = document.getElementById("screenshot");
  if (!stage || !toggle) {
    return;
  }

  // 再生中の表示はライブと過去映像で異なるため、最初の文言をそのまま使う
  const playingLabel = badge.textContent.trim();
  const shotBaseUrl = shot.getAttribute("href");
  // 再生位置を飛ばせる画面(過去映像)だけ、取得先が渡される
  const streamUrl = stage.dataset.streamUrl || null;
  const baseDuration = flowDuration();

  let position = new Date(stage.dataset.startedAt);
  let tickedAt = performance.now();
  let rate = 1;
  let paused = false;

  function flow() {
    return stage.querySelector(".nxv-flow");
  }

  function flowDuration() {
    const element = stage.querySelector(".nxv-flow");
    if (!element) {
      return 0;
    }
    return parseFloat(getComputedStyle(element).animationDuration) || 0;
  }

  function currentTime() {
    if (paused) {
      return position;
    }
    const advanced = (performance.now() - tickedAt) * rate;
    return new Date(position.getTime() + advanced);
  }

  function format(date) {
    const p = (n) => String(n).padStart(2, "0");
    return (
      date.getFullYear() + "-" + p(date.getMonth() + 1) + "-" + p(date.getDate()) +
      " " + p(date.getHours()) + ":" + p(date.getMinutes()) + ":" + p(date.getSeconds())
    );
  }

  function updateShotLink(date) {
    // 見ている場面をそのまま保存できるよう、再生位置を渡す
    shot.setAttribute("href", shotBaseUrl + "?at=" + encodeURIComponent(date.toISOString()));
  }

  function tick() {
    const now = currentTime();
    clock.textContent = format(now);
    if (!paused) {
      requestAnimationFrame(tick);
    }
  }

  function applyRate() {
    const element = flow();
    if (element && baseDuration) {
      element.style.animationDuration = (baseDuration / rate).toFixed(4) + "s";
    }
    document.querySelectorAll("[data-rate]").forEach(function (button) {
      button.classList.toggle("btn--active", Number(button.dataset.rate) === rate);
    });
  }

  function pause() {
    position = currentTime();
    paused = true;
    stage.classList.add("nxv-paused");
    toggle.textContent = "再生";
    badge.textContent = "■ 一時停止";
    badge.classList.add("viewer__badge--paused");
    clock.textContent = format(position);
    updateShotLink(position);
  }

  function play() {
    tickedAt = performance.now();
    paused = false;
    stage.classList.remove("nxv-paused");
    toggle.textContent = "一時停止";
    badge.textContent = playingLabel;
    badge.classList.remove("viewer__badge--paused");
    shot.setAttribute("href", shotBaseUrl);
    requestAnimationFrame(tick);
  }

  // 指定した時刻の映像に差し替える。位置を飛ばしたときだけ通信する
  function seek(date) {
    const now = new Date();
    if (date > now) {
      date = now;
    }
    position = date;
    tickedAt = performance.now();
    clock.textContent = format(date);

    if (!streamUrl) {
      return;
    }
    fetch(streamUrl + "?at=" + encodeURIComponent(date.toISOString()))
      .then(function (response) { return response.text(); })
      .then(function (markup) {
        const hud = stage.querySelector(".viewer__hud");
        stage.innerHTML = markup;
        stage.appendChild(hud);
        applyRate();
        if (paused) {
          stage.classList.add("nxv-paused");
          updateShotLink(date);
        }
      });
  }

  toggle.addEventListener("click", function () {
    if (paused) {
      play();
    } else {
      pause();
    }
  });

  document.querySelectorAll("[data-jump]").forEach(function (button) {
    button.addEventListener("click", function () {
      seek(new Date(currentTime().getTime() + Number(button.dataset.jump) * 1000));
    });
  });

  document.querySelectorAll("[data-rate]").forEach(function (button) {
    button.addEventListener("click", function () {
      // 速度を変えても見ている位置は動かさない
      position = currentTime();
      tickedAt = performance.now();
      rate = Number(button.dataset.rate);
      applyRate();
    });
  });

  applyRate();
  tick();
})();
