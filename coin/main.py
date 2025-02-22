import time

from core.api.telegram_client import TelegramClient
from core.api.upbit_client import UpbitClient
from core.service.auto_trader import AutoTrader
from core.support.envrionment import Environment

INTERVAL = 0.1
COIN_MARKET = "KRW-XRP"
DEFAULT_VOLUME = "24"


def main():
    env = Environment()
    upbit_client = UpbitClient(market=COIN_MARKET, env=env)
    telegram_client = TelegramClient(env=env)
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
