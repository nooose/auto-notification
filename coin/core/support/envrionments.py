import os
import sys
from pathlib import Path
from dotenv import load_dotenv


class Environments:
    """환경 변수를 가져오는 유틸리티 클래스"""

    _env_loaded = False

    @staticmethod
    def _load_env(env_path=None):
        """환경 변수를 로드하는 메서드"""
        if not env_path:
            env_path = Path.cwd() / '.env'

        if not env_path.exists():
            raise FileNotFoundError(f"{env_path} 파일을 찾을 수 없습니다.")

        load_dotenv(env_path)

    @staticmethod
    def get(key, default=None) -> str:
        """환경 변수를 가져온다."""

        if not Environments._env_loaded:
            try:
                Environments._load_env()
                Environments._env_loaded = True
            except FileNotFoundError as e:
                print(f"에러: {e}")
                sys.exit(1)

        return os.getenv(key, default)
