import requests

from core.support.envrionment import Environment


class TelegramClient:
    """텔레그램 메신저 클라이언트이다.
    """

    def __init__(self, env: Environment):
        """TelegramClient 객체를 생성한다.

        Args:
            env (Environment): 환경 변수 객체
        """

        self.bot_token: str = env.get("TELEGRAM_BOT_TOKEN")
        self.chat_id: str = env.get("TELEGRAM_CHAT_ID")

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
