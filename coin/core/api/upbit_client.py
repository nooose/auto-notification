import jwt
import hashlib
import requests
import uuid
from urllib.parse import urlencode, unquote
from typing import Dict, List

from core.data.account import Account
from core.data.candle import Candle
from core.data.trade_states import OrderState
from core.support.envrionment import Environment

API_ENDPOINT = 'https://api.upbit.com'


def make_query_hash(params: Dict) -> str:
    """업비트 API 요청에 사용되는 query_hash를 생성한다.

    Args:
        params (Dict): 요청 파라미터

    Returns:
        str: query_hash
    """

    query_string = unquote(urlencode(params, doseq=True)).encode("utf-8")
    message = hashlib.sha512()
    message.update(query_string)
    return message.hexdigest()


class UpbitClient:
    """업비트 API 클라이언트
    - https://docs.upbit.com/ 참고
    """

    market: str
    env: Environment

    def __init__(self, market: str, env: Environment):
        """UpbitClient 객체를 생성한다.
        
        Args:
            market (str): 클라이언트에서 다룰 코인
            env (Environment): 환경 변수 객체
        """

        self.market: str = market
        self.access_key: str = env.get("UPBIT_ACCESS_KEY")
        self.secret_key: str = env.get("UPBIT_SECRET_KEY")

    def get_recent_candles(self, count: int) -> List[Candle]:
        """실시간 5분봉 캔들 목록을 가져온다.
        
        Args:
            count (int): 가져올 캔들 개수

        Returns:
            List[Candle]: 캔들 목록
        """

        url = API_ENDPOINT + '/v1/candles/minutes/5'
        params = {
            'market': self.market,
            'count': count,
        }
        headers = {"accept": "application/json"}

        response = requests.get(url, params=params, headers=headers).json()
        return [Candle.from_response(data) for data in response]

    def place_buy_order(self, volume: str) -> str:
        """매수 주문을 실행한다.

        Args:
            volume (str): 주문 수량
        
        Returns:
            str: 주문 UUID
        """

        # TODO: volume 으로 구매할 때 지정가(limit)이 아닌 시장가 주문(price)으로 해야하는지?
        params = {
            'market': self.market,
            'side': 'bid',
            'ord_type': 'limit',
            'volume': volume,
        }

        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': make_query_hash(params),
            'query_hash_alg': 'SHA512',
        }

        jwt_token = jwt.encode(payload, self.secret_key)
        authorization = 'Bearer {}'.format(jwt_token)
        headers = {
            'Authorization': authorization,
        }

        response = requests.post(API_ENDPOINT + '/v1/orders', json=params, headers=headers)
        return response.json()["uuid"]

    def place_sell_order(self, volume: str) -> str:
        """매도 주문을 실행한다.

        Args:
            volume (str): 주문 수량

        Returns:
            str : 주문 UUID
        """

        params = {
            'market': self.market,
            'side': 'ask',
            'ord_type': 'limit',
            'volume': volume,
        }

        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': make_query_hash(params),
            'query_hash_alg': 'SHA512',
        }

        jwt_token = jwt.encode(payload, self.secret_key)
        authorization = 'Bearer {}'.format(jwt_token)
        headers = {
            'Authorization': authorization,
        }

        response = requests.post(API_ENDPOINT + '/v1/orders', json=params, headers=headers)
        return response.json()["uuid"]

    def get_my_account(self) -> List[Account]:
        """내 계좌 정보를 가져온다.
        
        Returns:
            List[Account]: 내 계좌 정보
        """

        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
        }

        jwt_token = jwt.encode(payload, self.secret_key)
        authorization = 'Bearer {}'.format(jwt_token)
        headers = {
            'Authorization': authorization,
        }

        response = requests.get(API_ENDPOINT + '/v1/accounts', headers=headers)
        accounts = response.json()
        return [Account.from_response(data) for data in accounts]

    def get_order(self, find_uuid: str) -> OrderState:
        """주문 정보를 가져온다.

        Args:
            find_uuid (str): 주문 UUID
        
        Returns:
            str: 주문 상태('wait', 'done')
        """

        params = {
            'uuid': [find_uuid]
        }

        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': make_query_hash(params),
            'query_hash_alg': 'SHA512',
        }

        jwt_token = jwt.encode(payload, self.secret_key)
        authorization = 'Bearer {}'.format(jwt_token)
        headers = {
            'Authorization': authorization,
        }

        response = requests.get(API_ENDPOINT + '/v1/accounts/v1/order', params=params, headers=headers)
        state = response.json()["state"]
        return OrderState.value_of(state)

    def cancel_and_sell_order(self, cancel_uuid: str, new_price: str):
        """기존 주문을 취소하고, 새로운 주문을 실행한다.
        
        Args:
            cancel_uuid (str): 취소할 주문 UUID
            new_price (str): 새로운 주문 가격
        """

        params = {
            'prev_order_uuid': cancel_uuid,
            'new_ord_type': 'limit',
            'new_price': new_price,
            'new_volume': 'remain_only',
        }

        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': make_query_hash(params),
            'query_hash_alg': 'SHA512',
        }

        jwt_token = jwt.encode(payload, self.secret_key)
        authorization = 'Bearer {}'.format(jwt_token)
        headers = {
            'Authorization': authorization,
        }

        response = requests.post(API_ENDPOINT + '/v1/orders/cancel_and_new', json=params, headers=headers)
        return response.json()["uuid"]
