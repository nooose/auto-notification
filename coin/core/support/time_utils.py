from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))


def now_kst() -> datetime:
    """현재 한국 시간(KST)을 반환한다.
    """
    return datetime.now(KST)
