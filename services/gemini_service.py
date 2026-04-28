# services/gemini_service.py
import os
from google import genai
from google.genai import types
from PyQt6.QtCore import QThread, pyqtSignal
from config import GEMINI_API_KEY

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        
        self.model_name = "gemini-3.1-flash-lite-preview"
        # self.model_name = "gemini-2.5-flash"
        
        # 비서의 페르소나 및 응답 규칙 설정
        self.system_instruction = (
            "당신은 AI 비서입니다."
            "사용자의 질문에 간결하고 명확하게 한국어로 답변하세요. "
            "음성으로 출력될 예정이므로 읽기 편한 구어체를 사용하십시오."
        )

    def generate_response(self, prompt: str, context: str = None) -> str:
        """
        STT 텍스트와 (선택적) 외부 API 컨텍스트를 조합하여 답변을 생성합니다.
        """
        # 외부 API(날씨, 일정 등) 데이터가 있다면 프롬프트에 병합
        final_prompt = prompt
        if context:
            final_prompt = f"참고 데이터: {context}\n\n사용자 명령: {prompt}"

        config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            temperature=0.7,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=final_prompt,
                config=config
            )
            return response.text
        except Exception as e:
            # print(f"[Gemini Error] API 호출 중 오류 발생: {e}")
            return "네트워크 연결이 원활하지 않거나 처리 중 오류가 발생했습니다."


class GeminiWorker(QThread):
    """
    PyQt6 UI 쓰레드 차단(Freezing)을 방지하기 위한 백그라운드 Worker 클래스
    """
    # 처리 완료 후 응답 텍스트를 메인 쓰레드로 전달할 시그널
    finished_signal = pyqtSignal(str)
    # 에러 발생 시 UI에 알릴 시그널
    error_signal = pyqtSignal(str)

    def __init__(self, stt_text: str, context_data: str = None):
        super().__init__()
        self.stt_text = stt_text
        self.context_data = context_data
        self.service = GeminiService()

    def run(self):
        """
        QThread.start() 호출 시 백그라운드에서 실행되는 메서드
        """
        try:
            response_text = self.service.generate_response(
                prompt=self.stt_text,
                context=self.context_data
            )
            self.finished_signal.emit(response_text)
        except Exception as e:
            self.error_signal.emit(str(e))