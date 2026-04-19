# services/stt_service.py
from faster_whisper import WhisperModel
import pyaudio
import wave
import os

class STTService:
    def __init__(self):
        print("[System] Faster-Whisper 모델 로딩 중... (small 모델 권장)")
        # compute_type="int8" 로 설정하면 메모리 사용량을 절반으로 줄입니다 (스팀덱 최적화)
        self.model = WhisperModel("small", device="cpu", compute_type="int8")
        
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 48000
        self.CHUNK = 3840
        self.RECORD_SECONDS = 5 # 임시 녹음 시간 (또는 Vosk에서 넘어온 오디오 데이터 사용)
        self.temp_audio_file = "temp_user_voice.wav"

    def listen_and_recognize(self) -> str:
        """마이크로 음성을 녹음하고 텍스트로 변환합니다."""
        
        # 1. 마이크 녹음 (예시용 기본 로직, 필요시 VAD로 말 끝남을 감지하도록 수정 가능)
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=self.FORMAT, 
            channels=self.CHANNELS,
            rate=self.RATE, 
            input=True,
            frames_per_buffer=self.CHUNK,
            input_device_index=6
            )
        
        print("🎙️ 듣고 있습니다...")
        frames = []
        for _ in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
            data = stream.read(self.CHUNK, exception_on_overflow=False)
            frames.append(data)
            
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # 임시 wav 파일로 저장
        with wave.open(self.temp_audio_file, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(frames))

        # 2. Faster-Whisper로 STT 변환
        print("⏳ 텍스트 변환 중...")
        
        # [핵심] vad_filter=True 로 환각 방지, initial_prompt로 한국어 힌트 제공
        segments, info = self.model.transcribe(
            self.temp_audio_file, 
            beam_size=5,
            vad_filter=True, 
            vad_parameters=dict(min_silence_duration_ms=500),
            initial_prompt="다음은 한국어로 된 데스크탑 비서에 대한 명령입니다."
        )

        text_result = ""
        for segment in segments:
            text_result += segment.text

        # 파일 정리
        if os.path.exists(self.temp_audio_file):
            os.remove(self.temp_audio_file)

        return text_result.strip()