from dataclasses import dataclass
from datetime import datetime
from typing import Dict


@dataclass
class Candle:
    """캔들 정보를 담는 값 클래스
    """

    market: str
    candle_date_time_utc: datetime
    candle_date_time_kst: datetime
    opening_price: float
    high_price: float
    low_price: float
    trade_price: float
    timestamp: int
    candle_acc_trade_price: float
    candle_acc_trade_volume: float
    unit: int

    @staticmethod
    def from_response(data: Dict) -> "Candle":
        """API 응답 데이터로부터 Candle 객체를 생성한다.
        Args:
            data (Dict): API 응답 데이터
        Returns:
            Candle: Candle 객체
        """
        return Candle(
            market=data["market"],
            candle_date_time_utc=datetime.fromisoformat(data["candle_date_time_utc"]),
            candle_date_time_kst=datetime.fromisoformat(data["candle_date_time_kst"]),
            opening_price=data["opening_price"],
            high_price=data["high_price"],
            low_price=data["low_price"],
            trade_price=data["trade_price"],
            timestamp=data["timestamp"],
            candle_acc_trade_price=data["candle_acc_trade_price"],
            candle_acc_trade_volume=data["candle_acc_trade_volume"],
            unit=data["unit"]
        )

    def is_red_candle(self):
        """양봉인지 확인한다.
        Returns:
            bool: 양봉 여부
        """
        return self.opening_price < self.trade_price

    def is_blue_candle(self):
        """음봉인지 확인한다.
        Returns:
            bool: 음봉 여부
        """
        return self.opening_price > self.trade_price

    def is_doji(self):
        """시가와 종가가 같은지 확인한다.
        Returns:
            bool: 도지 여부
        """
        return self.opening_price == self.trade_price
