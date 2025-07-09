from typing import List, Dict
import logging

class OutlierTracker:
    """어떤 통화가 이상치로 간주되는지, 그리고 얼마나 오랫동안 이상치였는지 추적합니다."""
    def __init__(self, notification_period: int = 4):
        self._tracking: Dict[str, int] = {}
        self._notification_period = notification_period

    def get_currencies_to_notify(self) -> List[str]:
        """알림이 필요한 통화의 정렬된 목록을 반환합니다."""
        return sorted(list(self._tracking.keys()))

    def update(self, new_outliers: List[str]):
        """추적 카운터를 업데이트하고 새로운 이상치를 추가합니다."""
        for code in list(self._tracking.keys()):
            self._tracking[code] -= 1
            if self._tracking[code] <= 0:
                logging.info(f"추적 종료: {code}")
                del self._tracking[code]

        for code in new_outliers:
            if code not in self._tracking:
                logging.info(f"신규 아웃라이어 감지: {code}. {self._notification_period-1}회차 동안 추가 알림을 시작합니다.")
            self._tracking[code] = self._notification_period
        
        if self._tracking:
            logging.debug(f"현재 추적중인 통화: {self._tracking}")
