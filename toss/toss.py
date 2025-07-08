import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import List, Tuple, Dict
from datetime import datetime
from zoneinfo import ZoneInfo
import re
import time
import logging
from logging.handlers import TimedRotatingFileHandler

from envrionments import Environments
from telegram_properties import TelegramProperties
from telegram_client import TelegramClient

# --- Constants and Global Config ---

KST = ZoneInfo("Asia/Seoul")
UP = "🔺"
DOWN = "🔽"
SAME = "➖"
INTERVAL_SECONDS = 2

# --- Data Classes ---

@dataclass(frozen=True)
class Config:
    """Holds all application configuration."""
    bot_token: str
    chat_id: str
    target_currencies: List[str]
    currency_display_names: Dict[str, str]
    outlier_thresholds: Dict[str, float]

    @classmethod
    def from_env(cls):
        """Loads configuration from environment variables."""
        target_currencies = ["USD", "HKD", "TWD", "THB", "SGD", "PHP", "MYR", "CHF"]
        currency_display_names = {
            "USD": "달러", "HKD": "달러", "TWD": "달러", "THB": "바트",
            "SGD": "달러", "PHP": "페소", "MYR": "링깃", "CHF": "프랑",
        }
        outlier_thresholds = {
            code: float(Environments.get(f"{code}_OUTLIER", 0))
            for code in currency_display_names if code != "USD"
        }
        return cls(
            bot_token=Environments.get("TELEGRAM_BOT_TOKEN"),
            chat_id=Environments.get("TELEGRAM_CHAT_ID"),
            target_currencies=target_currencies,
            currency_display_names=currency_display_names,
            outlier_thresholds=outlier_thresholds
        )

@dataclass(frozen=True)
class ExchangeRate:
    """Represents the exchange rate for a single currency."""
    currency_code: str
    base_rate: float
    country_name: str

@dataclass(frozen=True)
class RateMeta:
    """Metadata for a set of exchange rates."""
    publish_datetime: str
    round_number: str
    created_at: datetime = field(default_factory=lambda: datetime.now(KST))

# --- Core Components ---

class ExchangeRateScraper:
    """Fetches and parses exchange rate information from the Hana Bank website."""
    URL = "https://www.kebhana.com/cms/rate/wpfxd651_01i_01.do"
    HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}

    def fetch_rates(self) -> Tuple[RateMeta, Dict[str, ExchangeRate]]:
        """
        Fetches the latest exchange rates and returns metadata and a rate dictionary.
        """
        html_content = self._fetch_html()
        return self._parse_html(html_content)

    def _fetch_html(self) -> str:
        start_date = datetime.now(KST)
        data = {
            "ajax": "true", "curCd": "", "tmpInqStrDt": start_date.strftime("%Y-%m-%d"),
            "pbldDvCd": "3", "pbldSqn": "", "inqStrDt": start_date.strftime("%Y%m%d"),
            "inqKindCd": "1", "requestTarget": "searchContentDiv"
        }
        try:
            response = requests.post(self.URL, headers=self.HEADERS, data=data)
            response.raise_for_status()
            response.encoding = "utf-8"
            return response.text
        except requests.RequestException as e:
            logging.error(f"HTML fetching failed: {e}")
            raise

    def _parse_html(self, html_content: str) -> Tuple[RateMeta, Dict[str, ExchangeRate]]:
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Extract metadata
        meta_area = soup.find("p", class_="txtRateBox")
        publish_date = meta_area.find_all("strong")[0].get_text(strip=True)
        round_match = re.search(r"\((\d+)회차\)", meta_area.get_text())
        round_number = round_match.group(1) if round_match else "N/A"
        meta = RateMeta(publish_datetime=publish_date, round_number=round_number)

        # Parse exchange rates
        table = soup.find("table", {"class": "tblBasic leftNone"})
        rows = table.find("tbody").find_all("tr")
        exchange_rates = {}
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 9:
                continue
            
            full_currency = cols[0].get_text(strip=True)
            match = re.search(r"([\uAC00-\uD7A3\s]+)\s([A-Z]{3})", full_currency)
            if not match:
                continue
            
            country_name, currency_code = match.group(1).strip(), match.group(2)
            try:
                base_rate = float(cols[8].get_text(strip=True).replace(",", ""))
                exchange_rates[currency_code] = ExchangeRate(currency_code, base_rate, country_name)
            except (ValueError, IndexError):
                continue
        
        return meta, exchange_rates

class OutlierTracker:
    """Tracks which currencies are considered outliers and for how long."""
    def __init__(self, notification_period: int = 4):
        self._tracking: Dict[str, int] = {}
        self._notification_period = notification_period # This round + 3 more

    def get_currencies_to_notify(self) -> List[str]:
        """Returns a sorted list of currencies that require notification."""
        return sorted(list(self._tracking.keys()))

    def update(self, new_outliers: List[str]):
        """Updates tracking counters and adds new outliers."""
        # Decrement counters for all tracked items
        for code in list(self._tracking.keys()):
            self._tracking[code] -= 1
            if self._tracking[code] <= 0:
                logging.info(f"추적 기간 만료: {code}")
                del self._tracking[code]

        # Add or reset new outliers
        for code in new_outliers:
            if code not in self._tracking:
                logging.info(f"신규 아웃라이어 감지: {code}. {self._notification_period-1}회차 동안 추가 알림을 시작합니다.")
            self._tracking[code] = self._notification_period
        
        if self._tracking:
            logging.debug(f"현재 추적중인 통화: {self._tracking}")


