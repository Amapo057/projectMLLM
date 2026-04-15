import speech_recognition as sr
import logging

class STT:
    def __init__(self):
        # recognizer 객체 생성
        self.recognizer = sr.Recognizer()

        # 음성 인식 최적화
        # 이 수치보다 큰 소리만 음성으로 간주
        self.recognizer.energy_threshold = 300
        # 침묵 시간 판단(단위 초)
        self.recognizer.pause_threshold = 1.2

    def listen_and_recognize(self) -> str:
        # 음성을 텍스트로 반환
        # 오류 발생, 아무말 없을 시 빈 문자열 반환

        # sr.Micropone과 with문 사용시 알아서 마이크 자원 열고 닫음
        with sr.Microphone() as source:
            logging.info("마이크 활성화")
            # 0.5초동안 배경 소음 측정해 기준점 재설정
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            logging.info("듣는중")

            try:
                # 마이크 입력 대기
                # timeout으로 설정한 초만큼 소리가 없으면 대기 종료
                # pharse_time_limit으로 설정한 초만큼 녹음
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
            except sr.WaitTimeoutError:
                # 8초동안 아무말도 안한경우
                logging.info("입력시간 초과")
                return ""
            
            logging.info("음성 변환")
            try:
                # 한국어 인식 설정
                text = self.recognizer.recognize_whisper
                self.recognizer.recognize_whisper(audio, language='ko-KR')
                logging.info(f"인식된 문장: {text}")
                return text
            except sr.UnknownValueError:
                # 소리는 들었으나 이해못한경우
                logging.warning("못알아먹음")
                return ""
            

                
