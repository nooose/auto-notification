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
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import os

# 로그 설정
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-level", default="INFO", help="Set log level (e.g. DEBUG, INFO, WARNING)")
    return parser.parse_args()

LOG_DIR = "logs"
LOG_FILENAME = "app.log"

logging.basicConfig(
    level=getattr(logging, get_args().log_level.upper(), logging.INFO),
    format='[%(asctime)s] %(levelname)s - %(message)s',
    stream=sys.stdout
)

log_path = os.path.join(LOG_DIR, LOG_FILENAME)
os.makedirs(LOG_DIR, exist_ok=True)
handler = TimedRotatingFileHandler(
    log_path,
    when="midnight",
    interval=1,
    backupCount=5,  # 보관할 로그 파일 수
    encoding="utf-8"
)

log = logging.getLogger(__name__)
log.addHandler(handler)

# 애플리케이션

INTERVAL_SECONDS = 10
KAKAO_CROP_AREA = (236, 366, 610, 183)
SWITCH_ONE_CROP_AREA = (61, 1268, 418, 112)
AMOUNT_PATTERN = r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b"

def normalize_amount(amount: str) -> float:
    matches = re.findall(AMOUNT_PATTERN, amount)
    if not matches:
        raise ValueError(f"유효한 금액 형식을 찾을 수 없습니다: '{amount}'")

    first_match = matches[0]

    # 마침표가 2개 이상인 경우 → 마지막 마침표만 소수점으로 간주
    if first_match.count('.') > 1:
        last_dot_index = first_match.rfind('.')
        first_match = first_match[:last_dot_index].replace('.', ',') + first_match[last_dot_index:]

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
            log.info(f"메타 정보: {meta_data}")

            kakao_image_path = processor.crop_image(image_path="pre.jpg", output_path="kakako.jpg", crop_rect=KAKAO_CROP_AREA)
            switch_image_path = processor.crop_image(image_path="pre.jpg", output_path="switch.jpg", crop_rect=SWITCH_ONE_CROP_AREA)
            kakao_text = ocr_reader.extract_text(image_path=kakao_image_path)
            switch_text = ocr_reader.extract_text(image_path=switch_image_path)
            
            log.info(f"카카오 추출 환율: {kakao_text}")
            log.info(f"스위치 추출 환율: {switch_text}")

            kakao = normalize_amount(kakao_text)
            switch_one = normalize_amount(switch_text)
            pair = ExchangeRatePair(switch_one=switch_one, kakao=kakao)                

            if previous_pair == pair:
                time.sleep(INTERVAL_SECONDS)
                continue

            log.info(f"환율 정보: {pair}")

            if (pair.is_switch_one_more_expensive()):
                message = f"갭 {pair.diff:.2f}원 (🔼 가능성)\n평균: {pair.switch_one}\n카뱅: {pair.kakao}\n기준시각: '{meta_data.kst_creation_time()}'"
                telegram_client.send_message(message=message)
                last_rise_alert_time = datetime.datetime.now()
            else:
                now = datetime.datetime.now()
                if last_rise_alert_time is not None and now < last_rise_alert_time + datetime.timedelta(minutes=5):

                    if pair.diff > 0:
                        message = f"갭 {pair.diff:.2f}원 (갭이 작아졌습니다‼)\n평균: {pair.switch_one}\n카뱅: {pair.kakao}"
                    else:
                        message = f"갭 {pair.diff:.2f}원 (마이너스 갭‼‼)\n평균: {pair.switch_one}\n카뱅: {pair.kakao}"
                    telegram_client.send_message(message=message)

            previous_pair = pair
        except Exception as e:
            log.exception(f"오류 발생: {e}")
        time.sleep(INTERVAL_SECONDS)