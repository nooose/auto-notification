from dataclasses import dataclass


@dataclass
class UpbitProperties:
    """업비트 프로퍼티
    """

    access_key: str
    secret_key: str
