from typing import List, Dict
import logging
import time

from .config import Config
from .exchange_rate import ExchangeRate, RateMeta
from .exchange_rate_scraper import ExchangeRateScraper
from .outlier_tracker import OutlierTracker
from telegram_client import TelegramClient

# --- Constants ---
UP = "🔺"
DOWN = "🔽"
SAME = "➖"
INTERVAL_SECONDS = 2

class RateChangeNotifier:
    """알림 프로세스를 조정하는 메인 애플리케이션 클래스입니다."""
    def __init__(self, config: Config, scraper: ExchangeRateScraper, client: TelegramClient):
        self._config = config
        self._scraper = scraper
        self._client = client
        self._tracker = OutlierTracker()
        self._currency_code_to_prev_rate: Dict[str, ExchangeRate] = {}
        self._prev_meta: RateMeta | None = None
        self._profit_per_0_01 = {
            'CNY': 526, 'HKD': 270, 'TWD': 1090, 'THB': 1100, 'SGD': 46,
            'PHP': 2000, 'MYR': 50
        }

    def run(self):
        """지속적인 모니터링 및 알림 루프를 시작합니다."""
        logging.info("초기 설정 완료, 환율 정보 확인 시작")
        while True:
            try:
                logging.info("="*50)
                logging.info("새 환율 정보 확인 시작")
                
                current_meta, currency_to_current_rate = self._scraper.fetch_rates()
                logging.debug(f"{current_meta.publish_datetime} {current_meta.round_number}회차 정보 수신")

                if self._is_same_round(current_meta):
                    self._wait()
                    continue
                
                logging.info(f"새 회차({current_meta.round_number}) 정보 처리 시작")
                
                new_outliers = self._find_new_outliers(currency_to_current_rate)
                self._tracker.update(new_outliers)
                
                currencies_to_notify = self._tracker.get_currencies_to_notify()
                
                if currencies_to_notify:
                    message_prefix = "[⚠️ 감시]"
                    is_bold = False
                    if new_outliers:
                        message_prefix = "[💸 아웃라이어]"
                        is_bold = True
                    message = self._format_notification_message(
                        current_meta, 
                        currency_to_current_rate, 
                        currencies_to_notify, 
                        message_prefix, 
                        is_prefix_bold=is_bold
                    )
                    logging.info(f"알림 보낼 통화 {len(currencies_to_notify)}건. 텔레그램 메시지를 전송합니다.")
                    self._client.send_message(message)
                else:
                    logging.info("알림 보낼 통화가 없습니다.")

                self._update_state(current_meta, currency_to_current_rate)
                self._wait()

            except Exception as e:
                logging.error(f"예상치 못한 오류가 발생했습니다: {e}", exc_info=True)
                self._wait()

    def _is_same_round(self, current_meta: RateMeta) -> bool:
        if self._prev_meta and current_meta.round_number == self._prev_meta.round_number:
            logging.debug(f"이전과 동일한 회차({current_meta.round_number})이므로 건너뜁니다.")
            return True
        return False

    def _find_new_outliers(self, currency_to_current_rate: Dict[str, ExchangeRate]) -> List[str]:
        new_outliers = []
        if not self._currency_code_to_prev_rate:
            return []

        for code in self._config.target_currencies:
            current = currency_to_current_rate.get(code)
            previous = self._currency_code_to_prev_rate.get(code)
            threshold = self._config.currency_code_to_outlier_threshold.get(code)

            if not all([current, previous, threshold is not None]):
                continue

            diff = round(current.base_rate - previous.base_rate, 2)
            logging.debug(f"{code}: 현재 {current.base_rate}, 이전 {previous.base_rate}, 차액 {diff:.2f}, 임계값 {threshold}")
            
            if diff >= threshold:
                new_outliers.append(code)
        
        return new_outliers

    def _format_notification_message(
        self, 
        meta: RateMeta, 
        currency_to_exchange_rate: Dict[str, ExchangeRate], 
        codes: List[str], 
        prefix: str, 
        is_prefix_bold: bool = False
    ) -> str:
        if is_prefix_bold:
            lines = [f"*{prefix}*"]
        else:
            lines = [prefix]
        
        for code in codes:
            current = currency_to_exchange_rate.get(code)
            previous = self._currency_code_to_prev_rate.get(code)
            
            if not current or not previous: continue

            diff = round(current.base_rate - previous.base_rate, 2)
            emoji = UP if diff > 0 else (DOWN if diff < 0 else SAME)
            
            display_name = self._config.currency_code_to_display_name.get(code, "통화")
            line = f"{current.country_name} {display_name}: {current.base_rate:.2f} ({emoji} {diff:.2f})"
            
            profit = diff * 100 * self._profit_per_0_01.get(code, 0)
            if profit != 0:
                line += f"\n💸: 약 {profit:,.0f}원"

            lines.append(line)
        
        header = f"{meta.created_at.strftime('%H:%M:%S')}-{meta.round_number}회차"
        lines.append(header)
        
        return "\n\n".join(lines)

    def _update_state(self, meta: RateMeta, currency_to_exchange_rate: Dict[str, ExchangeRate]):
        self._prev_meta = meta
        self._currency_code_to_prev_rate = currency_to_exchange_rate
        logging.info("이전 환율 정보를 현재 정보로 업데이트했습니다.")

    def _wait(self):
        logging.info(f"다음 확인까지 {INTERVAL_SECONDS}초 대기합니다.")
        time.sleep(INTERVAL_SECONDS)