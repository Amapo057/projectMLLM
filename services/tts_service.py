# services/tts_service.py
import asyncio
import edge_tts
import pygame
import os

class TTSService:
    def __init__(self):
        # 자비스 느낌의 남성 목소리 (여성을 원하시면 'ko-KR-SunHiNeural' 사용)
        self.voice = "ko-KR-SunHiNeural" 
        self.output_file = "temp_response.mp3"
        
        # 오디오 재생을 위한 pygame 초기화
        pygame.mixer.init()

    async def _generate_audio(self, text: str):
        """edge-tts를 사용해 텍스트를 mp3 파일로 변환 (비동기)"""
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(self.output_file)

    def speak(self, text: str):
        """텍스트를 음성으로 출력 (동기 대기)"""
        if not text:
            return

        # print("🔊 음성 생성 중...")
        
        # 1. 비동기 오디오 생성 함수를 동기적으로 실행
        asyncio.run(self._generate_audio(text))
        
        # 2. 생성된 오디오 파일 로드 및 재생
        pygame.mixer.music.load(self.output_file)
        pygame.mixer.music.play()
        
        # 3. 재생이 완전히 끝날 때까지 대기 (현재 CLI 파이프라인용)
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        # 4. 재생 완료 후 파일 점유(Lock) 해제
        pygame.mixer.music.unload()
        
        # 필요시 임시 파일 삭제 (선택 사항)
        if os.path.exists(self.output_file):
            os.remove(self.output_file)