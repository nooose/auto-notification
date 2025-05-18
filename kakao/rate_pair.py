from dataclasses import dataclass, field

class ExchangeRateError(Exception):
    """ExchangeRatePair 클래스에서 발생하는 예외의 기본 클래스입니다."""
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
class ExchangeRatePair:
    switch_one: float
    kakao: float
    diff: float = field(init=False)
    abs_diff: float = field(init=False)

    def __post_init__(self):
        self.diff = round(self.switch_one - self.kakao, 2)
        self.abs_diff = abs(self.diff)

        if (self.switch_one <= 1000 or self.kakao <= 1000):
            raise LowExchangeRateError(f"스위치원: {self.switch_one} 카카오: {self.kakao} - 환율이 너무 낮습니다.")
        if (self.switch_one >= 2000 or self.kakao >= 2000):
            raise HighExchangeRateError(f"스위치원: {self.switch_one} 카카오: {self.kakao} - 환율이 너무 높습니다.")
        if (self.abs_diff >= 30):
            raise LargeExchangeRateDifferenceError(f"환율 차이가 너무 큽니다. 스위치원: {self.switch_one} 카카오: {self.kakao} 차이: {self.diff}")

    def is_switch_one_more_expensive(self) -> bool:
        return self.switch_one - self.kakao >= 1
    
    def __repr__(self):
        return f"ExchangeRatePair (스위치원={self.switch_one}, 카카오={self.kakao}, 차이={self.diff})"

