from dataclasses import dataclass

@dataclass
class ExchangeRatePair:
    switch_one: float
    kakao: float

    def __repr__(self):
        return f"(스위치원={self.switch_one}, 카카오={self.kakao})"

    def is_switch_one_more_expensive(self) -> bool:
        return self.switch_one - self.kakao >= 1

    def diff(self) -> float:
        return abs(self.switch_one - self.kakao)