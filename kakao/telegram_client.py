import requests
import json
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

    def send_message(self, message: str):
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

    def send_photo(self, photo_path: str, caption: str ):
        """
        사진을 전송한다.

        :param photo_path: 사진 경로
        """
        url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
        files = {
            "photo": open(photo_path, "rb")
        }
        payload = {
            "chat_id": self.chat_id,
            "caption": caption
        }

        try:
            response = requests.post(url, files=files, data=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"텔레그램 사진 전송 실패: {e}")

    def send_photo_group(self, photo_path_to_caption: dict[str, str]):
        """
        여러 장의 사진을 각각 캡션과 함께 전송한다.

        :param photo_path_to_caption: {사진 경로: 캡션} 딕셔너리
        """
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMediaGroup"

        media = []
        files = {}

        try:
            for idx, (photo_path, caption) in enumerate(photo_path_to_caption.items()):
                attach_name = f"photo{idx}"
                media.append({
                    "type": "photo",
                    "media": f"attach://{attach_name}",
                    "caption": caption
                })
                files[attach_name] = open(photo_path, "rb")

            data = {
                "chat_id": self.chat_id,
                "media": json.dumps(media)
            }

            response = requests.post(url, data=data, files=files)
            response.raise_for_status()

        except requests.RequestException as e:
            print(f"텔레그램 사진 그룹 전송 실패: {e}")

        finally:
            for f in files.values():
                f.close()