import requests
from bs4 import BeautifulSoup
from typing import Tuple, Dict
from datetime import datetime
from zoneinfo import ZoneInfo
import re
import logging

from .exchange_rate import ExchangeRate, RateMeta

KST = ZoneInfo("Asia/Seoul")

class ExchangeRateScraper:
    """하나은행 웹사이트에서 환율 정보를 가져와 파싱합니다."""
    URL = "https://www.kebhana.com/cms/rate/wpfxd651_01i_01.do"
    HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}

    def fetch_rates(self) -> Tuple[RateMeta, Dict[str, ExchangeRate]]:
        """
        최신 환율 정보를 가져와 메타데이터와 환율 딕셔너리를 반환합니다.
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
            logging.error(f"HTML 가져오기 실패: {e}")
            raise

    def _parse_html(self, html_content: str) -> Tuple[RateMeta, Dict[str, ExchangeRate]]:
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 메타 데이터 추출
        meta_area = soup.find("p", class_="txtRateBox")
        publish_date = meta_area.find_all("strong")[0].get_text(strip=True)
        round_match = re.search(r"\((\d+)회차\)", meta_area.get_text())
        round_number = round_match.group(1) if round_match else "N/A"
        meta = RateMeta(publish_datetime=publish_date, round_number=round_number)

        # 환율 파싱
        table = soup.find("table", {"class": "tblBasic leftNone"})
        rows = table.find("tbody").find_all("tr")
        currency_to_exchange_rate = {}
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
                currency_to_exchange_rate[currency_code] = ExchangeRate(currency_code, base_rate, country_name)
            except (ValueError, IndexError):
                continue
        
        return meta, currency_to_exchange_rate
