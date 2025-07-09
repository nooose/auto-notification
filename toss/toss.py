import logging
from logging.handlers import TimedRotatingFileHandler

from core.config import Config
from core.exchange_rate_scraper import ExchangeRateScraper
from core.rate_change_notifier import RateChangeNotifier
from telegram_properties import TelegramProperties
from telegram_client import TelegramClient

def setup_logging():
    """파일 및 콘솔 로깅을 설정합니다."""
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_file = 'logs/rate_checker.log'
    
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
