import sys
import pygame
import threading
import time
from datetime import datetime

from services.wake_word_service import WakeWordService
from services.stt_service import STTService
from services.gemini_service import GeminiService
from services.weather_service import WeatherService
from services.bus_service import BusService
from services.tts_service import TTSService
from services.calender_service import CalendarService
from services.system_service import SystemService
from services.iot_service import IoTService


def auto_sleep_scheduler(system_service):
    sleep_hour = 12
    sleep_minute = 00
    last_sleep_date = None

    while True:
        now = datetime.now()

        if (
            now.hour == sleep_hour
            and now.minute == sleep_minute
            and last_sleep_date != now.date()
        ):
            system_service.enter_hard_sleep()
            last_sleep_date = now.date()

        time.sleep(50)


def main():    
    wake_word_service = WakeWordService(custom_model_path="services/yo_kah_ee.onnx")
    stt_service = STTService()
    gemini_service = GeminiService()
    weather_service = WeatherService()
    bus_service = BusService()
    tts_service = TTSService()
    calendar_service = CalendarService()
    iot_service = IoTService()
    system_service = SystemService()

    # 자동 수면 스케줄러 실행
    sleep_thread = threading.Thread(
        target=auto_sleep_scheduler,
        args=(system_service,),
        daemon=True
    )
    sleep_thread.start()

    pygame.mixer.init()
    try:
        wake_sound = pygame.mixer.Sound("soundshelfstudio-ui-click-soft.mp3")
    except Exception:
        wake_sound = None

    try:
        while True:
            detected = wake_word_service.listen_for_wake_word(threshold=0.5)

            if not detected:
                continue

            if wake_sound:
                wake_sound.play()

            user_text = stt_service.listen_and_recognize()
            if not user_text or user_text.strip() == "":
                continue

            gemini_need, response_text = noGeminiKeyword(
                user_text,
                iot_service,
                system_service,
                wake_sound
            )

            if gemini_need:
                context_data_list = []

                if "날씨" in user_text:
                    weather_context = weather_service.get_weather_context()
                    context_data_list.append(weather_context)

                if "버스" in user_text:
                    bus_context = bus_service.get_bus_context()
                    context_data_list.append(bus_context)

                if "일정" in user_text or "스케줄" in user_text or "캘린더" in user_text:
                    calendar_context = calendar_service.get_upcoming_events_context()
                    context_data_list.append(calendar_context)

                context_data = "\n".join(context_data_list) if context_data_list else None

                response_text = gemini_service.generate_response(
                    prompt=user_text,
                    context=context_data
                )

            tts_service.speak(response_text)

    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        sys.exit(1)

def noGeminiKeyword(user_text, iot_service, system_service, wake_sound) -> tuple:
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
        wake_sound.play()
        time.sleep(0.4)
        wake_sound.play()
        time.sleep(2)
        system_service.enter_hard_sleep()
        response = "작동 준비완료"
        gemini_need = False

    return gemini_need, response



if __name__ == "__main__":

    main()