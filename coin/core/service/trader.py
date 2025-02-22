from typing import List, Optional
from datetime import datetime, timedelta, timezone

from core.api.upbit_client import UpbitClient
from core.data.candle import Candle
from core.data.trade_states import TradeState, OrderState

KST = timezone(timedelta(hours=9))


def now_kst() -> datetime:
    """현재 한국 시간(KST)을 반환한다."""
    return datetime.now(KST)


class Trader:
    """실 거래를 수행하는 클래스이다.
    """

    # TODO: 잔고에 금액이 있는지 유효성 체크 필요
    def __init__(self, volume: str, client: UpbitClient):
        """Trader 객체를 생성한다.

        Args:
            volume (str): 기본 거래 수량
            client (UpbitClient): 업비트 클라이언트
        """

        self.volume = volume
        self.client: UpbitClient = client
        self.state: TradeState = TradeState.INITIAL_BUY
        self.buy_time: Optional[datetime] = None
        self.completed_candle_time: Optional[datetime] = None
        self.last_order_uuid: Optional[str] = None

    def start_trading(self):
        """거래를 시작한다.
        """

        now = now_kst()
        candles = self.client.get_recent_candles(5)
        print(f"현재 시간: {now}=====================================")

        if (self.state == TradeState.INITIAL_BUY or
                self.state == TradeState.COMPLETED):
            self._attempt_buy(candles)

        elif self.state == TradeState.WAITING_SELL:
            self._check_sell_status(candles)

        elif self.state == TradeState.SELL_UNFILLED:
            self._average_down(candles)

        elif self.state == TradeState.AVERAGING_DOWN:
            self._check_averaging_status(candles)

    def _attempt_buy(self, candles: List[Candle]):
        """최근 캔들 목록을 기반으로 매수 주문을 시도한다.

        - 상태가 초기일 때 또는 매도가 완료되었을 때 실행된다.
        - 매수 조건을 만족하면 매수를 진행하고, 매도 주문을 설정한다.

        Args:
            candles (List[Candle]): 최근 캔들 목록
        """

        print("구매를 시도한다.")
        if self._should_buy(candles):
            return

        live_candle = candles[0]
        self.client.place_buy_order(self.volume)  # TODO: 시장가 주문
        uuid = self.client.place_sell_order(self.volume)  # TODO: 수량을 얼마 팔지

        self._set_buy_info(live_candle, uuid)
        self._change_state(TradeState.WAITING_SELL)

    def _should_buy(self, candles: List[Candle]) -> bool:
        """최근 캔들을 보고 매수 여부를 결정한다.

        Args:
            candles (List[Candle]): 최근 캔들 목록

        Returns:
            bool: 매수 여부 (True: 매수, False: 매수 안 함)
        """

        if any(candle.candle_date_time_kst == self.completed_candle_time for candle in candles):
            return False

        recent_candles = candles[1:]
        # for candle in recent_candles:
        # print(f"{candle.candle_date_time_kst} {candle.trade_price} {'red' if candle.is_red_candle() else 'blue'}")
        return len(recent_candles) == 4 and all(candle.is_blue_candle() for candle in recent_candles)

    def _set_buy_info(self, candle: Candle, uuid: str):
        """매수 정보를 설정하고 매도 마감 기한을 지정한다."""
        self.buy_time = candle.candle_date_time_kst
        self.last_order_uuid = uuid

    def _average_down(self, candles: List[Candle]):
        """평단가를 내리기 위해 물타기를 진행한다.
        - 상태가 매도 미체결일 때 실행된다.

        Args:
            candles (List[Candle]): 최근 캔들 목록
        """

        live_candle = candles[0]
        current_price = live_candle.trade_price
        print(f"물타기 시작: {current_price}")
        self.client.place_buy_order(self.volume)
        self.state = TradeState.AVERAGING_DOWN

    def _check_averaging_status(self, candles: List[Candle]):
        """물타기 상태에서 매수/매도 전략을 펼친다.
        - 상태가 물타기 진행 중일 때 실행된다.

        Args:
            candles (List[Candle]): 최근 캔들 목록
        """

        # 현재가를 계속 확인하면서 매도 주문 및 손절가 설정
        live_candle = candles[0]
        current_price = live_candle.trade_price

        accounts = self.client.get_my_account()
        krw_account = next((account for account in accounts if account.currency == 'KRW'), None)

        average_price = krw_account.avg_buy_price
        if current_price >= average_price + 6:
            # TODO: 주문 취소후 매도 요청
            print(f"매도 주문 가격 재설정: {average_price + 8}")
            self.buy_time = live_candle.candle_date_time_kst
            # 마지막 주문이 있다면 취소 후

            # 마지막 주문 UUID 세팅
        elif current_price <= average_price - 6:
            # TODO: 마지막 주문들 취소후 매도 요청
            print(f"손절 매도 주문 가격 설정: {average_price - 8}")
            self.buy_time = live_candle.candle_date_time_kst
            # 마지막 주문 UUID 세팅
        self._check_sell_status(candles)

    def _check_sell_status(self, candles: List[Candle]):
        """현재 매도 상태를 확인하여 상태를 변경한다.
        Args:
            candles (List[Candle]): 최근 캔들 목록
        """

        if (self.buy_time is None or
                self.last_order_uuid is None):
            return

        live_candle = candles[0]

        if live_candle.candle_date_time_kst == self.buy_time:
            order_state = self.client.get_order(self.last_order_uuid)
            if order_state == OrderState.DONE:
                self._complete(live_candle)
        elif self.state == TradeState.AVERAGING_DOWN:
            return
        else:
            self._change_state(TradeState.SELL_UNFILLED)

    def _complete(self, candle: Candle):
        self.completed_candle_time = candle.candle_date_time_kst
        self._change_state(TradeState.COMPLETED)
        self.last_order_uuid = None
        self.buy_time = None

    def _change_state(self, state: TradeState):
        self.state = state
