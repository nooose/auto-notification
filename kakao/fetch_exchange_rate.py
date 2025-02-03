from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# 인증 정보 및 구글 스프레드시트 ID
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SAMPLE_SPREADSHEET_ID = '1oFYWVmL4TuowdfAQpFXHLnDCA-D3JtsCKL3ipTbrZlI'
SAMPLE_RANGE_NAME = 'A1'  # 'A1' 셀에서 환율값 가져오기
CREDENTIALS_FILE = "client_secret_1060577310620-nkos0h3sng51k4ss3rf18brdqaufve24.apps.googleusercontent.com.json"  # 발급받은 JSON 파일 경로

def get_current_exchange_rate():
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    service = build('sheets', 'v4', credentials=creds)

    sheet = service.spreadsheets()
    request = sheet.values().update(
        spreadsheetId=SAMPLE_SPREADSHEET_ID,
        range=SAMPLE_RANGE_NAME,
        valueInputOption="USER_ENTERED",
        body={"values": [["=GOOGLEFINANCE(\"CURRENCY:USDKRW\")"]]}
    )
    request.execute()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values', [])

    if values:
        return float(values[0][0])  # A1 셀의 환율 값 반환
    else:
        print("환율 데이터를 찾을 수 없습니다.")
        return None

print(get_current_exchange_rate())

