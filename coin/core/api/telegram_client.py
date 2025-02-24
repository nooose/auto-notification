from typing import Dict

import threading
import requests
from concurrent.futures import ThreadPoolExecutor
from core.api.telegram_properties import TelegramProperties


class TelegramClient:
    """텔레그램 메신저 클라이언트이다.
    """

    def __init__(self, properties: TelegramProperties):
        """TelegramClient 객체를 생성한다.

        :param properties: 텔레그램 프로퍼티
        """

        self.bot_token: str = properties.bot_token
        self.chat_id: str = properties.chat_id
        self.url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        self.executor = ThreadPoolExecutor(max_workers=3)

    def async_send_message(self, message):
        """동기 코드에서 비동기 메시지 전송을 호출하는 래퍼
        """
    
        self.executor.submit(self.send_message, message)

    def send_message(self, message):
        """텔레그램에 메시지를 전송한다.

        :param message: 전송할 메시지
        """
                
        payload = self._create_payload(message)
        try:
            response = requests.post(self.url, data=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"텔레그램 메시지 전송 실패: {e}")

    def _create_payload(self, message: str) -> Dict:
        """텔레그램 API 요청에 사용되는 payload를 생성한다.

        :param message: 전송할 메시지
        :return: payload
        """

        return {"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"}
    
    def __del__(self):
        """객체 소멸 시 스레드 풀 정리"""
        self.executor.shutdown(wait=False)