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
KAKAO_CROP_AREA = (249, 380, 563, 149)
SWITCH_ONE_CROP_AREA = (286, 1199, 405, 129)
REFRESH_CROP_AREA = (284, 523, 515, 69)

AMOUNT_PATTERN = re.compile(r"\b(?:(?:\d{1,3}(?:[.,]\d{3})+)|\d+)(?:[.,]\d{2})\b")
NOISE_AMOUNT = 0.03

def normalize_amount(amount: str) -> float:
    amount_text = amount.strip()
    match = AMOUNT_PATTERN.search(amount_text)
    if not match:
        raise ValueError(f"유효한 금액 형식을 찾을 수 없습니다: '{amount_text}'")

    amount_text = match.group()
    dot_count = amount_text.count('.')

    if dot_count > 1:
        unified = amount_text.replace(',', '.')
        last_dot = unified.rfind('.')
        integer_part = unified[:last_dot].replace('.', '')
        decimal_part = unified[last_dot + 1:]

        normalized = f"{integer_part}.{decimal_part}"
        return float(normalized)

    try:
        return float(amount_text.replace(',', ''))
    except ValueError:
        raise ValueError(f"올바르지 않은 숫자 형식입니다: '{amount_text}'")

if __name__ == "__main__":
    downloader = PhotoDownloader()
    processor = PhotoProcessor()
    ocr_reader = OCRReader()

    telegram_properties = TelegramProperties(
        bot_token=Environments.get("TELEGRAM_BOT_TOKEN"),
        chat_id=Environments.get("TELEGRAM_CHAT_ID"),
    )
    telegram_client = TelegramClient(telegram_properties)

    telegram_monitoring_properties = TelegramProperties(
        bot_token=Environments.get("TELEGRAM_BOT_TOKEN"),
        chat_id=Environments.get("TELEGRAM_MONITORING_CHAT_ID"),
    )
    telegram_monitoring_client = TelegramClient(telegram_monitoring_properties)

    last_rise_alert_time = None
    previous_pair = None

    while True:
        try:
            meta_data = downloader.download_latest_photo(save_as="pre.jpg")
            log.info(f"{meta_data}")

            kakao_image_path = processor.crop_image(image_path="pre.jpg", output_path="kakako.jpg", crop_rect=KAKAO_CROP_AREA)
            switch_image_path = processor.crop_image(image_path="pre.jpg", output_path="switch.jpg", crop_rect=SWITCH_ONE_CROP_AREA)
            refresh_image_path = processor.crop_image(image_path="pre.jpg", output_path="refresh.jpg", crop_rect=REFRESH_CROP_AREA)
            kakao_text = ocr_reader.extract_text(image_path=kakao_image_path)
            switch_text = ocr_reader.extract_text(image_path=switch_image_path)
            refresh_text = ocr_reader.extract_text(image_path=refresh_image_path)
            
            log.info(f"카카오 추출 환율: {kakao_text}")
            log.info(f"스위치 추출 환율: {switch_text}")
            log.info(f"갱신 추출 환율: {refresh_text}")

            kakao = normalize_amount(kakao_text)
            switch_one = normalize_amount(switch_text)
            pair = ExchangeRatePair(switch_one=switch_one, kakao=kakao)                

            if previous_pair == pair:
                time.sleep(INTERVAL_SECONDS)
                continue

            log.info(f"{pair}")

            if (pair.is_switch_one_more_expensive()):
                noise_gap = pair.diff + NOISE_AMOUNT
                noise_switch_one = pair.switch_one + NOISE_AMOUNT
                message = f"갭 {noise_gap:.2f}원 (🔼 가능성)\n평균: {noise_switch_one:.2f}\n카뱅: {pair.kakao}\n({refresh_text})\n기준시각: '{meta_data.kst_creation_time()}'"

                telegram_client.send_message(message=message)
                last_rise_alert_time = datetime.datetime.now()
            else:
                now = datetime.datetime.now()
                if last_rise_alert_time is not None and now < last_rise_alert_time + datetime.timedelta(minutes=5):

                    noise_gap = pair.diff - NOISE_AMOUNT
                    noise_switch_one = pair.switch_one - NOISE_AMOUNT
                    if pair.diff > 0:
                        message = f"갭 {noise_gap:.2f}원 (갭이 작아졌습니다‼)\n평균: {noise_switch_one:.2f}\n카뱅: {pair.kakao}"
                    else:
                        message = f"갭 {noise_gap:.2f}원 (마이너스 갭‼‼)\n평균: {noise_switch_one:.2f}\n카뱅: {pair.kakao}"
                    telegram_client.send_message(message=message)

            previous_pair = pair
            telegram_monitoring_client.send_photo_group({
                switch_image_path : f"스원: {pair.switch_one:.2f} '{meta_data.kst_creation_time()}'",
                kakao_image_path : f"카뱅: {pair.kakao:.2f} '{meta_data.kst_creation_time()}'",
            })
        except Exception as e:
            log.exception(f"에러 발생: {e}")
            telegram_monitoring_client.send_message(message=f"에러 발생: {e}")
        time.sleep(INTERVAL_SECONDS)