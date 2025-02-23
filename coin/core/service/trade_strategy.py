from typing import List
from core.data.candle import Candle
from core.data.states import SellDecision


class TradeStrategy:
    """매매 전략을 책임지는 클래스.
    """

    def __init__(self, margin: int):
        """매매 전략 생성자

        :param margin: 거래 당 최소 수익 금액
        """

        self.detection_margin = margin - 2

    @staticmethod
    def should_buy(candles: List[Candle]) -> bool:
        """첫 매수 여부를 판단한다.

        :param candles: 최근 캔들 목록
        :return: 매수 여부
        """

        recent_candles = candles[1:]
        return len(recent_candles) == 3 and all(candle.is_blue_candle() for candle in recent_candles)

    def should_sell(self, average_price: float, current_price: float) -> SellDecision:
        """DCA 중 매도 여부를 결정한다.

        :param average_price: 평균 매수 가격
        :param current_price: 현재 거래 가격
        :return: 매도 결정 값
        """

        profit_threshold = average_price + self.detection_margin
        stop_loss_threshold = average_price - self.detection_margin

        if current_price >= profit_threshold:
            return SellDecision.PROFIT

        if current_price <= stop_loss_threshold:
            return SellDecision.CUT_LOSS

        return SellDecision.HOLD
