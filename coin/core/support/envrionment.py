from dotenv import load_dotenv
import os
from pathlib import Path


class Environment:
    """환경 변수를 가져오는 클래스
    """

    def __init__(self):
        """.env 파일로 부터 환경 변수를 로드한다.
        """

        env_path = Path.cwd() / '.env'
        load_dotenv(env_path)

    @staticmethod
    def get(key, default=None) -> str:
        """환경 변수를 가져온다.

        Args:
            key (str): 환경 변수 키
            default (str): 기본값

        Returns:
            str: 환경 변수 값
        """
        return os.getenv(key, default)
