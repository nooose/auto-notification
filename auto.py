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

load_dotenv()

handler = TimedRotatingFileHandler(
    'output.log', when='midnight', interval=1, backupCount=7, encoding='utf-8'
)
logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)


def fetch_vnd_exchange_rate():

    url = "https://www.kebhana.com/cms/rate/wpfxd651_01i_01.do?tmpInqStrDt=2023-03-25&pbldDvCd=3&inqStrDt=20230325&inqKindCd=1"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        table_rows = soup.select('tbody tr')

        for row in table_rows:
            cells = [cell.get_text(strip=True) for cell in row.find_all('td')]

            if 'VND' in cells[0]:
                exchange_rate = float(cells[8].replace(
                    ",", ""))
                return exchange_rate
    else:
        logging.error(
            f"Failed to fetch the webpage. Status code: {response.status_code}")
        return None


def calculate_seconds_to_next_minute_20():
    now = datetime.now()
    seconds_to_next_20 = (60 - now.second) + 20
    if now.second <= 20:
        seconds_to_next_20 = 20 - now.second
    return seconds_to_next_20


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            pass
        else:
            pass
    except Exception as e:
        logging.error(e)


previous_rate = None

try:
    while True:
        current_rate = fetch_vnd_exchange_rate()
        now = datetime.now()
        seconds_to_next_20 = calculate_seconds_to_next_minute_20()
        if current_rate is not None:
            if previous_rate is not None:
                diff = current_rate - previous_rate
                # logging.info(f"current_rate:{current_rate}, previous_rate:{previous_rate}")
                if round(abs(diff), 2) >= 0.01:
                    emoji = "🔺" if diff >= 0 else "🔽"
                    message = (f"토스: {current_rate + 0.00:.2f} {emoji}({round(abs(diff), 2)}원)\n"
                               f"'{seconds_to_next_20}초' {now.strftime('%H:%M:%S')}")
                    logging.info(f"send_message: {message}")
                    send_telegram_message(message)
            previous_rate = current_rate
        else:
            logging.error("Failed to retrieve exchange rate.")

        time.sleep(5)
except KeyboardInterrupt:
    print("exit")
