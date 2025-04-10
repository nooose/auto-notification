import os
import requests
from httplib2 import Http
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

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
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Http())
            print("토큰 갱신 완료")
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())
        return creds

    def download_latest_photo(self, save_as: str):
        item = self._get_latest_photo()
        if not item:
            return

        url = item["baseUrl"] + "=d"
        response = requests.get(url)
        if response.status_code == 200:
            with open(save_as, "wb") as file:
                file.write(response.content)
            # print(f"사진 저장 완료. '{save_as}'.")
        else:
            print("사진 다운로드에 실패하였습니다.:", response.status_code)

    def _get_latest_photo(self):
        results = self.service.mediaItems().list(pageSize=1).execute()
        items = results.get("mediaItems", [])
        if not items:
            print("사진을 찾을 수 없습니다.")
            return None
        return items[0]