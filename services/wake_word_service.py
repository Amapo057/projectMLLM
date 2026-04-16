# services/wake_word_service.py
import pyaudio
import numpy as np
import openwakeword
from openwakeword.model import Model

class WakeWordService:
    def __init__(self, wakeword_model="hey_mycroft"):
        print("[System] 호출어 모델을 확인/다운로드하는 중입니다...")
        
        # --- [핵심 추가 코드] ---
        # 기본 제공되는 모델(.onnx) 파일들이 없으면 자동으로 다운로드합니다.
        # (최초 1회만 다운로드하며, 이후에는 설치된 파일을 그대로 사용합니다)
        openwakeword.utils.download_models()
        
        print("[System] 호출어 모델을 로드하는 중입니다...")
        # onnx 런타임을 통해 모델 로드
        self.oww_model = Model(wakeword_models=[wakeword_model], inference_framework="onnx")
        self.wakeword = wakeword_model

        # PyAudio 오디오 스트림 설정 (openwakeword 권장 스펙: 16kHz, 1채널, 16bit PCM)
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1280
        self.audio = pyaudio.PyAudio()

    def listen_for_wake_word(self, threshold=0.5) -> bool:
        """
        호출어가 감지될 때까지 백그라운드에서 대기(블로킹)합니다.
        """
        stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        try:
            while True:
                # 1. 마이크에서 오디오 데이터(청크) 읽기
                audio_data = stream.read(self.CHUNK, exception_on_overflow=False)
                audio_np = np.frombuffer(audio_data, dtype=np.int16)

                # 2. 모델 예측 (오디오 데이터를 넣어 확률 점수 계산)
                prediction = self.oww_model.predict(audio_np)

                # 3. 설정된 모델의 점수가 임계치(threshold)를 넘으면 감지된 것으로 판단
                score = prediction[self.wakeword]
                if score > threshold:
                    return True
                    
        except Exception as e:
            print(f"[WakeWord Error] 오디오 스트림 오류: {e}")
            return False
            
        finally:
            # [매우 중요] 호출어가 감지되었거나 에러가 나면 마이크 점유를 즉시 해제합니다.
            # 해제하지 않으면 다음 순서인 STT에서 마이크를 열지 못해 충돌이 발생합니다.
            stream.stop_stream()
            stream.close()