import requests
from bs4 import BeautifulSoup
from .exchange_rate_fetcher import ExchangeRateFetcher
import re

class HanaBankFetcher(ExchangeRateFetcher):
    def get_usd_rate(self) -> float:
        url = "https://www.kebhana.com/cms/rate/wpfxd651_01i_01.do?pbldDvCd=3&inqKindCd=1"
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            usd_element = soup.find(string=re.compile(r'미국\s+USD'))
            if not usd_element:
                raise ValueError("USD exchange rate not found on the page.")

            # 해당 요소의 부모 <tr>을 찾습니다.
            usd_row = usd_element.find_parent('tr')
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
            print(f"Error fetching data from Hana Bank: {e}")
            return 0.0
        except (ValueError, AttributeError) as e:
            print(f"Error parsing Hana Bank exchange rate: {e}")
            return 0.0