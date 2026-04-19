# find_mic.py
import os
# 💡 [핵심] 파이썬이 리눅스의 PipeWire 설정을 읽지 못하도록 차단!
os.environ['ALSA_CONFIG_PATH'] = '/dev/null' 
import pyaudio

p = pyaudio.PyAudio()
print("\n=== 깔끔해진 마이크 목록 ===")
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    if dev.get('maxInputChannels') > 0:
        print(f"[{i}번] {dev.get('name')}")
p.terminate()
print("===============================\n")