import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal

# 모든 서비스 임포트
from services.wake_word_service import WakeWordService
from services.stt_service import STTService 
from services.gemini_service import GeminiService
from services.weather_service import WeatherService
from services.bus_service import BusService
from services.tts_service import TTSService
from services.calender_service import CalendarService
from services.system_service import SystemService
from services.iot_service import IoTService
import pygame

# UI 화면 임포트 (경로는 실제 파일 위치에 맞게 수정)
from screens.home_screen import HomeScreen

# --- [워커 스레드 (자비스의 뇌)] ---
class JarvisWorker(QThread):
    # 화면으로 상태를 전달할 신호 (현재는 검은 화면이지만 나중을 위해)
    status_signal = pyqtSignal(str) 

    def __init__(self, services):
        super().__init__()
        self.services = services
        self.is_running = True

        # 1. 오디오 믹서 초기화 및 파일 로드 (한 번만 실행)
        pygame.mixer.init()
        try:
            # 준비하신 효과음 파일 이름을 넣어주세요
            self.ding_sound = pygame.mixer.Sound("soundshelfstudio-ui-click-soft-.mp3") 
        except Exception as e:
            print(f"[경고] 효과음 파일을 찾을 수 없습니다: {e}")
            self.ding_sound = None

    def run(self):
        # 딕셔너리로 묶어둔 서비스들 꺼내기
        wake_word = self.services['wake_word']
        stt = self.services['stt']
        gemini = self.services['gemini']
        weather = self.services['weather']
        bus = self.services['bus']
        tts = self.services['tts']
        calendar = self.services['calendar']
        iot = self.services['iot']
        system = self.services['system']

        while True:
            try:
                self.status_signal.emit("호출어 대기 중...")
                detected = wake_word.listen_for_wake_word(threshold=0.4)
                
                if not detected:
                    continue
                
                if self.ding_sound:
                    self.ding_sound.play()
                    
                self.status_signal.emit("명령 듣는 중...")
                
                user_text = stt.listen_and_recognize()
                if not user_text or user_text.strip() == "":
                    continue
                    
                self.status_signal.emit(f"인식됨: {user_text}")

                # [버그 수정됨] 튜플 언패킹
                gemini_need, response_text = noGeminiKeyword(user_text, iot, system)

                if gemini_need:
                    self.status_signal.emit("데이터 수집 및 생각 중...")
                    context_data_list = []
                    
                    if "날씨" in user_text:
                        context_data_list.append(weather.get_weather_context())
                    if "버스" in user_text:
                        context_data_list.append(bus.get_bus_context())
                    if "일정" in user_text or "스케줄" in user_text or "캘린더" in user_text:
                        context_data_list.append(calendar.get_upcoming_events_context())

                    context_data = "\n".join(context_data_list) if context_data_list else None
                    response_text = gemini.generate_response(prompt=user_text, context=context_data)
                    
                if response_text:
                    self.status_signal.emit("대답 중...")
                    tts.speak(response_text)
                    
            except Exception as e:
                print(f"[워커 스레드 에러]: {e}")
                # 에러가 나도 스레드가 죽지 않게 넘깁니다. (실제 운영 시 중요)
                continue

# --- [로컬 키워드 처리 함수] ---
def noGeminiKeyword(user_text, iot_service, system_service) -> tuple:
    gemini_need = True
    response = ""
    
    if "불" in user_text and ("켜" in user_text or "꺼" in user_text):
        response = "밝기가 맞지않아 수행하지 않았어요"
        if "켜" in user_text:
            if iot_service.turn_on_light():
                response = "불을 켰습니다"
                gemini_need = False
        elif "꺼" in user_text:
            if iot_service.turn_off_light():
                response = "불을 껐습니다"
                gemini_need = False
                
    elif "컴퓨터" in user_text and "켜" in user_text:
        if system_service.wake_on_lan():
            response = "컴퓨터 전원을 켰습니다"
        else:
            response = "패킷 전송중 오류 발생했습니다"
        gemini_need = False
        
    elif "절전" in user_text and "모드" in user_text:
        system_service.enter_temporary_sleep(4)
        response = "작동 준비완료"
        gemini_need = False

    elif ("수면" in user_text and "모드" in user_text) or ("전원" in user_text and "꺼" in user_text):
        system_service.enter_hard_sleep()
        response = "작동 준비완료"
        gemini_need = False
    elif "요카이" in user_text and "종료" in user_text:
        import os
        os._exit(0) 
        
        return False, response
        
    return gemini_need, response

# --- [메인 실행부] ---
def main():
    app = QApplication(sys.argv)

    # 1. 서비스 객체 초기화 (딕셔너리로 묶어서 워커에 전달하기 쉽게 만듦)
    services = {
        'wake_word': WakeWordService(custom_model_path="services/yo_kah_ee.onnx"),
        'stt': STTService(),
        'gemini': GeminiService(),
        'weather': WeatherService(),
        'bus': BusService(),
        'tts': TTSService(),
        'calendar': CalendarService(),
        'iot': IoTService(),
        'system': SystemService()
    }

    # 2. UI 화면 생성 및 띄우기
    window = HomeScreen()
    window.show()

    # 3. 백그라운드 자비스 뇌(워커) 가동
    worker = JarvisWorker(services)
    
    # 워커에서 나오는 상태 메시지를 UI의 handle_stt_result 함수로 연결
    # (현재 HomeScreen은 검은 화면이므로 함수 안에서 print 처리하거나 로그를 남기면 됩니다)
    # worker.status_signal.connect(window.handle_stt_result) 
    
    worker.start()

    # 4. 프로그램 유지
    sys.exit(app.exec())

if __name__ == "__main__":
    main()