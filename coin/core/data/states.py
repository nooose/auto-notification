from enum import Enum


class TradeState(Enum):
    """거래 상태를 나타내는 값이다.
    """

    INITIAL = "첫번째 단계"
    DCA = "Dollar-Cost Averaging(물타기)"
    DCA_BUY_COMPLETED = "물타기 매수 완료"
    DCA_SELL_ORDER_COMPLETED = "물타기 매도 주문 완료"
    COMPLETED = "매도 완료"

class OrderState(Enum):
    """주문 상태를 나타내는 값이다.
    """

    WAIT = "체결 대기"
    WATCH = "예약 주문 대기"
    CANCEL = "주문 취소"
    DONE = "주문 완료"

    @staticmethod
    def value_of(value: str) -> "OrderState":
        """문자열을 주문 상태로 변환한다.

        :param value 주문 상태 문자열
        :return: 주문 상태 값
        :raise ValueError: 일치하는 주문 상태가 없으면 발생할 수 있다.
        """

        try:
            return OrderState[value.upper()]
        except KeyError:
            raise ValueError(f"일치하는 주문 상태가 없습니다: {value}")

class SellDecision(Enum):
    """매도 결정을 위한 값이다.
    """

    PROFIT = "수익화"
    CUT_LOSS = "손절"
    HOLD = "보류"
