import os
import requests
from google.auth.transport.requests import Request 
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from photo_meta import PhotoMeta
from datetime import datetime, timezone, timedelta
from googleapiclient.http import MediaIoBaseDownload
import io

# OAuth 2.0 인증 정보
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "client_secret.json"  # 발급받은 JSON 파일 경로

class PhotoDownloader:
    def __init__(self):
        self.creds = self._authenticate()
        self.service = build("drive", "v3", credentials=self.creds)

    def _authenticate(self):
        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if creds and creds.expired:
            creds.refresh(Request())
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())
        return creds

    def download_latest_photo(self, save_as: str) -> PhotoMeta:
        try:
            return self._download_latest_file(save_as)
        except Exception as e:
            self._refresh_token()
            raise e

    def _refresh_token(self):
        self.creds.refresh(Request())
        print("[토큰 갱신 완료]")

    def _download_latest_file(self, save_as: str) -> PhotoMeta:
        results = self.service.files().list(
            pageSize = 1,
            fields = "files(id, name, createdTime, modifiedTime, mimeType)",
            orderBy = "modifiedTime desc",
            q = "trashed = false"
        ).execute()

        items = results.get("files", [])
        if not items:
            raise RuntimeError("드라이브에 다운로드할 파일이 없습니다.")

        file = items[0]
        file_id = file["id"]
        file_name = file["name"]
        createdTime = file["createdTime"]

        self._download_file(file_id, save_as)
        return PhotoMeta(
            creation_time_utc=datetime.fromisoformat(createdTime.replace("Z", "+00:00")),
            file_name=file_name,
        )

    def _download_file(self, file_id: str, save_as: str):
        request = self.service.files().get_media(fileId=file_id)
        
        try:
            with io.FileIO(save_as, 'wb') as file_handle:
                downloader = MediaIoBaseDownload(file_handle, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
        except Exception as e:
            raise RuntimeError(f"파일 다운로드에 실패하였습니다: {e}")