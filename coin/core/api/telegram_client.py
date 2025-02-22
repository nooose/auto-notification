import requests

from core.api.telegram_properties import TelegramProperties


class TelegramClient:
    """텔레그램 메신저 클라이언트이다.
    """

    def __init__(self, properties: TelegramProperties):
        """TelegramClient 객체를 생성한다.

        Args:
            properties (TelegramProperties): 프로퍼티
        """

        self.bot_token: str = properties.bot_token
        self.chat_id: str = properties.chat_id

    async def send_message(self, message):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        try:
            response = requests.post(url, data=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"텔레그램 메시지 전송 실패: {e}")
