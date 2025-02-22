from enum import Enum


class TradeState(Enum):
    """거래 상태를 나타내는 값이다.
    """

    INITIAL_BUY = "첫 매수 완료"
    WAITING_SELL = "매도 체결 대기"
    SELL_UNFILLED = "매도 미체결"
    AVERAGING_DOWN = "물타기 진행"
    COMPLETED = "매도 완료"


class OrderState(Enum):
    """주문 상태를 나타내는 값이다.
    """

    WAIT = "주문 대기"
    DONE = "주문 완료"

    @staticmethod
    def value_of(value: str) -> "OrderState":
        """문자열을 OrderState로 변환한다."""
        try:
            return OrderState[value.upper()]
        except KeyError:
            raise ValueError(f"Invalid order state: {value}")  # 예외 처리
