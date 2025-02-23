import os
import sys
from pathlib import Path
from dotenv import load_dotenv


class Environments:
    """환경 변수를 가져오는 유틸리티 클래스"""

    _env_loaded = False

    @staticmethod
    def _load_env(env_path=None):
        """환경 변수를 불러온다.

        :param env_path: ``.env`` 파일 경로
        :raise FileNotFoundError: ``.env`` 파일이 없으면 발생할 수 있다.
        """
        if not env_path:
            env_path = Path.cwd() / '.env'

        if not env_path.exists():
            raise FileNotFoundError(f"{env_path} 파일을 찾을 수 없습니다.")

        load_dotenv(env_path)

    @staticmethod
    def get(key, default=None) -> str:
        """환경 변수 값을 불러온다.

        :param key: 환경변수 키
        :param default: 키가 존재하지 않을 때 기본 값
        :return: 환경변수 값
        :raise SystemExit: 환경변수를 불러오지 못하면 발생할 수 있다.
        """

        if not Environments._env_loaded:
            try:
                Environments._load_env()
                Environments._env_loaded = True
            except FileNotFoundError as e:
                print(f"에러: {e}")
                sys.exit(1)

        return os.getenv(key, default)
