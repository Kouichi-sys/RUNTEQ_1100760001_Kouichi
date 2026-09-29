"""クリップの保存と書き出しの処理。

ビューは「画面からの入力を読む」「結果を返す」ことに集中させ、
映像の切り出し方やファイルの作り方はここにまとめる。
"""

import re
from datetime import timedelta

from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from cameras.video_sources import get_video_source

from .models import Clip

# 画面から送られてくる時刻を、どこまで信用するか
CAPTURE_TIME_TOLERANCE = timedelta(minutes=10)

# クリップとして切り取れる長さ
MIN_CLIP_SECONDS = 1
MAX_CLIP_SECONDS = 10 * 60

# 生成した映像のアニメーション定義。一覧用に取り除いて静止画にする
ANIMATION_STYLE = re.compile(r"<style>.*?</style>", re.DOTALL)


def resolve_capture_time(raw, now=None):
    """スクリーンショットを切り出す時刻を決める。

    動画を一時停止していればその時刻を使う。値は画面から送られてくるため、
    現在時刻から大きく離れていれば信用せず、いまの時刻に戻す。
    """
    now = now or timezone.now()
    if raw:
        parsed = parse_datetime(raw)
        if parsed and abs(now - parsed) < CAPTURE_TIME_TOLERANCE:
            return parsed
    return now


def resolve_clip_range(raw_start, raw_end, now=None):
    """クリップとして切り取る範囲を決める。

    戻り値は (開始, 終了, エラー文言)。指定が正しくないときは
    開始と終了をNoneにし、理由を返す。
    """
    now = now or timezone.now()
    start = parse_datetime(raw_start or "")
    end = parse_datetime(raw_end or "")

    if not start or not end:
        return None, None, "切り取る範囲が指定されていません。"
    if end <= start:
        return None, None, "終了は開始より後にしてください。"
    if start > now or end > now:
        return None, None, "未来の範囲は指定できません。"

    seconds = (end - start).total_seconds()
    if seconds < MIN_CLIP_SECONDS:
        return None, None, "範囲が短すぎます。1秒以上にしてください。"
    if seconds > MAX_CLIP_SECONDS:
        return None, None, "範囲が長すぎます。10分以内にしてください。"

    return start, end, None


def _store(clip, content, extension):
    """切り出した映像をファイルとして保存する。

    保存先の決定に taken_at を使うため、属性を入れ終えてから渡す。
    """
    clip.file.save(f"clip.{extension}", ContentFile(content), save=False)
    clip.save()
    return clip


def save_screenshot(*, user, camera, taken_at, title, memo):
    """その時点の1コマを保存する。"""
    content, extension, media_type = get_video_source().capture(
        camera, timezone.localtime(taken_at)
    )
    clip = Clip(
        user=user,
        camera=camera,
        title=title,
        memo=memo,
        taken_at=taken_at,
        media_type=media_type,
        seconds=0,
    )
    return _store(clip, content, extension)


def save_clip(*, user, camera, start_at, end_at, title, memo):
    """開始から終了までを切り取って保存する。"""
    content, extension, media_type = get_video_source().capture_range(
        camera, timezone.localtime(start_at), timezone.localtime(end_at)
    )
    clip = Clip(
        user=user,
        camera=camera,
        title=title,
        memo=memo,
        taken_at=start_at,
        media_type=media_type,
        seconds=int((end_at - start_at).total_seconds()),
    )
    return _store(clip, content, extension)


def still_image(clip):
    """一覧に並べるための静止画を返す。

    クリップ(動画)をそのまま並べると枚数だけ映像が動き続けて重くなるため、
    アニメーションの指定を外して最初のコマで止める。
    """
    with clip.file.open("rb") as stored:
        return ANIMATION_STYLE.sub("", stored.read().decode("utf-8"))


def needs_still_conversion(clip):
    """一覧用に静止画へ直す必要があるか。"""
    return clip.is_video and clip.file.name.endswith(".svg")


def needs_movie_conversion(clip):
    """共有用に動画へ直す必要があるか。

    mockの保存形式(SVG)はメールで配りにくい。実機のmp4は変換せずそのまま渡す。
    """
    return clip.is_video and clip.file.name.endswith(".svg")


def shareable_movie(clip):
    """メールに添付できる形式の動画を返す。(bytes, ファイル名)"""
    content, extension = get_video_source().export_movie(
        clip.camera, timezone.localtime(clip.taken_at)
    )
    return content, clip.movie_name(extension)
