from dataclasses import dataclass, field
from typing import Optional

class ExchangeRateError(Exception):
    """ExchangeRates 클래스에서 발생하는 예외의 기본 클래스입니다."""
    pass

class LowExchangeRateError(ExchangeRateError):
    """환율이 너무 낮을 때 발생하는 예외입니다."""
    pass

class HighExchangeRateError(ExchangeRateError):
    """환율이 너무 높을 때 발생하는 예외입니다."""
    pass

class LargeExchangeRateDifferenceError(ExchangeRateError):
    """환율 차이가 너무 클 때 발생하는 예외입니다."""
    pass

@dataclass
class ExchangeRates:
    kakao: float
    google: float
    woori: float
    hana: float
    threshold: float = 0.01 # 임계값
    
    avg_rate: float = field(init=False)
    avg_diff: float = field(init=False)

    def __post_init__(self):
        self.avg_rate = (self.google + self.woori + self.hana) / 3
        self.avg_diff = self.avg_rate - self.kakao

    def is_over_threshold(self) -> bool:
        """다른 은행들의 환율이 카카오 환율보다 임계값 이상 높은지 확인합니다."""
        over_count = 0
        other_rates = [self.google, self.woori, self.hana]

        for rate in other_rates:
            if rate - self.kakao >= self.threshold:
                over_count += 1
        
        return over_count >= 2

    def format_alert_message(self) -> str:
        RISE_EMOJI = "🔺"
        FALL_EMOJI = "▼"

        title = f"$ 카뱅 ({self.kakao:.2f}원) 상승 기회"        
        lines = [
            title,
            "",
            f"카뱅: {self.kakao:.2f}원",
        ]

        # Google Finance
        google_diff = self.google - self.kakao
        google_emoji = RISE_EMOJI if google_diff >= 0 else FALL_EMOJI
        lines.append(f"평균: {self.google:.2f}원 [{google_emoji}] {abs(google_diff):.2f}원")

        # Hana Bank
        hana_diff = self.hana - self.kakao
        hana_emoji = RISE_EMOJI if hana_diff >= 0 else FALL_EMOJI
        lines.append(f"하나: {self.hana:.2f}원 [{hana_emoji}] {abs(hana_diff):.2f}원")

        # Woori Bank
        woori_diff = self.woori - self.kakao
        woori_emoji = RISE_EMOJI if woori_diff >= 0 else FALL_EMOJI
        lines.append(f"우리: {self.woori:.2f}원 [{woori_emoji}] {abs(woori_diff):.2f}원")

        return "\n".join(lines)

    def __repr__(self):
        return f"ExchangeRates (카카오={self.kakao:.2f}, 구글={self.google:.2f}, 우리={self.woori:.2f}, 하나={self.hana:.2f}, 평균={self.avg_rate:.2f})"