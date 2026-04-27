import os.path
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class CalendarService:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        self.creds = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """구글 계정 인증 및 토큰 관리 (동일)"""
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    print("[Error] credentials.json 파일이 없습니다.")
                    return
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())

        try:
            self.service = build('calendar', 'v3', credentials=self.creds)
        except HttpError as error:
            print(f'[Calendar Error] 서비스 생성 실패: {error}')
            

    def get_upcoming_events_context(self) -> str:
        """오늘부터 향후 2주(14일)간의 일정을 가져와 브리핑 텍스트로 반환"""
        if not self.service:
            return "캘린더 서비스를 사용할 수 없습니다."

        try:
            # 1. 범위 설정: 현재 시간부터 14일 후까지
            now = datetime.datetime.utcnow()
            time_min = now.isoformat() + 'Z'  # 시작 시간 (현재)
            time_max = (now + datetime.timedelta(days=14)).isoformat() + 'Z' # 종료 시간 (14일 후)

            # print(f"[System] {now.date()}부터 14일간의 일정을 조회합니다...")

            events_result = self.service.events().list(
                calendarId='primary', 
                timeMin=time_min,
                timeMax=time_max, # 2주 제한 추가
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])

            if not events:
                return "향후 2주 동안 예정된 일정이 없습니다."

            event_list = []
            for event in events:
                # 시작 날짜/시간 정보 가져오기
                start_raw = event['start'].get('dateTime', event['start'].get('date'))
                
                # 날짜 부분만 추출 (YYYY-MM-DD)
                date_str = start_raw.split('T')[0]
                summary = event.get('summary', '(제목 없음)')
                
                # 요카이(제미나이)가 읽기 좋게 "날짜: 내용" 형식으로 정리
                event_list.append(f"- {date_str}: {summary}")

            return f"향후 2주간의 주요 일정입니다:\n" + "\n".join(event_list)

        except HttpError as error:
            # print(f'[Calendar Error] 일정 조회 실패: {error}')
            return "구글 캘린더에서 일정을 가져오는 중 오류가 발생했습니다."