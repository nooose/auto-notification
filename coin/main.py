import time

from core.api.telegram_client import TelegramClient
from core.api.telegram_properties import TelegramProperties
from core.api.upbit_client import UpbitClient
from core.api.upbit_properties import UpbitProperties
from core.service.auto_trader import AutoTrader
from core.support.envrionments import Environments

INTERVAL = 0.1
COIN_MARKET = "KRW-XRP"
DEFAULT_VOLUME = "24"


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

    trader = AutoTrader(DEFAULT_VOLUME, upbit_client, telegram_client)

    # TODO: 예외 발생 시 예외 로직 처리
    while True:
        try:
            trader.start_trading()
        except Exception as e:
            print(f"에러: {e}")

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
