import jwt
import hashlib
import requests
import uuid
from urllib.parse import urlencode, unquote
from typing import Dict, List

from core.api.upbit_properties import UpbitProperties
from core.data.account import Account
from core.data.candle import Candle
from core.data.trade_states import OrderState


def make_query_hash(params: Dict) -> str:
    """업비트 API 요청에 사용되는 query_hash를 생성한다.

    :param params: 요청 파라미터
    :return: query_hash 값
    """

    query_string = unquote(urlencode(params, doseq=True)).encode("utf-8")
    message = hashlib.sha512()
    message.update(query_string)
    return message.hexdigest()


class UpbitClient:
    """업비트 API 클라이언트

    업비트 공식 문서 참고:
    https://docs.upbit.com/reference
    """

    def __init__(self, market: str, properties: UpbitProperties):
        """UpbitClient 객체를 생성한다.

        :param market: 클라이언트가 다룰 코인 이름
        :param properties: 업비트 프로퍼티
        """

        self.API_ENDPOINT = 'https://api.upbit.com'
        self.access_key = properties.access_key
        self.secret_key = properties.secret_key
        self.market = market

    def get_recent_candles(self, count: int) -> List[Candle]:
        """실시간 5분봉 목록을 가져온다.

        :param count: 가져올 캔들 수
        :return: 캔들 목록
        """

        url = self.API_ENDPOINT + '/v1/candles/minutes/5'
        params = {
            'market': self.market,
            'count': count,
        }
        headers = {"accept": "application/json"}

        response = requests.get(url, params=params, headers=headers).json()
        return [Candle.from_response(data) for data in response]

    def place_buy_order(self, volume: str) -> str:
        """매수 주문을 한다.

        :param volume: 주문 수량
        :return: 주문 UUID
        """

        url = self.API_ENDPOINT + '/v1/orders'

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

        response = requests.post(url, json=params, headers=headers)
        return response.json()["uuid"]

    def place_sell_order(self, volume: str) -> str:
        """매도 주문을 한다.

        :param volume: 주문 수량
        :return: 주문 UUID
        """

        url = self.API_ENDPOINT + '/v1/orders'

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

        response = requests.post(url, json=params, headers=headers)
        return response.json()["uuid"]

    def get_my_account(self) -> List[Account]:
        """내 계좌 정보를 가져온다.

        :return: 계좌 정보 목록
        """
        url = self.API_ENDPOINT + '/v1/accounts'

        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
        }

        jwt_token = jwt.encode(payload, self.secret_key)
        authorization = 'Bearer {}'.format(jwt_token)
        headers = {
            'Authorization': authorization,
        }

        response = requests.get(url, headers=headers)
        accounts = response.json()
        return [Account.from_response(data) for data in accounts]

    def get_order(self, request_uuid: str) -> OrderState:
        """주문 정보를 가져온다.

        :param request_uuid: 주문 UUID
        :return: 주문 상태
        """
        url = self.API_ENDPOINT + '/v1/accounts/v1/order'

        params = {
            'uuid': [request_uuid]
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

        response = requests.get(url, params=params, headers=headers)
        state = response.json()["state"]
        return OrderState.value_of(state)

    def cancel_and_sell_order(self, cancel_uuid: str, new_price: str) -> str:
        """주문을 취소하고, 매도 주문을 새로 한다.

        :param cancel_uuid: 취소할 주문 UUID
        :param new_price: 매도할 가격
        :return: 새주문 UUID
        """
        url = self.API_ENDPOINT + '/v1/orders/cancel_and_new'

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

        response = requests.post(url, json=params, headers=headers)
        return response.json()["uuid"]

    def cancel_order(self, request_uuid: str):
        """주문을 취소한다.

        :param request_uuid: 주문 UUID
        """

        url = self.API_ENDPOINT + '/v1/order'

        params = {
            'uuid': request_uuid
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

        response = requests.delete(url, params=params, headers=headers)
        response.json()
