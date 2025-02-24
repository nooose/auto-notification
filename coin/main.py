import time
import traceback
import os
import logging
from logging.handlers import TimedRotatingFileHandler

from core.api.telegram_client import TelegramClient
from core.api.telegram_properties import TelegramProperties
from core.api.upbit_client import UpbitClient
from core.api.upbit_properties import UpbitProperties
from core.service.auto_trader import AutoTrader
from core.service.trade_strategy import TradeStrategy
from core.support.envrionments import Environments

INTERVAL = 0.1
COIN_MARKET = "KRW-XRP"
DEFAULT_MARGIN = 8.0
DEFAULT_VOLUME = "2"

DEBUG = False

def main():
    upbit_properties = UpbitProperties(
        access_key=Environments.get("UPBIT_ACCESS_KEY"),
        secret_key=Environments.get("UPBIT_SECRET_KEY"),
    )
    upbit_client = UpbitClient(market=COIN_MARKET, properties=upbit_properties)

    telegram_properties = TelegramProperties(
        bot_token=Environments.get("TELEGRAM_BOT_TOKEN"),
        chat_id=Environments.get("TELEGRAM_CHAT_ID"),
    )
    telegram_client = TelegramClient(properties=telegram_properties)

    strategy = TradeStrategy(margin=DEFAULT_MARGIN)
    trader = AutoTrader(
        margin=DEFAULT_MARGIN,
        volume=DEFAULT_VOLUME,
        strategy=strategy,
        upbit_client=upbit_client,
        telegram_client=telegram_client,
    )

    while not DEBUG:
        try:
            trader.trading()
        except Exception as e:
            print(f"에러: {e}")
            live_candle = upbit_client.get_recent_candles(1)[0]
            trader.sell_completed(live_candle)
            traceback.print_exc()
            telegram_client.async_send_message(f"에러 발생 - {e}")
        time.sleep(INTERVAL)

def _setup_logger():
    """로깅 설정
    """

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    os.makedirs(LOG_DIR, exist_ok=True)

    log_file = os.path.join(LOG_DIR, "output.log")

    handler = TimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=7, encoding="utf-8"
    )

    logging.basicConfig(
        handlers=[handler],
        level=logging.INFO,
        format="%(asctime)s - %(message)s"
    )


if __name__ == "__main__":
    _setup_logger()
    main()