class RateChangeNotifier:
    """The main application class that orchestrates the notification process."""
    def __init__(self, config: Config, scraper: ExchangeRateScraper, client: TelegramClient):
        self._config = config
        self._scraper = scraper
        self._client = client
        self._tracker = OutlierTracker()
        self._prev_rates: Dict[str, ExchangeRate] = {}
        self._prev_meta: RateMeta | None = None

    def run(self):
        """Starts the continuous monitoring and notification loop."""
        logging.info("초기 설정 완료, 환율 정보 확인 시작")
        while True:
            try:
                logging.info("="*50)
                logging.info("새 환율 정보 확인 시작")
                
                current_meta, current_rates = self._scraper.fetch_rates()
                logging.debug(f"{current_meta.publish_datetime} {current_meta.round_number}회차 정보 수신")

                if self._is_same_round(current_meta):
                    self._wait()
                    continue
                
                logging.info(f"새 회차({current_meta.round_number}) 정보 처리 시작")
                
                new_outliers = self._find_new_outliers(current_rates)
                self._tracker.update(new_outliers)
                
                currencies_to_notify = self._tracker.get_currencies_to_notify()
                
                if currencies_to_notify:
                    message = self._format_notification_message(current_meta, current_rates, currencies_to_notify)
                    logging.info(f"알림 보낼 통화 {len(currencies_to_notify)}건. 텔레그램 메시지를 전송합니다.")
                    self._client.send_message(message)
                else:
                    logging.info("알림 보낼 통화가 없습니다.")

                self._update_state(current_meta, current_rates)
                self._wait()

            except Exception as e:
                logging.error(f"예상치 못한 오류가 발생했습니다: {e}", exc_info=True)
                self._wait()

    def _is_same_round(self, current_meta: RateMeta) -> bool:
        if self._prev_meta and current_meta.round_number == self._prev_meta.round_number:
            logging.debug(f"이전과 동일한 회차({current_meta.round_number})이므로 건너뜁니다.")
            return True
        return False

    def _find_new_outliers(self, current_rates: Dict[str, ExchangeRate]) -> List[str]:
        new_outliers = []
        if not self._prev_rates:
            return []

        for code in self._config.target_currencies:
            current = current_rates.get(code)
            previous = self._prev_rates.get(code)
            threshold = self._config.outlier_thresholds.get(code)

            if not all([current, previous, threshold is not None]):
                continue

            diff = abs(round(current.base_rate - previous.base_rate, 2))
            logging.debug(f"{code}: 현재 {current.base_rate}, 이전 {previous.base_rate}, 차액 {diff:.2f}, 임계값 {threshold}")
            
            if diff >= threshold:
                new_outliers.append(code)
        
        return new_outliers

    def _format_notification_message(self, meta: RateMeta, rates: Dict[str, ExchangeRate], codes: List[str]) -> str:
        header = f"{meta.publish_datetime} {meta.created_at.strftime('%H:%M:%S')}-{meta.round_number}회차"
        lines = [header]
        
        for code in codes:
            current = rates.get(code)
            previous = self._prev_rates.get(code)
            
            if not current or not previous: continue

            diff = round(current.base_rate - previous.base_rate, 2)
            emoji = UP if diff > 0 else (DOWN if diff < 0 else SAME)
            
            display_name = self._config.currency_display_names.get(code, "통화")
            line = f"{current.country_name} {display_name}: {current.base_rate:.2f} ({emoji} {abs(diff):.2f})"
            lines.append(line)
        
        return "\n\n".join(lines)

    def _update_state(self, meta: RateMeta, rates: Dict[str, ExchangeRate]):
        self._prev_meta = meta
        self._prev_rates = rates
        logging.info("이전 환율 정보를 현재 정보로 업데이트했습니다.")

    def _wait(self):
        logging.info(f"다음 확인까지 {INTERVAL_SECONDS}초 대기합니다.")
        time.sleep(INTERVAL_SECONDS)

def setup_logging():
    """Configures logging to file and console."""
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_file = 'rate_checker.log'
    
    file_handler = TimedRotatingFileHandler(log_file, when='D', interval=3, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)
    
    logger = logging.getLogger()
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

if __name__ == "__main__":
    setup_logging()
    
    try:
        config = Config.from_env()
        logging.debug(f"설정 로드 완료: {config}")
        
        telegram_properties = TelegramProperties(bot_token=config.bot_token, chat_id=config.chat_id)
        telegram_client = TelegramClient(properties=telegram_properties)
        
        scraper = ExchangeRateScraper()
        
        notifier = RateChangeNotifier(
            config=config,
            scraper=scraper,
            client=telegram_client
        )
        
        notifier.run()
        
    except Exception as e:
        logging.critical(f"프로그램 시작에 실패했습니다: {e}", exc_info=True)