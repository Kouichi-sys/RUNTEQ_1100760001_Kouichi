"""過去映像の再生位置を決める処理。

画面から送られてくる日付・時刻の解釈をビューから切り離し、
単体で確かめられるようにする。
"""

from datetime import datetime, timedelta

from django.utils import timezone

# 日時を指定しなかったときに、どれだけ遡るか
DEFAULT_MINUTES_AGO = 60
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"

# 画面に並べる「よく使う範囲」
SHORTCUTS = [
    (10, "10分前"),
    (60, "1時間前"),
    (180, "3時間前"),
    (1440, "昨日の今ごろ"),
]


def resolve_playback_start(raw_date, raw_time, now=None):
    """カレンダーで選ばれた日付と時刻から、再生を始める時刻を決める。

    戻り値は (再生開始時刻, 画面に出す理由)。
    未来や読み取れない値は既定値に戻し、理由を添えて返す。
    """
    now = now or timezone.localtime()
    default = now - timedelta(minutes=DEFAULT_MINUTES_AGO)

    raw_date = (raw_date or "").strip()
    raw_time = (raw_time or "").strip()
    if not raw_date and not raw_time:
        return default, None

    # 片方だけ選ばれたときは、もう片方を既定値で補う
    raw_date = raw_date or default.strftime(DATE_FORMAT)
    raw_time = raw_time or default.strftime(TIME_FORMAT)

    try:
        parsed = timezone.make_aware(
            datetime.strptime(f"{raw_date} {raw_time}", f"{DATE_FORMAT} {TIME_FORMAT}")
        )
    except ValueError:
        return default, "日時を読み取れませんでした。既定の1時間前から再生します。"

    if parsed > now:
        return now, "未来の日時は指定できません。現在の映像を表示します。"
    return parsed, None


def playback_shortcuts(now=None):
    """「よく使う範囲」のリンク用に、日付と時刻を組にして返す。"""
    now = now or timezone.localtime()
    return [
        {
            "label": label,
            "date": (now - timedelta(minutes=minutes)).strftime(DATE_FORMAT),
            "time": (now - timedelta(minutes=minutes)).strftime(TIME_FORMAT),
        }
        for minutes, label in SHORTCUTS
    ]
