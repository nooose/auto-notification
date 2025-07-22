
from abc import ABC, abstractmethod

class ExchangeRateFetcher(ABC):
    @abstractmethod
    def get_usd_rate(self) -> float:
        pass
