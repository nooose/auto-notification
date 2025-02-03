# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import telegram
import logging
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv
import os

handler = TimedRotatingFileHandler(
    'output.log', when='midnight', interval=1, backupCount=7, encoding='utf-8'
)

logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

load_dotenv()

FETCH_VND_URL = "https://www.kebhana.com/cms/rate/wpfxd651_01i_01.do?pbldDvCd=3&inqKindCd=1"
FETCH_INTERVAL = 5
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

def fetch_vnd_exchange_rate():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(FETCH_VND_URL, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch the webpage: {e}")
        return None

    return extract_vnd_rate_from_html(response.text)

def extract_vnd_rate_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.select('tbody tr')

    vnd_row = next((row for row in rows if 'PHP' in row.get_text()), None)
    if not vnd_row:
        logging.error("No PHP data found in the table.")
        return None

    try:
        cells = [cell.get_text(strip=True) for cell in vnd_row.find_all('td')]
        exchange_rate = float(cells[8].replace(",", ""))
        return exchange_rate
    except (IndexError, ValueError) as e:
        logging.error(f"Error parsing exchange rate: {e}")
        return None

def calculate_seconds_to_next_minute(now, target_second):
    if now.second <= target_second:
        return target_second - now.second
    else:
        return 60 - now.second + target_second

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        logging.info(f"Message sent successfully: {message}")
    except requests.RequestException as e:
        logging.error(f"Failed to send Telegram message: {e}")

def get_emoji_for_time(next_seconds):
    if next_seconds <= 10:
        return "🟥"
    elif next_seconds <= 20:
        return "🟧"
    elif next_seconds <= 30:
        return "🟨"
    elif next_seconds <= 40:
        return "🟩"
    else:
        return "🟦"

# main
previous_rate = None

try:
    while True:
        current_rate = fetch_vnd_exchange_rate()
        now = datetime.now()
        next_seconds = calculate_seconds_to_next_minute(now, 20)

        if current_rate is None:
            logging.error("Failed to retrieve exchange rate.")
            continue

        if previous_rate is not None:
            diff = current_rate - previous_rate
            if round(abs(diff), 2) >= 0.00: # 변동 발생
                emoji = "🔺" if diff >= 0 else "🔽"
                message = (f"{previous_rate:.2f} → {current_rate:.2f} {emoji}({round(abs(diff), 2)}원)\n"
                f"다음 반영까지 **'{next_seconds}'초** {get_emoji_for_time(next_seconds)}\n"
                f"현재 시각: {now.strftime('%H:%M:%S')}")
                logging.info(f"send_message: {message}")
                send_telegram_message(message)
        previous_rate = current_rate
        time.sleep(FETCH_INTERVAL)
except KeyboardInterrupt:
    print("exit")
