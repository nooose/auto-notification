import os
import json
import requests
from httplib2 import Http
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# OAuth 2.0 인증 정보
SCOPES = ["https://www.googleapis.com/auth/photoslibrary.readonly"]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "client_secret_1060577310620-nkos0h3sng51k4ss3rf18brdqaufve24.apps.googleusercontent.com.json"  # 발급받은 JSON 파일 경로

def authenticate():
    """Google Photos API에 인증"""
    creds = None

    # 기존 토큰 파일 확인
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # 인증이 없거나 만료되었으면 새로 로그인
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)

        # 새로운 토큰 저장
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds

def get_photo_list(service):
    """Google Photos에서 사진 목록 가져오기"""
    results = service.mediaItems().list(pageSize=1).execute()
    items = results.get("mediaItems", [])

    if not items:
        print("사진이 없습니다.")
        return []

    for idx, item in enumerate(items):
        print(f"{idx+1}. 파일이름: {item['filename']}, URL: {item['baseUrl']}")

    return items

def download_photo(item, save_dir="downloads"):
    """사진을 다운로드하여 로컬에 저장"""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    url = item["baseUrl"] + "=d"  # 원본 다운로드 URL
    response = requests.get(url)

    if response.status_code == 200:
        file_path = os.path.join(save_dir, item["filename"])
        with open(file_path, "wb") as file:
            file.write(response.content)
        print(f"다운로드 완료: {file_path}")
    else:
        print("다운로드 실패:", response.status_code)

if __name__ == "__main__":
    creds = authenticate()
    service = build("photoslibrary", "v1", credentials = creds, static_discovery = False)

    items = get_photo_list(service)
    if items:
        download_photo(items[0])  # 첫 번째 사진 다운로드

