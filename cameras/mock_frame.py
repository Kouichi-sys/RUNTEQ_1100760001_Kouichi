"""疑似ライブ映像(SVG)の生成。

実カメラが無い環境でライブ映像の画面を確認できるようにするためのもの。
SVGは数KBしかないため、静止画を定期取得する方式でも帯域をほとんど使わない。
"""

from django.utils.html import escape

WIDTH = 640
HEIGHT = 360
BELT_TOP = 232
# 製品が流れる間隔(px)と速さ(px/秒)
PRODUCT_GAP = 96
PRODUCT_SPEED = 42


def _can(x, y, hue):
    return (
        f'<g transform="translate({x:.1f},{y})">'
        f'<rect x="-15" y="-46" width="30" height="46" rx="4" fill="hsl({hue},45%,62%)"/>'
        f'<rect x="-15" y="-40" width="30" height="7" fill="hsl({hue},55%,45%)"/>'
        f'<rect x="-15" y="-20" width="30" height="5" fill="hsl({hue},55%,45%)"/>'
        f'<ellipse cx="0" cy="-46" rx="15" ry="4.5" fill="hsl({hue},25%,78%)"/>'
        "</g>"
    )


def _bottle(x, y, hue):
    return (
        f'<g transform="translate({x:.1f},{y})">'
        f'<path d="M-12,0 L-12,-34 Q-12,-44 -5,-50 L-5,-62 L5,-62 L5,-50 '
        f'Q12,-44 12,-34 L12,0 Z" fill="hsl({hue},50%,40%)"/>'
        f'<rect x="-12" y="-28" width="24" height="12" fill="hsl({hue},20%,86%)"/>'
        f'<rect x="-5" y="-66" width="10" height="5" rx="1" fill="hsl({hue},40%,58%)"/>'
        "</g>"
    )


def _keg(x, y, hue):
    return (
        f'<g transform="translate({x:.1f},{y})">'
        f'<path d="M-22,0 Q-27,-26 -22,-52 L22,-52 Q27,-26 22,0 Z" fill="hsl({hue},14%,62%)"/>'
        f'<rect x="-25" y="-38" width="50" height="5" fill="hsl({hue},14%,48%)"/>'
        f'<rect x="-25" y="-20" width="50" height="5" fill="hsl({hue},14%,48%)"/>'
        f'<ellipse cx="0" cy="-52" rx="22" ry="5" fill="hsl({hue},14%,74%)"/>'
        "</g>"
    )


SHAPES = {"can": _can, "bottle": _bottle, "keg": _keg}


def render_frame(camera, now, shape="can"):
    """カメラ1台ぶんの疑似ライブ映像をSVG文字列で返す。

    now の秒・マイクロ秒で製品の位置をずらすことで、取得し直すたびに
    ラインが流れて見える。カメラごとに色味と位置を変えている。
    """
    draw = SHAPES.get(shape, _can)
    # カメラごとに見た目を変えるための値(同じカメラなら常に同じになる)
    hue = (camera.pk * 47) % 360
    seed = (camera.pk * 31) % PRODUCT_GAP

    elapsed = now.second + now.microsecond / 1_000_000
    offset = (elapsed * PRODUCT_SPEED + seed) % PRODUCT_GAP

    products = "".join(
        draw(x - offset, BELT_TOP, hue)
        for x in range(0, WIDTH + PRODUCT_GAP * 2, PRODUCT_GAP)
    )
    # 走査線。映像らしさを出すための薄い横線
    scanlines = "".join(
        f'<rect x="0" y="{y}" width="{WIDTH}" height="1" fill="#000" opacity="0.10"/>'
        for y in range(0, HEIGHT, 8)
    )

    name = escape(camera.name)
    line = escape(camera.server.line)
    stamp = now.strftime("%Y-%m-%d %H:%M:%S")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" role="img" aria-label="{name} のライブ映像(疑似)">
  <defs>
    <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#1b2433"/><stop offset="1" stop-color="#0d131c"/>
    </linearGradient>
    <radialGradient id="vignette" cx="0.5" cy="0.45" r="0.75">
      <stop offset="0.55" stop-color="#000" stop-opacity="0"/>
      <stop offset="1" stop-color="#000" stop-opacity="0.55"/>
    </radialGradient>
  </defs>

  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#wall)"/>
  <!-- 奥の設備 -->
  <rect x="44" y="96" width="104" height="120" fill="#151d29"/>
  <rect x="60" y="116" width="72" height="42" fill="#0b1119"/>
  <rect x="470" y="78" width="126" height="138" fill="#141c27"/>
  <rect x="488" y="100" width="90" height="34" fill="#0b1119"/>
  <rect x="0" y="210" width="{WIDTH}" height="8" fill="#0a0f16"/>
  <!-- コンベア -->
  <rect x="0" y="{BELT_TOP}" width="{WIDTH}" height="34" fill="#232d3d"/>
  <rect x="0" y="{BELT_TOP}" width="{WIDTH}" height="4" fill="#2f3b4e"/>
  <rect x="0" y="{BELT_TOP + 34}" width="{WIDTH}" height="{HEIGHT - BELT_TOP - 34}" fill="#0c1119"/>
  <!-- 流れている製品 -->
  <g>{products}</g>
  {scanlines}
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vignette)"/>

  <!-- ヘッドアップ表示 -->
  <circle cx="24" cy="26" r="6" fill="#ef4444"/>
  <text x="38" y="31" font-family="sans-serif" font-size="15" font-weight="bold" fill="#f8fafc">LIVE</text>
  <text x="{WIDTH - 16}" y="31" font-family="sans-serif" font-size="15" fill="#f8fafc" text-anchor="end">{name}</text>
  <text x="{WIDTH - 16}" y="52" font-family="sans-serif" font-size="12" fill="#94a3b8" text-anchor="end">{line}</text>
  <text x="16" y="{HEIGHT - 16}" font-family="monospace" font-size="15" fill="#e2e8f0">{stamp}</text>
  <text x="{WIDTH - 16}" y="{HEIGHT - 16}" font-family="sans-serif" font-size="11" fill="#64748b" text-anchor="end">DEMO / NxWitness未接続</text>
</svg>"""
