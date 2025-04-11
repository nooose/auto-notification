import time
from google_photo_downloader import PhotoDownloader
from photo_processor import PhotoProcessor
from ocr import OCRReader
from data import ExchangeRatePair
import re
from telegram_properties import TelegramProperties
from telegram_client import TelegramClient
from envrionments import Environments

DEBUG = False

def toPair(text: str) -> ExchangeRatePair:
    if DEBUG:
        print(f"추출 텍스트: {text}")

    amounts = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)+', text)
    print(f"추출된 금액: {amounts}")

    filtered_amounts = []        
    for amount in amounts:
        cleaned = normalize_amount(amount)
        print(f"{amount} -> {cleaned}")
        if 1300 <= cleaned <= 1600:
            filtered_amounts.append(cleaned)

    print(f"필터링된 금액: {filtered_amounts}")
    if len(filtered_amounts) < 2:
        raise ValueError("환율 정보를 파싱할 수 없습니다.")

    kakao = filtered_amounts[0]
    switch_one = filtered_amounts[-1]
    return ExchangeRatePair(switch_one=switch_one, kakao=kakao)

def fix_amount(amount: str) -> str:
    parts = amount.split('.')
    
    if len(parts) >= 3 and parts[0] == '1':
        # "1.234.56" -> "1,234.56"
        return f"1,{parts[1]}.{parts[2]}"
    
    if len(parts) >= 3 and parts[0] == '11':
        # "11.449.96" -> "1,449.96"
        return f"1,{parts[1]}.{parts[2]}"    
    
    return amount

def normalize_amount(amount: str) -> float:
    fixed = fix_amount(amount)
    cleaned = fixed.replace(',', '')
    if (float(cleaned) > 10000):
        return round(float(cleaned - 10000), 2)
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

    previous_pair = None

    while True:
        try:
            downloader.download_latest_photo(save_as="pre.jpg")
            # processor.preprocess_image(image_path="pre.jpg", output_path="post.jpg")
            rates_text = ocr_reader.extract_text(image_path="pre.jpg")
            pair = toPair(rates_text)

            if previous_pair == pair:
                time.sleep(10)
                continue

            if DEBUG:
                print(f"환율 정보: {pair}")
            if (pair.is_switch_one_more_expensive()):
                message = f"갭 {pair.diff():.2f}원\n기준: {pair.switch_one}\n카뱅: {pair.kakao}"
                telegram_client.send_message(message=message)
            previous_pair = pair
        except Exception as e:
            print(f"오류 발생: {e}")
        time.sleep(10)