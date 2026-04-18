# main.py
import sys
from dotenv import load_dotenv

# 모든 서비스 임포트
from services.wake_word_service import WakeWordService
from services.stt_service import STTService 
from services.gemini_service import GeminiService
from services.weather_service import WeatherService
from services.bus_service import BusService
from services.tts_service import TTSService
from services.calender_service import CalendarService
from services.bluetooth_service import BluetoothService

def main():
    load_dotenv()
    
    print("="*50)
    print("시스템 초기화 중... (UI 비활성화 모드)")
    
    # 1. 서비스 객체 초기화
    wake_word_service = WakeWordService(custom_model_path="services/yo_kah_ee.onnx") # 테스트용 모델
    stt_service = STTService()
    gemini_service = GeminiService()
    weather_service = WeatherService()
    bus_service = BusService()
    tts_service = TTSService()
    calendar_service = CalendarService()
    
    # 블루투스 서비스 초기화 및 연결 (포트 번호는 환경에 맞게 변경 필요)
    bluetooth_service = BluetoothService(port="COM3")
    bluetooth_service.connect()
    
    print("자비스(Jarvis) 테스트 구동 완료. (종료하려면 Ctrl+C)")
    print("="*50)

    try:
        while True:
            # --- [1단계: 백그라운드 호출어 대기] ---
            print("\n[대기 모드] 호출어('헤이 마이크로프트')를 기다리는 중...")
            detected = wake_word_service.listen_for_wake_word(threshold=0.4)
            
            if not detected:
                continue
                
            print("\n[호출어 감지!] 네, 듣고 있습니다. 명령을 말씀해주세요.")
            
            # (옵션) 여기서 "띠링~" 하는 짧은 효과음을 재생해주면 사용자 경험이 매우 좋아집니다.

            # --- [2단계: STT 사용자 명령 인식] ---
            user_text = stt_service.listen_and_recognize()
            if not user_text or user_text.strip() == "":
                print("[알림] 입력된 음성이 없습니다. 다시 대기 모드로 돌아갑니다.")
                continue
                
            print(f"👤 사용자: {user_text}")
            
            # --- [3단계: 외부 데이터 수집 (라우팅)] ---
            context_data_list = []
            
            if "날씨" in user_text:
                print("☁️ 날씨 정보 수집 중...")
                weather_context = weather_service.get_weather_context()
                context_data_list.append(weather_context)
                
            if "버스" in user_text:
                print("🚌 버스 정보 수집 중...")
                bus_context = bus_service.get_bus_context()
                context_data_list.append(bus_context)
                
            if "일정" in user_text or "스케줄" in user_text or "캘린더" in user_text:
                print("📅 일정 정보 수집 중...")
                calendar_context = calendar_service.get_upcoming_events_context()
                context_data_list.append(calendar_context)

            # 조명 제어 (켜기/끄기 동일한 toggle 동작으로 처리)
            if "불" in user_text and ("켜" in user_text or "꺼" in user_text):
                print("💡 조명 제어 중...")
                success = bluetooth_service.toggle()
                if success:
                    context_data_list.append("시스템 컨텍스트: 사용자의 요청으로 조명을 제어(토글)했습니다.")
                else:
                    context_data_list.append("시스템 컨텍스트: 조명 제어에 실패했습니다. 블루투스 연결을 확인해주세요.")

            context_data = "\n".join(context_data_list) if context_data_list else None

            # --- [4단계: LLM 응답 생성] ---
            print("🤖 자비스 생각중...")
            response_text = gemini_service.generate_response(prompt=user_text, context=context_data)
            print(f"🤖 자비스: {response_text}")
            
            # --- [5단계: TTS 음성 출력] ---
            tts_service.speak(response_text)
            
            # 한 번의 사이클이 끝나면 다시 대기 모드로 돌아갑니다.

    except KeyboardInterrupt:
        print("\n[시스템 종료] 테스트를 마칩니다.")
        bluetooth_service.disconnect()
        sys.exit(0)
    except Exception as e:
        print(f"\n[치명적 오류 발생]: {e}")
        bluetooth_service.disconnect()
        sys.exit(1)

if __name__ == "__main__":
    main()