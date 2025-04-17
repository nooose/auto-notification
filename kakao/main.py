import time
from google_photo_downloader import PhotoDownloader
from photo_processor import PhotoProcessor
from ocr import OCRReader
from rate_pair import ExchangeRatePair
from photo_meta import PhotoMeta
import re
from telegram_properties import TelegramProperties
from telegram_client import TelegramClient
from envrionments import Environments
import argparse
import datetime

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Enable debug mode") # 옵션이 있으면 True, 없으면 False
    return parser.parse_args()

DEBUG = get_args().debug
INTERVAL_SECONDS = 10

KAKAO_CROP_AREA = (236, 366, 610, 183)
SWITCH_ONE_CROP_AREA = (61, 1268, 418, 112)

AMOUNT_PATTERN = r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b"

def normalize_amount(amount: str) -> float:
    matches = re.findall(AMOUNT_PATTERN, amount)
    first_match = matches[0] if matches else None
    cleaned = first_match.replace(',', '')
    return round(float(cleaned), 2)

if __name__ == "__main__":
    downloader = PhotoDownloader()
    processor = PhotoProcessor()
    ocr_reader = OCRReader()

    telegram_properties = TelegramProperties(
        bot_token=Environments.get("TELEGRAM_BOT_TOKEN"),
        chat_id=Environments.get("TELEGRAM_CHAT_ID"),
    )
    telegram_client = TelegramClient(telegram_properties)

    last_rise_alert_time = None
    previous_pair = None

    while True:
        try:
            meta_data = downloader.download_latest_photo(save_as="pre.jpg")

            if DEBUG:
                print(f"메타 정보: {meta_data}")

            kakao_image_path = processor.crop_image(image_path="pre.jpg", output_path="kakako.jpg", crop_rect=KAKAO_CROP_AREA)
            switch_image_path = processor.crop_image(image_path="pre.jpg", output_path="switch.jpg", crop_rect=SWITCH_ONE_CROP_AREA)
            kakao_text = ocr_reader.extract_text(image_path=kakao_image_path)
            switch_text = ocr_reader.extract_text(image_path=switch_image_path)
            
            if DEBUG:
                print(f"카카오 추출 환율: {kakao_text}\n스위치 추출 환율: {switch_text}")

            kakao = normalize_amount(kakao_text)
            switch_one = normalize_amount(switch_text)
            pair = ExchangeRatePair(switch_one=switch_one, kakao=kakao)                

            if previous_pair == pair:
                time.sleep(INTERVAL_SECONDS)
                continue

            if DEBUG:
                print(f"환율 정보: {pair}")

            if (pair.is_switch_one_more_expensive()):
                message = f"갭 {pair.diff:.2f}원 (🔼 가능성)\n평균: {pair.switch_one}\n카뱅: {pair.kakao}\n기준시각: '{meta_data.kst_creation_time()}'"
                telegram_client.send_message(message=message)
                last_rise_alert_time = datetime.datetime.now()
            else:
                now = datetime.datetime.now()
                if last_rise_alert_time is not None and now < last_rise_alert_time + datetime.timedelta(minutes=5):
                    message = f"갭 -{pair.diff:.2f}원 (마이너스 갭‼‼)\n평균: {pair.switch_one}\n카뱅: {pair.kakao}"
                    telegram_client.send_message(message=message)

            previous_pair = pair
        except Exception as e:
            print(f"오류 발생: {e}")
        time.sleep(INTERVAL_SECONDS)