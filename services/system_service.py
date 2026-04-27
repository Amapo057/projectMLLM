import subprocess
import datetime
import time
import urllib.request
import os
import glob
import socket
import struct


class SystemService:
    def __init__(self):
        # sudo visudo로 필요시 권한 주기
        # 시스템 초기화 시 필요한 상태값이나 로거를 설정할 수 있습니다.
        pass

    def enter_hard_sleep(self, wake_hour=7, wake_minute=0):
        """
        [Hard Sleep] OS 레벨 S3 수면 모드(rtcwake) 진입.
        스팀덱의 전력을 차단하고, 지정된 시간에 메인보드 RTC 알람으로 강제 기상합니다.
        
        Args:
            wake_hour (int): 기상할 시간 (0~23)
            wake_minute (int): 기상할 분 (0~59)
        """
        now = datetime.datetime.now()
        
        # 다음 기상 목표 시간 계산
        target_time = now.replace(hour=wake_hour, minute=wake_minute, second=0, microsecond=0)
        
        # 목표 시간이 현재 시간보다 이전이라면(이미 지났다면) '내일'로 설정
        if target_time <= now:
            target_time += datetime.timedelta(days=1)
            
        target_epoch = int(target_time.timestamp())
        
        print(f"\n[시스템] 하드웨어 절전 모드(S3) 진입. 💤")
        print(f"[시스템] 기상 예정 시간: {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 리눅스 rtcwake 명령어 실행
            # 주의: SteamOS 환경에 따라 sudo 비밀번호 없이 실행 가능하도록 visudo 설정이 필요할 수 있습니다.
            subprocess.run(['sudo', 'rtcwake', '-m', 'mem', '-t', str(target_epoch)], check=True)
            
            # === 이 라인 이후의 코드는 스팀덱이 아침에 기상한 직후에 실행됩니다. ===
            print("\n[시스템] ☀️ 기상 완료. 시스템을 복구합니다.")
            
            # 기상 직후 와이파이가 다시 잡힐 때까지 대기 (방어 로직)
            self.wait_for_network()
            
        except subprocess.CalledProcessError as e:
            print(f"[오류] 절전 모드 진입 실패. (sudo 권한을 확인해주세요): {e}")

    def is_soft_sleep_time(self, start_hour=23, end_hour=7) -> bool:
        """
        [Soft Sleep] 현재 시간이 소프트 절전 시간대인지 판별합니다.
        메인 루프에서 이 함수를 호출하여 마이크를 끌지 결정합니다.
        """
        current_hour = datetime.datetime.now().hour
        
        # 자정을 넘어가는 시간대 (예: 23시 ~ 07시)
        if start_hour > end_hour: 
            return current_hour >= start_hour or current_hour < end_hour
        # 당일 시간대 (예: 01시 ~ 07시)
        else:                     
            return start_hour <= current_hour < end_hour

    def wait_for_network(self, timeout=30) -> bool:
        """
        [Network Check] 와이파이가 연결되어 인터넷 통신이 가능한지 확인합니다.
        S3 수면에서 깨어나면 네트워크 칩셋이 IP를 할당받는 데 2~5초가 소요됩니다.
        """
        print("[시스템] 네트워크 연결 대기 중...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # 구글 DNS 서버에 매우 짧은 타임아웃으로 핑을 보내 연결 확인
                urllib.request.urlopen('http://8.8.8.8', timeout=1)
                print("[시스템] 네트워크 연결이 확인되었습니다. (API 사용 가능)")
                return True
            except Exception:
                time.sleep(1) # 1초 대기 후 재시도
                
        print("[경고] 네트워크 연결 대기 시간 초과. (오프라인 모드 또는 연결 불량)")
        return False
    def enter_temporary_sleep(self, hours=1):
        """
        [Temporary Sleep] 지정된 시간(시간 단위)만큼 즉시 절전 모드에 진입합니다.
        """
        seconds = int(hours * 3600)
        print(f"\n[시스템] 낮잠 모드 진입: {hours}시간 동안 절전합니다. 😴")
        
        try:
            # -s 옵션: 현재부터 n초 후에 깨어남
            subprocess.run(['sudo', 'rtcwake', '-m', 'mem', '-s', str(seconds)], check=True)
            
            # 깨어난 후 로직
            print("\n[시스템] 일시 절전 종료. 다시 업무를 시작합니다.")
            self.wait_for_network()
            
        except subprocess.CalledProcessError as e:
            print(f"[오류] 절전 모드 진입 실패: {e}")
    def get_ambient_light_level(self) -> int:
        """
        [Sensor] 스팀덱의 내장 조도 센서(ALS) 값을 읽어옵니다.
        반환값: 0(완전 어두움) ~ 수백/수천(밝음). 센서를 찾지 못하면 -1 반환.
        """
        # 리눅스 IIO 장치 목록에서 조도 센서(illuminance) 파일 경로 탐색
        # 기기에 따라 iio:device0, iio:device1 등 번호가 다를 수 있어 glob 사용
        sensor_paths = glob.glob('/sys/bus/iio/devices/iio:device*/in_illuminance_raw')
        
        if not sensor_paths:
            # 센서 경로를 찾지 못한 경우 (권한 문제 또는 하드웨어 미지원)
            return -1
            
        try:
            # 첫 번째 발견된 조도 센서 파일 읽기
            with open(sensor_paths[0], 'r') as f:
                light_level = int(f.read().strip())
                return light_level
        except Exception as e:
            print(f"[오류] 조도 센서 읽기 실패: {e}")
            return -1

    def is_room_dark(self, threshold=50) -> bool:
        """
        [State] 현재 방이 어두운 상태(불이 꺼짐)인지 판별합니다.
        threshold 값은 방 환경에 맞게 테스트 후 조정하세요.
        """
        lux = self.get_ambient_light_level()
        
        if lux == -1:
            return False # 센서 오류 시 안전을 위해 밝은 상태로 간주
            
        # 디버깅용 출력
        # print(f"[센서] 현재 조도 값: {lux}")
        
        return lux < threshold
    def wake_on_lan(self, mac_address: str) -> bool:
        """
        [Network] 같은 로컬 네트워크 내의 다른 PC에 매직 패킷을 보내 전원을 켭니다.
        
        Args:
            mac_address (str): 켤 PC의 MAC 주소 (예: "1A:2B:3C:4D:5E:6F" 또는 "1A-2B-3C-4D-5E-6F")
        """
        try:
            # 1. MAC 주소 문자열 정제 (구분자 제거)
            clean_mac = mac_address.replace(':', '').replace('-', '')
            if len(clean_mac) != 12:
                print(f"[오류] 잘못된 MAC 주소 형식입니다: {mac_address}")
                return False
                
            # 2. 매직 패킷 구성: 6바이트의 0xFF + 16번 반복된 대상의 MAC 주소
            packet = bytes.fromhex('FF' * 6 + clean_mac * 16)
            
            # 3. UDP 브로드캐스트 소켓 생성 및 전송
            # 255.255.255.255 (서브넷 전체 대상)의 9번 포트로 쏘아 올립니다.
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(packet, ('255.255.255.255', 9))
                
            print(f"[시스템] WOL 매직 패킷 전송 완료 (대상: {mac_address})")
            return True
            
        except Exception as e:
            print(f"[오류] WOL 패킷 전송 중 예외 발생: {e}")
            return False