"""疑似映像を動くファイル(GIF)として書き出す。

クリップをメールで共有したいとき、SVGのままでは受け取った人が開きにくい。
GIFなら添付してそのまま再生でき、報告書にも貼れる。

mockの映像は製品が一定間隔で流れるだけなので、1周期ぶんを作って
ループさせれば、何秒のクリップでも同じ見え方になる。
実機のNxWitnessに繋いだあとは、区間の動画(mp4)をそのまま渡す。
"""

import colorsys
import io

from PIL import Image, ImageDraw

from .mock_frame import BELT_TOP, HEIGHT, PRODUCT_GAP, PRODUCT_SPEED, WIDTH, _offset_at

# 1周期ぶんを何コマで表すか。増やすと滑らかになるがファイルが重くなる
FRAMES = 24
CYCLE_SECONDS = PRODUCT_GAP / PRODUCT_SPEED

WALL = (18, 26, 38)
FLOOR = (12, 17, 25)
BELT = (35, 45, 61)
BELT_EDGE = (47, 59, 78)
EQUIPMENT = (21, 29, 41)
EQUIPMENT_DARK = (11, 17, 25)


def _hsl(hue, saturation, lightness):
    """SVG側と同じ色指定(hsl)をRGBに直す。"""
    r, g, b = colorsys.hls_to_rgb(hue / 360, lightness / 100, saturation / 100)
    return int(r * 255), int(g * 255), int(b * 255)


def _draw_can(draw, x, y, hue):
    draw.rectangle([x - 15, y - 46, x + 15, y], fill=_hsl(hue, 45, 62))
    draw.rectangle([x - 15, y - 40, x + 15, y - 33], fill=_hsl(hue, 55, 45))
    draw.rectangle([x - 15, y - 20, x + 15, y - 15], fill=_hsl(hue, 55, 45))
    draw.ellipse([x - 15, y - 51, x + 15, y - 41], fill=_hsl(hue, 25, 78))


def _draw_bottle(draw, x, y, hue):
    body = _hsl(hue, 50, 40)
    draw.polygon(
        [
            (x - 12, y), (x - 12, y - 34), (x - 9, y - 44), (x - 5, y - 50),
            (x - 5, y - 62), (x + 5, y - 62), (x + 5, y - 50), (x + 9, y - 44),
            (x + 12, y - 34), (x + 12, y),
        ],
        fill=body,
    )
    draw.rectangle([x - 12, y - 28, x + 12, y - 16], fill=_hsl(hue, 20, 86))
    draw.rectangle([x - 5, y - 66, x + 5, y - 61], fill=_hsl(hue, 40, 58))


def _draw_keg(draw, x, y, hue):
    body = _hsl(hue, 14, 62)
    draw.polygon(
        [
            (x - 22, y), (x - 26, y - 26), (x - 22, y - 52),
            (x + 22, y - 52), (x + 26, y - 26), (x + 22, y),
        ],
        fill=body,
    )
    draw.rectangle([x - 25, y - 38, x + 25, y - 33], fill=_hsl(hue, 14, 48))
    draw.rectangle([x - 25, y - 20, x + 25, y - 15], fill=_hsl(hue, 14, 48))
    draw.ellipse([x - 22, y - 57, x + 22, y - 47], fill=_hsl(hue, 14, 74))


SHAPES = {"can": _draw_can, "bottle": _draw_bottle, "keg": _draw_keg}


def _frame(camera, offset, shape):
    """1コマぶんの絵を作る。"""
    image = Image.new("RGB", (WIDTH, HEIGHT), WALL)
    draw = ImageDraw.Draw(image)

    # 奥の設備
    draw.rectangle([44, 96, 148, 216], fill=EQUIPMENT)
    draw.rectangle([60, 116, 132, 158], fill=EQUIPMENT_DARK)
    draw.rectangle([470, 78, 596, 216], fill=EQUIPMENT)
    draw.rectangle([488, 100, 578, 134], fill=EQUIPMENT_DARK)
    draw.rectangle([0, 210, WIDTH, 218], fill=(10, 15, 22))

    # コンベア
    draw.rectangle([0, BELT_TOP, WIDTH, BELT_TOP + 34], fill=BELT)
    draw.rectangle([0, BELT_TOP, WIDTH, BELT_TOP + 4], fill=BELT_EDGE)
    draw.rectangle([0, BELT_TOP + 34, WIDTH, HEIGHT], fill=FLOOR)

    # 流れている製品
    paint = SHAPES.get(shape, _draw_can)
    hue = (camera.pk * 47) % 360
    for x in range(0, WIDTH + PRODUCT_GAP * 2, PRODUCT_GAP):
        paint(draw, x - offset, BELT_TOP, hue)

    # 走査線
    for y in range(0, HEIGHT, 8):
        draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0), width=1)

    return image


def render_gif(camera, start_at, shape="can"):
    """流れ続ける映像をGIFのバイト列で返す。"""
    base = _offset_at(camera, start_at)
    frames = [
        _frame(camera, (base + PRODUCT_GAP * i / FRAMES) % PRODUCT_GAP, shape)
        for i in range(FRAMES)
    ]

    buffer = io.BytesIO()
    frames[0].save(
        buffer,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=int(CYCLE_SECONDS * 1000 / FRAMES),
        loop=0,
        optimize=True,
    )
    return buffer.getvalue()
