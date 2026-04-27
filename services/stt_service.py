import os
import subprocess
import shutil
import speech_recognition as sr

class STTService:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def listen_and_recognize(self, record_seconds=5) -> str:
        # 수정됨: /tmp 대신 현재 실행 중인 프로젝트 폴더에 임시 파일을 생성합니다.
        # 이렇게 하면 Flatpak 샌드박스 내부(파이썬)와 외부(arecord)가 동일한 파일을 바라보게 됩니다.
        temp_audio_path = os.path.join(os.getcwd(), "stt_capture.wav")
        
        base_cmd = [
            'arecord', '-D', 'pulse', '-r', '16000', '-c', '1', 
            '-f', 'S16_LE', '-d', str(record_seconds), '-q', temp_audio_path
        ]
        
        if shutil.which('arecord') is None:
            cmd = ['flatpak-spawn', '--host'] + base_cmd
        else:
            cmd = base_cmd

        # print(f"\n[STT] 듣고 있습니다... ({record_seconds}초간 녹음)")
        
        try:
            # 녹음 실행 (완료될 때까지 블로킹 대기)
            subprocess.run(cmd, check=True)
            
            # 녹음 파일이 정상적으로 생성되었는지 방어 코드 추가
            if not os.path.exists(temp_audio_path):
                # print("[오류] 오디오 파일이 생성되지 않았습니다. 호스트 마이크 설정을 확인해주세요.")
                return ""
            
            # 저장된 임시 오디오 파일을 SpeechRecognition으로 로드
            with sr.AudioFile(temp_audio_path) as source:
                audio_data = self.recognizer.record(source)
                
            # print("[STT] 음성 분석 중...")
            text = self.recognizer.recognize_google(audio_data, language='ko-KR')
            return text

        except subprocess.CalledProcessError as e:
            # print(f"[오류] 오디오 녹음 실패: {e}")
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            # print(f"[오류] Google STT 서비스 요청 실패: {e}")
            return ""
        except Exception as e:
            # print(f"[오류] STT 처리 중 예기치 못한 에러: {e}")
            return ""
        finally:
            # 분석 후 프로젝트 폴더가 지저분해지지 않도록 파일 삭제
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)