from dataclasses import dataclass
from typing import Dict


@dataclass
class Account:
    """계좌 정보를 담는 값 클래스
    """

    currency: str
    balance: float # 주문가능 금액/수량
    locked: float # 주문 중 묶여있는 금액/수량
    avg_buy_price: float # 매수 평균가
    avg_buy_price_modified: bool
    unit_currency: str

    @staticmethod
    def from_response(data: Dict) -> "Account":
        """API 응답 데이터로부터 계좌 객체를 생성한다.

        :param data: API 응답 딕셔너리
        :return: 계좌 객체
        """
        return Account(
            currency=data["currency"],
            balance=float(data["balance"]),
            locked=data["locked"],
            avg_buy_price=float(data["avg_buy_price"]),
            avg_buy_price_modified=data["avg_buy_price_modified"],
            unit_currency=data["unit_currency"],
        )
