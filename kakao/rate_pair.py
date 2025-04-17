from dataclasses import dataclass, field

@dataclass
class ExchangeRatePair:
    switch_one: float
    kakao: float
    diff: float = field(init=False)
    abs_diff: float = field(init=False)

    def __post_init__(self):
        self.diff = round(self.switch_one - self.kakao, 2)
        self.abs_diff = abs(self.diff)

    def is_switch_one_more_expensive(self) -> bool:
        return self.switch_one - self.kakao >= 1
    
    def __repr__(self):
        return f"(스위치원={self.switch_one}, 카카오={self.kakao}, 차이={self.diff})"

