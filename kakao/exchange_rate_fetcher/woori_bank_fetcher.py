import requests
from bs4 import BeautifulSoup
from .exchange_rate_fetcher import ExchangeRateFetcher
import datetime

class WooriBankFetcher(ExchangeRateFetcher):
    def get_usd_rate(self) -> float:
        url = "https://svc.wooribank.com/svc/jcc?withyou=CMCOM0184&__ID=c012238"
        today = datetime.datetime.now().strftime('%Y%m%d')
        payload = {'p_date': today}

        try:
            response = requests.post(url, data=payload)
            response.raise_for_status()  # HTTP 오류가 발생하면 예외를 발생시킵니다.
            soup = BeautifulSoup(response.content, 'html.parser')

            # '미국 달러' 텍스트를 포함하는 <td> 요소를 찾습니다.
            usd_td = soup.find('td', string='미국 달러')
            if not usd_td:
                raise ValueError("USD exchange rate not found on the page.")

            # <td> 요소의 부모 <tr>을 찾습니다.
            usd_row = usd_td.find_parent('tr')
            if not usd_row:
                raise ValueError("Could not find the table row for USD rate.")

            # 해당 행의 모든 <td>를 가져옵니다. 매매기준율은 9번째(인덱스 8)에 있습니다.
            columns = usd_row.find_all('td')
            if len(columns) > 8:
                rate_text = columns[8].get_text(strip=True)
                # 쉼표를 제거하고 float으로 변환합니다.
                return float(rate_text.replace(',', ''))
            else:
                raise ValueError("USD base rate column not found in the row.")
        except requests.RequestException as e:
            print(f"Error fetching data from Woori Bank: {e}")
            return 0.0
        except (ValueError, AttributeError) as e:
            print(f"Error parsing Woori Bank exchange rate: {e}")
            return 0.0