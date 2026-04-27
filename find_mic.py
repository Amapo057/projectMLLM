import pyaudio

def list_audio_input_devices():
    p = pyaudio.PyAudio()
    # print("=== 사용할 수 있는 오디오 입력 장치 목록 ===")
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        # 입력 채널이 1개 이상인 장치만 필터링
        if dev_info.get('maxInputChannels', 0) > 0:
            # print(f"Index [{i}] - {dev_info.get('name')}")
    p.terminate()

if __name__ == "__main__":
    list_audio_input_devices()