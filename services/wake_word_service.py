# services/wake_word_service.py
import pyaudio
import numpy as np
from openwakeword.model import Model

class WakeWordService:
    def __init__(self, custom_model_path="services/yo_kah_ee.onnx"):
        print(f"[System] 커스텀 호출어 모델을 로드하는 중입니다... ({custom_model_path})")
        
        # 💡 핵심: 내장 모델 이름 대신, 내가 만든 파일의 '경로'를 직접 넘겨줍니다.
        self.oww_model = Model(wakeword_models=[custom_model_path], inference_framework="onnx")
        
        # oww_model.models 딕셔너리에서 로드된 커스텀 모델의 내부 키(이름)를 동적으로 가져옵니다.
        self.wakeword = list(self.oww_model.models.keys())[0]

        # PyAudio 오디오 스트림 설정
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 48000
        self.CHUNK = 3840

    def listen_for_wake_word(self, threshold=0.4) -> bool:
        """호출어가 감지될 때까지 대기합니다."""
        
        # 마이크 점유율 충돌(Locking) 방지를 위해 매번 새로 엽니다.
        audio = pyaudio.PyAudio() 
        stream = audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        try:
            while True:
                audio_data = stream.read(self.CHUNK, exception_on_overflow=False)
                audio_np = np.frombuffer(audio_data, dtype=np.int16)
                
                # 모델 예측
                prediction = self.oww_model.predict(audio_np)
                
                # 설정한 임계치(threshold)를 넘으면 감지 성공!
                score = prediction[self.wakeword]
                if score > threshold:
                    # 필요하다면 여기서 print(f"감지 스코어: {score}") 를 찍어보셔도 좋습니다.
                    return True
                    
        except Exception as e:
            print(f"[WakeWord Error] 오디오 스트림 오류: {e}")
            return False
            
        finally:
            # 완벽한 마이크 자원 해제
            stream.stop_stream()
            stream.close()
            audio.terminate()