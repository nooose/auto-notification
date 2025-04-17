from dataclasses import dataclass, field

@dataclass
class ExchangeRatePair:
    switch_one: float
    kakao: float
    diff: float = field(init=False)  # 생성자에서 초기화하지 않음

    def __post_init__(self):
        self.diff = round(abs(self.switch_one - self.kakao), 2)

    def is_switch_one_more_expensive(self) -> bool:
        return self.switch_one - self.kakao >= 0.05
    
    def __repr__(self):
        return f"(스위치원={self.switch_one}, 카카오={self.kakao}, 차이={self.diff})"

