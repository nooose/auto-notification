import os
import requests
from google.auth.transport.requests import Request 
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from photo_meta import PhotoMeta
from datetime import datetime, timezone, timedelta

# OAuth 2.0 인증 정보
SCOPES = ["https://www.googleapis.com/auth/photoslibrary.readonly"]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "client_secret.json"  # 발급받은 JSON 파일 경로

class PhotoDownloader:
    def __init__(self):
        self.creds = self._authenticate()
        self.service = build("photoslibrary", "v1", credentials=self.creds, static_discovery=False)

    def _authenticate(self):
        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if creds and creds.expired:
            creds.refresh(Request())
            print("[토큰 갱신 완료]")
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())
        return creds

    def download_latest_photo(self, save_as: str) -> PhotoMeta:
        meta_data = self._get_latest_photo()
        if not meta_data:
            return
        
        response = requests.get(meta_data.base_url)
        if response.status_code == 200:
            with open(save_as, "wb") as file:
                file.write(response.content)
            return meta_data
        else:
            raise ValueError("사진 다운로드에 실패하였습니다.")

    def _get_latest_photo(self) -> PhotoMeta:
        results = self.service.mediaItems().list(pageSize=1).execute()
        items = results.get("mediaItems", [])
        if not items:
            return None
        item = items[0]
        raw_time = item["mediaMetadata"]["creationTime"]
        utc = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
        url = item["baseUrl"] + "=d"
        return PhotoMeta(creation_time_utc=utc, file_name=item["filename"], base_url=url)
