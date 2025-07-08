from dataclasses import dataclass


@dataclass
class TelegramProperties:
    """텔레그램 프로퍼티
    """

    bot_token: str
    chat_id: str
