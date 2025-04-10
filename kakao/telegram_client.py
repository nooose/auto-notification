import requests

from telegram_properties import TelegramProperties


class TelegramClient:
    """텔레그램 메신저 클라이언트이다.
    """

    def __init__(self, properties: TelegramProperties):
        """TelegramClient 객체를 생성한다.

        :param properties: 텔레그램 프로퍼티
        """

        self.bot_token: str = properties.bot_token
        self.chat_id: str = properties.chat_id

    def send_message(self, message):
        """
        메시지를 전송한다.

        :param message: 채널에 전달할 메시지
        """
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
