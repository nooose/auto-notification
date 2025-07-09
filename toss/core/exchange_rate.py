from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

@dataclass(frozen=True)
class ExchangeRate:
    """단일 통화에 대한 환율을 나타냅니다."""
    currency_code: str
    base_rate: float
    country_name: str

@dataclass(frozen=True)
class RateMeta:
    """환율 세트에 대한 메타데이터입니다."""
    publish_datetime: str
    round_number: str
    created_at: datetime = field(default_factory=lambda: datetime.now(KST))
