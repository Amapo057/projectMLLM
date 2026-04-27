import subprocess
import datetime
import time
import urllib.request
import os
import glob
import socket
import struct
import shutil  # 샌드박스 우회 명령어 확인용 추가

import config


class SystemService:
    def __init__(self):
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
        
        # print(f"\n[시스템] 하드웨어 절전 모드(S3) 진입. 💤")
        # print(f"[시스템] 기상 예정 시간: {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. 기본 실행 명령어 (리눅스 rtcwake)
            base_cmd = ['sudo', 'rtcwake', '-m', 'mem', '-t', str(target_epoch)]
            
            # 2. Flatpak(VS Code 샌드박스) 환경 판별 및 우회 적용
            if shutil.which('sudo') is None:
                cmd = ['flatpak-spawn', '--host'] + base_cmd
            else:
                cmd = base_cmd

            # 3. 절전 명령어 실행
            subprocess.run(cmd, check=True)
            
            # === 이 라인 이후의 코드는 스팀덱이 아침에 기상한 직후에 실행됩니다. ===
            # print("\n[시스템] ☀️ 기상 완료. 시스템을 복구합니다.")
            
            # 기상 직후 와이파이가 다시 잡힐 때까지 대기 (방어 로직)
            self.wait_for_network()
            
        except subprocess.CalledProcessError as e:
            # print(f"[오류] 절전 모드 진입 실패. (sudo 권한을 확인해주세요): {e}")
            pass

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

    def wait_for_network(self, sleep_time=5) -> bool:
        """
        단순히 지정된 시간만큼 대기합니다.
        S3 수면 해제 후 WiFi 칩셋 안정화를 위한 시간 확보용입니다.
        """
        # print(f"[시스템] 네트워크 안정화 대기 중 ({sleep_time}초)...")
        
        # 1초씩 끊어서 출력해주면 진행 상황을 알기 좋습니다.
        for i in range(sleep_time, 0, -1):
            # print(f"[{i}]", end=" ", flush=True)
            time.sleep(1)
            
        # print("\n[시스템] 대기 완료. 서비스를 시작합니다.")
        return True

    def enter_temporary_sleep(self, hours=1):
        """
        [Temporary Sleep] 지정된 시간(시간 단위)만큼 즉시 절전 모드에 진입합니다.
        """
        seconds = int(hours * 3600)
        # print(f"\n[시스템] 낮잠 모드 진입: {hours}시간 동안 절전합니다. 😴")
        
        try:
            # 1. 기본 실행 명령어 (현재부터 n초 후 기상)
            base_cmd = ['sudo', 'rtcwake', '-m', 'mem', '-s', str(seconds)]
            
            # 2. 샌드박스 우회 로직 동일하게 적용
            if shutil.which('sudo') is None:
                cmd = ['flatpak-spawn', '--host'] + base_cmd
            else:
                cmd = base_cmd

            # 3. 절전 명령어 실행
            subprocess.run(cmd, check=True)
            
            # 깨어난 후 로직
            # print("\n[시스템] 일시 절전 종료. 다시 업무를 시작합니다.")
            self.wait_for_network()
            
        except subprocess.CalledProcessError as e:
            # print(f"[오류] 절전 모드 진입 실패: {e}")
            pass
    
    def wake_on_lan(self) -> bool:
        """
        [Network] 같은 로컬 네트워크 내의 다른 PC에 매직 패킷을 보내 전원을 켭니다.
        
        Args:
            mac_address (str): 켤 PC의 MAC 주소 (예: "1A:2B:3C:4D:5E:6F" 또는 "1A-2B-3C-4D-5E-6F")
        """
        mac_address = config.PC_MAC

        try:
            # 1. MAC 주소 문자열 정제 (구분자 제거)
            clean_mac = mac_address.replace(':', '').replace('-', '')
            if len(clean_mac) != 12:
                # print(f"[오류] 잘못된 MAC 주소 형식입니다: {mac_address}")
                return False
                
            # 2. 매직 패킷 구성: 6바이트의 0xFF + 16번 반복된 대상의 MAC 주소
            packet = bytes.fromhex('FF' * 6 + clean_mac * 16)
            
            # 3. UDP 브로드캐스트 소켓 생성 및 전송
            # 255.255.255.255 (서브넷 전체 대상)의 9번 포트로 쏘아 올립니다.
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(packet, ('255.255.255.255', 9))
                
            # print(f"[시스템] WOL 매직 패킷 전송 완료 (대상: {mac_address})")
            return True
            
        except Exception as e:
            # print(f"[오류] WOL 패킷 전송 중 예외 발생: {e}")
            return False

if __name__ == '__main__':
    # 테스트 코드를 실행하기 전 객체를 정상적으로 생성하도록 수정 
    sysTest = SystemService()
    
    # 주의: 이 코드를 직접 실행하면 스팀덱이 낮 12시 혹은 밤 12시까지 즉시 수면 모드에 들어갈 수 있습니다.
    # 안전한 테스트를 원하신다면 enter_temporary_sleep(hours=0.005) (약 18초) 등을 권장합니다.
    sysTest.wake_on_lan()
