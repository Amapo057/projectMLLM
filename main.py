# main.py
import sys
from dotenv import load_dotenv

# 모든 서비스 임포트
from services.wake_word_service import WakeWordService
from services.stt_service import STTService 
from services.gemini_service import GeminiService
from services.weather_service import WeatherService
from services.tts_service import TTSService

def main():
    load_dotenv()
    
    print("="*50)
    print("시스템 초기화 중... (UI 비활성화 모드)")
    
    # 1. 서비스 객체 초기화
    wake_word_service = WakeWordService(wakeword_model="hey_mycroft") # 테스트용 모델
    stt_service = STTService()
    gemini_service = GeminiService()
    weather_service = WeatherService()
    tts_service = TTSService()
    
    print("자비스(Jarvis) 테스트 구동 완료. (종료하려면 Ctrl+C)")
    print("="*50)

    try:
        while True:
            # --- [1단계: 백그라운드 호출어 대기] ---
            print("\n[대기 모드] 호출어('헤이 마이크로프트')를 기다리는 중...")
            detected = wake_word_service.listen_for_wake_word(threshold=0.5)
            
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
            context_data = None
            if "날씨" in user_text:
                print("☁️ 날씨 정보 수집 중...")
                context_data = weather_service.get_weather_context()

            # --- [4단계: LLM 응답 생성] ---
            print("🤖 자비스 생각중...")
            response_text = gemini_service.generate_response(prompt=user_text, context=context_data)
            print(f"🤖 자비스: {response_text}")
            
            # --- [5단계: TTS 음성 출력] ---
            tts_service.speak(response_text)
            
            # 한 번의 사이클이 끝나면 다시 while 문의 처음(대기 모드)으로 자연스럽게 돌아갑니다.

    except KeyboardInterrupt:
        print("\n[시스템 종료] 테스트를 마칩니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[치명적 오류 발생]: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()