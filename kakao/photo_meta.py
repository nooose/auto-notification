from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
    
KST = timezone(timedelta(hours=9))

@dataclass
class PhotoMeta:
    creation_time_utc: datetime
    file_name: str
    kst_creation_time_from_name: str = field(init=False)

    def __post_init__(self):
        date_time_kst = datetime.strptime(self.file_name, "%Y%m%d_%H%M%S").replace(tzinfo=KST)
        self.kst_creation_time_from_name = date_time_kst.strftime("%H:%M:%S")

    def kst_creation_date_time(self) -> str:
        return self.creation_time_utc.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S")
    
    def kst_creation_time(self) -> str:
        return self.creation_time_utc.astimezone(KST).strftime("%H:%M:%S")
    
    def __repr__(self):
        return f"PhotoMeta (파일 이름: {self.file_name}, 생성 시간: {self.creation_time_utc})"
