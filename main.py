import sys
import pygame

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

# from services.bluetooth_service import BluetoothService

def main():    
    # 1. 서비스 객체 초기화
    wake_word_service = WakeWordService(custom_model_path="services/yo_kah_ee.onnx") # 추가로 학습시킨 단어 사용
    stt_service = STTService()
    gemini_service = GeminiService()
    weather_service = WeatherService()
    bus_service = BusService()
    tts_service = TTSService()
    calendar_service = CalendarService()
    iot_service = IoTService()
    system_service = SystemService()

    # 유선 연결로 변경
    # bluetooth_service = BluetoothService(port="COM3")
    # bluetooth_service.connect()  

    # 작동음 찾기
    pygame.mixer.init()
    try:
        wake_sound = pygame.mixer.Sound("soundshelfstudio-ui-click-soft.mp3")
    except Exception as e:
        wake_sound = None

    # print("===구동===")

    try:
        while True:
            # --- [1단계: 백그라운드 호출어 대기] ---
            # print("\n[대기 모드] 호출어('yokai')를 기다리는 중...")
            detected = wake_word_service.listen_for_wake_word(threshold=0.4)

            if not detected:
                continue

            # print("\n[호출어 감지!]")
            if wake_sound:
                wake_sound.play()

            # --- [2단계: STT 사용자 명령 인식] ---
            user_text = stt_service.listen_and_recognize()
            if not user_text or user_text.strip() == "":
                # print("[알림] 입력된 음성이 없습니다. 다시 대기 모드로 돌아갑니다.")
                continue

            # print(f"👤 사용자: {user_text}")
            gemini_need, response_text = noGeminiKeyword(user_text, iot_service, system_service)
            if gemini_need:
                # --- [3단계: 외부 데이터 수집 (라우팅)] ---
                context_data_list = []

                if "날씨" in user_text:
                    # print("☁️ 날씨 정보 수집 중...")
                    weather_context = weather_service.get_weather_context()
                    context_data_list.append(weather_context)

                if "버스" in user_text:
                    # print("🚌 버스 정보 수집 중...")
                    bus_context = bus_service.get_bus_context()
                    context_data_list.append(bus_context)

                if "일정" in user_text or "스케줄" in user_text or "캘린더" in user_text:
                    # print("📅 일정 정보 수집 중...")
                    calendar_context = calendar_service.get_upcoming_events_context()
                    context_data_list.append(calendar_context)

                context_data = "\n".join(context_data_list) if context_data_list else None

                # --- [4단계: LLM 응답 생성] ---
                # print("🤖 자비스 생각중...")
                response_text = gemini_service.generate_response(prompt=user_text, context=context_data)
                # print(f"🤖 자비스: {response_text}")

            # --- [5단계: TTS 음성 출력] ---
            tts_service.speak(response_text)


    except KeyboardInterrupt:
        # print("\n[시스템 종료] 테스트를 마칩니다.")
        sys.exit(0)
    except Exception as e:
        # print(f"\n[치명적 오류 발생]: {e}")
        sys.exit(1)

def noGeminiKeyword(user_text, iot_service, system_service) -> tuple:
    gemini_need = True
    response = ""

    if "불" in user_text and ("켜" in user_text or "꺼" in user_text):
        # print("💡 조명 제어 중...")
        response = "밝기가 맞지않아 수행하지 않았어요"
        if "켜" in user_text:
            success = iot_service.turn_on_light()
            if success:
                response = "불을 켰습니다"

        elif "꺼" in user_text:
            success = iot_service.turn_off_light()
            if success:
                response = "불을 껐습니다"
        gemini_need = False

    elif "컴퓨터" in user_text and "켜" in user_text:
        success = system_service.wake_on_lan()
        if success:
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

    return gemini_need, response



if __name__ == "__main__":

    main()