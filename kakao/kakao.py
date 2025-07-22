import time
from photo_downloader import PhotoDownloader
from photo_processor import PhotoProcessor
from ocr import OCRReader
from rates import ExchangeRates, ExchangeRateError
import re
from telegram_properties import TelegramProperties
from telegram_client import TelegramClient
from envrionments import Environments
import argparse
from zoneinfo import ZoneInfo
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import os

from exchange_rate_fetcher import (
    GoogleFinanceFetcher,
    WooriBankFetcher,
    HanaBankFetcher
)

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
INTERVAL_SECONDS = 2
KAKAO_CROP_AREA = (120, 160, 250, 80)  # (x, y, width, height)
FRAME_FILE_NAME = "frame.jpg"

KST = ZoneInfo("Asia/Seoul")
AMOUNT_PATTERN = re.compile(r"\b(?:(?:\d{1,3}(?:[.,]\d{3})+)|\d+)(?:[.,]\d{2})\b")

class NormalizeAmountError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message

def normalize_amount(amount_text: str) -> float:
    match = AMOUNT_PATTERN.search(amount_text)
    if not match:
        raise NormalizeAmountError(f"유효한 금액 형식을 찾을 수 없습니다: '{amount_text}'")

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
    try:
        os.remove(FRAME_FILE_NAME)
    except FileNotFoundError:
        pass

    downloader = PhotoDownloader(Environments.get("STREAM_URL"))
    processor = PhotoProcessor()
    ocr_reader = OCRReader()

    google_fetcher = GoogleFinanceFetcher()
    woori_fetcher = WooriBankFetcher()
    hana_fetcher = HanaBankFetcher()

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

    alert_mode = "IDLE"
    previous_rates = None

    while True:
        try:
            downloader.download_latest_photo(path=FRAME_FILE_NAME)

            kakao_image_path = processor.crop_image(image_path=FRAME_FILE_NAME, output_path="kakako.jpg", crop_rect=KAKAO_CROP_AREA)
            kakao_text = ocr_reader.extract_text(image_path=kakao_image_path).strip()
            
            log.info(f"카카오 추출 환율: {kakao_text}")
            rates = ExchangeRates(
                kakao=normalize_amount(kakao_text), 
                google=google_fetcher.get_usd_rate(), 
                woori=woori_fetcher.get_usd_rate(), 
                hana=hana_fetcher.get_usd_rate()
            )                

            if previous_rates == rates:
                log.info("환율이 동일하여 생략합니다.")
                time.sleep(INTERVAL_SECONDS)
                continue

            log.info(f"{rates}")

            # 메인 알림 대기 상태
            if alert_mode == "IDLE":
                if rates.is_over_threshold() and previous_rates:
                    message = rates.format_alert_message()
                    telegram_client.send_message(message=message)
                    alert_mode = "WAITING_FOR_FOLLOWUP" # 후속 알림 대기 상태로 변경
            
            # 후속 알림 대기 상태
            elif alert_mode == "WAITING_FOR_FOLLOWUP":
                if previous_rates and rates.kakao != previous_rates.kakao:
                    kakao_diff = rates.kakao - previous_rates.kakao
                    status = "상승" if kakao_diff > 0 else "하락"
                    
                    message = f"카뱅 현재 환율: {rates.kakao:.2f}원 (약 {abs(kakao_diff):.2f}원 {status})"
                    telegram_client.send_message(message=message)
                    alert_mode = "IDLE" # 다시 메인 알림 대기 상태로 변경

            previous_rates = rates
            telegram_monitoring_client.send_photo_group({
                kakao_image_path : f"카뱅: {rates.kakao:.2f}\n구글: {rates.google:.2f}\n우리: {rates.woori:.2f}\n하나: {rates.hana:.2f}",
            })
        except ExchangeRateError as e:
            log.exception(f"환율 객체 생성 에러 발생: {e}")
        except NormalizeAmountError as e:
            log.exception(f"금액 포맷 에러 발생: {e}")
        except FileNotFoundError as e:
            log.exception(f"파일 에러 발생: {e}")
        except Exception as e:
            log.exception(f"에러 발생: {e}")
            telegram_monitoring_client.send_message(message=f"에러 발생: {e}")
        time.sleep(INTERVAL_SECONDS)
