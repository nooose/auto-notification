import time

from core.api.upbit_client import UpbitClient
from core.service.trader import Trader
from core.support.envrionment import Environment

INTERVAL = 0.1
COIN_MARKET = "KRW-XRP"
DEFAULT_VOLUME = "24"


def main():
    env = Environment()
    client = UpbitClient(market=COIN_MARKET, env=env)
    trader = Trader(DEFAULT_VOLUME, client)

    # TODO: 예외 발생 시 예외 로직 처리
    while True:
        try:
            trader.start_trading()
        except Exception as e:
            print(f"에러: {e}")

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
