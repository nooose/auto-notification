from typing import List, Optional
from datetime import datetime

from core.api.telegram_client import TelegramClient
from core.api.upbit_client import UpbitClient
from core.data.candle import Candle
from core.data.states import TradeState, OrderState, SellDecision
from core.service.trade_strategy import TradeStrategy
from core.support.time_utils import now_kst


class AutoTrader:
    """자동 거래를 수행하는 클래스이다.
    """

    # TODO: 잔고에 금액이 있는지 유효성 체크 필요
    def __init__(self,
                 margin: float,
                 volume: str,
                 strategy: TradeStrategy,
                 upbit_client: UpbitClient,
                 telegram_client: TelegramClient,
                 ):
        """객체를 생성한다.

        :param margin: 거래 당 최소 수익
        :param volume: 기본 거래 수량
        :param strategy: 거래 전략 객체
        :param upbit_client: 업비트 API 클라이언트
        :param telegram_client: 텔레그램 API 클라이언트
        """

        self.margin = margin
        self.volume = volume
        self.strategy = strategy
        self.upbit_client = upbit_client
        self.telegram_client = telegram_client
        self.state: TradeState = TradeState.INITIAL
        self.buy_time: Optional[datetime] = None
        self.completed_candle_time: Optional[datetime] = None
        self.last_buy_order_uuid: Optional[str] = None
        self.last_sell_order_uuid: Optional[str] = None

    def trading(self):
        """상태에 따라 거래를 수행한다.
        """

        now = now_kst()
        candles = self.upbit_client.get_recent_candles(4)
        live_candle = candles[0]
        print(f"현재 시간: {now}=====================================")

        if (self.state == TradeState.INITIAL or
                self.state == TradeState.COMPLETED):
            self._attempt_buy(candles)
            return

        if self.is_order_done(uuid=self.last_sell_order_uuid):
            self.sell_completed(candle=live_candle)
            self.telegram_client.send_message("[자동] 매도 체결 완료")
            return

        if self.state == TradeState.DCA:
            account = self._my_account()
            avg_buy_price = account.avg_buy_price
            market_price = live_candle.trade_price
            decision = self.strategy.should_sell(average_price=avg_buy_price, current_price=market_price)
            if decision == SellDecision.CUT_LOSS:
                target_price = round(avg_buy_price - self.margin)
                self._buy(target_price)
                self.telegram_client.send_message(f"[자동] 물타기 매수 주문 완료 {target_price}원")
                self.state = TradeState.DCA_BUY_COMPLETED
                return

        if self.state == TradeState.DCA_BUY_COMPLETED and self.is_order_done(self.last_buy_order_uuid):
            self.upbit_client.cancel_order(self.last_sell_order_uuid)
            account = self._my_account()
            self._sell(volume=str(account.balance), price=account.avg_buy_price)
            self.state = TradeState.DCA_SELL_ORDER_COMPLETED
            self.telegram_client.send_message(f"[자동] 물타기 매도 주문 완료 {round(account.avg_buy_price)}원")

    def _attempt_buy(self, candles: List[Candle]):
        """최근 캔들 목록을 기반으로 매수 주문을 시도한다.

        - 초기 상태 또는 매도가 완료되었을 때 실행된다.
        - 매수 조건을 만족하면 매수를 진행하고, 매도 주문을 한다.

        :param candles: 최근 갠들 목록
        """

        if not self._should_buy(candles):
            return

        live_candle = candles[0]
        opening_price = live_candle.opening_price
        target_buy_price = round(opening_price + 1.0)
        self._buy(target_buy_price)
        self.buy_time = live_candle.candle_date_time_kst

        avg_price = self._my_account().avg_buy_price
        target_sell_price = round(avg_price + self.margin)
        self._sell(self.volume, target_sell_price)

        self._change_state(TradeState.DCA)
        self.telegram_client.send_message(f"[자동] 주문 완료 매수: {target_buy_price}({self.volume}개), 매도: {target_sell_price}")

    def _should_buy(self, candles: List[Candle]) -> bool:
        """최근 캔들을 보고 매수 여부를 결정한다.

        :param candles: 최근 캔들 목록
        :return: 매수 여부
        """

        if any(candle.candle_date_time_kst == self.completed_candle_time for candle in candles):
            return False

        return self.strategy.should_buy(candles)


    def _my_account(self):
        """나의 계좌를 조회한다.

        :return: 내 계좌
        """

        return self.upbit_client.get_my_account()

    def _change_state(self, state: TradeState):
        """ 거래 상태를 변경한다.

        :param state: 거래 상태
        """

        self.state = state

    def _buy(self, price: float):
        """매수 주문
        :param price: 주문 가격
        :return: 주문 UUID
        """
        uuid = self.upbit_client.place_buy_order(self.volume, price)
        self.last_buy_order_uuid = uuid
        return uuid

    def _sell(self, volume: str, price: float):
        """매도 주문

        :param volume: 주문 수량
        :param price: 주문 가격
        :return: 주문 UUID
        """

        uuid = self.upbit_client.place_sell_order(volume, price)
        self.last_sell_order_uuid = uuid
        return uuid

    def is_order_done(self, uuid: str):
        """주문이 완료되었는지 확인한다.

        :param uuid: 주문 UUID
        :return: 완료 여부
        """

        if uuid is None:
            return False

        state = self.upbit_client.get_order(uuid)
        return state == OrderState.DONE

    def sell_completed(self, candle: Candle):
        """매도 체결을 완료한다.

        :param candle: 체결된 시점의 캔들 객체
        """

        self.completed_candle_time = candle.candle_date_time_kst
        self._change_state(TradeState.COMPLETED)
        self.last_sell_order_uuid = None
