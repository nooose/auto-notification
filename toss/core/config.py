from dataclasses import dataclass, field
from typing import List, Dict
from envrionments import Environments

@dataclass(frozen=True)
class Config:
    """애플리케이션의 모든 설정을 담고 있습니다."""
    bot_token: str
    chat_id: str
    target_currencies: List[str]
    currency_code_to_display_name: Dict[str, str]
    currency_code_to_outlier_threshold: Dict[str, float]

    @classmethod
    def from_env(cls):
        """환경 변수에서 설정을 불러옵니다."""
        target_currencies = ["CNY", "HKD", "TWD", "THB", "SGD", "PHP", "MYR"]
        currency_code_to_display_name = {
            "CNY": "위안", "HKD": "달러", "TWD": "달러", "THB": "바트",
            "SGD": "달러", "PHP": "페소", "MYR": "링깃",
        }
        currency_code_to_outlier_threshold = {
            code: float(Environments.get(f"{code}_OUTLIER", 0))
            for code in currency_code_to_display_name
        }
        
        return cls(
            bot_token=Environments.get("TELEGRAM_BOT_TOKEN"),
            chat_id=Environments.get("TELEGRAM_CHAT_ID"),
            target_currencies=target_currencies,
            currency_code_to_display_name=currency_code_to_display_name,
            currency_code_to_outlier_threshold=currency_code_to_outlier_threshold
        )
