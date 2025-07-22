
import requests
from bs4 import BeautifulSoup
from .exchange_rate_fetcher import ExchangeRateFetcher

class GoogleFinanceFetcher(ExchangeRateFetcher):
    def get_usd_rate(self) -> float:
        url = "https://www.google.com/finance/quote/USD-KRW"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        result = soup.find("div", {"class": "YMlKec fxKbKc"}).text
        return float(result.replace(",", ""))
