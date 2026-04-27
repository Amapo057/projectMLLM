import subprocess
import shutil
import numpy as np
from openwakeword.model import Model

class WakeWordService:
    def __init__(self, custom_model_path="services/yo_kah_ee.onnx"):
        # 1. 호출어 모델 로드 (이 부분이 누락되어서 에러가 발생했었습니다)
        self.owwModel = Model(wakeword_models=[custom_model_path], inference_framework="onnx")
        
        # 2. 오디오 스트림(arecord) 명령어 구성
        base_cmd = ['arecord', '-D', 'pulse', '-r', '16000', '-c', '1', '-f', 'S16_LE', '-t', 'raw']
        
        # 3. Flatpak(VS Code 샌드박스) 환경 우회 적용
        if shutil.which('arecord') is None:
            cmd = ['flatpak-spawn', '--host'] + base_cmd
        else:
            cmd = base_cmd

        # 4. 백그라운드 오디오 녹음 프로세스 시작
        self.audio_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )

    def listen_for_wake_word(self, threshold=0.4) -> bool:
        # 지정된 바이트만큼 오디오 데이터 읽기
        raw_data = self.audio_process.stdout.read(2560)
        if not raw_data:
            return False
            
        audio_data = np.frombuffer(raw_data, dtype=np.int16)
        
        # 모델 예측 (여기서 self.owwModel이 정상적으로 사용됩니다)
        prediction = self.owwModel.predict(audio_data)
        
        # 임계값(threshold) 초과 여부 검사
        for wakeword, score in prediction.items():
            if score > threshold:
                print(f"\n[디버그] 호출어 감지됨! (인식률: {score:.2f} / 기준치: {threshold})")
                return True
                
        return False
        
    def close(self):
        if hasattr(self, 'audio_process'):
            self.audio_process.terminate()