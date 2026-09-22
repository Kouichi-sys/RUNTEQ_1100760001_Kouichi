// 保存した映像をPNGとしてダウンロードする。
//
// 保存形式はSVGのため、そのまま配ると受け取った人が開きにくい。
// メールに添付して共有できるよう、画面側で画像に変換してから渡す。
// 変換はブラウザ内で行うため、サーバーには負荷がかからない。
(function () {
  const button = document.getElementById("download-png");
  if (!button) {
    return;
  }

  const sourceUrl = button.dataset.source;
  const fileName = button.dataset.filename;
  // 変換中に文言を差し替えるため、元の表記を覚えておく
  const label = button.textContent;
  // 変換後の大きさ。映像と同じ16:9
  const WIDTH = 1280;
  const HEIGHT = 720;

  function fail(message) {
    button.disabled = false;
    button.textContent = label;
    window.alert(message);
  }

  button.addEventListener("click", function () {
    button.disabled = true;
    button.textContent = "準備中…";

    fetch(sourceUrl)
      .then(function (response) {
        if (!response.ok) {
          throw new Error("映像を取得できませんでした。");
        }
        return response.text();
      })
      .then(function (svg) {
        // 大きさの指定が無いと画像として読み込めないブラウザがあるため補う
        const sized = svg.replace("<svg ", '<svg width="' + WIDTH + '" height="' + HEIGHT + '" ');
        const blob = new Blob([sized], { type: "image/svg+xml;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const image = new Image();

        image.onload = function () {
          const canvas = document.createElement("canvas");
          canvas.width = WIDTH;
          canvas.height = HEIGHT;
          const context = canvas.getContext("2d");
          context.drawImage(image, 0, 0, WIDTH, HEIGHT);
          URL.revokeObjectURL(url);

          canvas.toBlob(function (png) {
            if (!png) {
              fail("画像に変換できませんでした。");
              return;
            }
            const link = document.createElement("a");
            link.href = URL.createObjectURL(png);
            link.download = fileName;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(link.href);

            button.disabled = false;
            button.textContent = label;
          }, "image/png");
        };

        image.onerror = function () {
          URL.revokeObjectURL(url);
          fail("画像に変換できませんでした。");
        };

        image.src = url;
      })
      .catch(function (error) {
        fail(error.message);
      });
  });
})();
