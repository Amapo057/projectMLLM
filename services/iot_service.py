import serial
import time
import glob

class IoTService:
    # 아두이노 프로토콜 상수 정의
    STX = 0xFF
    ETX = 0xFE
    CMD_TOGGLE = 0x01
    CMD_ON = 0x02
    CMD_OFF = 0x03
    ACK = 0xA0
    NAK = 0xA1

    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        self.baudrate = baudrate
        self.serial_conn = None
        self.connect_arduino()

    # ==========================================
    # 1. 하드웨어 통신 (Arduino - Packet Protocol)
    # ==========================================
    def connect_arduino(self) -> bool:
        try:
            possible_ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
            if not possible_ports:
                # print("[IoT] 연결된 아두이노 장치를 찾을 수 없습니다.")
                return False
                
            # timeout=1 은 read() 호출 시 최대 1초만 기다리겠다는 뜻입니다. (무한 대기 방지)
            self.serial_conn = serial.Serial(possible_ports[0], self.baudrate, timeout=1, write_timeout=1)
            time.sleep(2) # 아두이노 부팅 대기
            # print(f"[IoT] 스마트 홈 제어기 연결 완료 ({possible_ports[0]})")
            return True
            
        except serial.SerialException as e:
            # print(f"[오류] 아두이노 연결 실패: {e}")
            self.serial_conn = None
            return False

    def _send_packet(self, cmd: int, data: int = 0x00) -> bool:
        """5바이트 프로토콜 패킷을 전송하고 최대 3회 재시도합니다."""
        max_retries = 3
        
        for attempt in range(max_retries):
            # 1. 연결 상태 체크
            if self.serial_conn is None or not self.serial_conn.is_open:
                # print(f"[IoT] 연결 재시도 중... ({attempt + 1}/{max_retries})")
                if not self.connect_arduino():
                    time.sleep(0.5)
                    continue

            try:
                self.serial_conn.reset_input_buffer()
                
                # 2. 패킷 전송
                checksum = cmd ^ data
                packet = bytes([self.STX, cmd, data, self.ETX, checksum])
                self.serial_conn.write(packet)
                self.serial_conn.flush()

                # 3. 아두이노 응답 대기 (여기서 1초 타임아웃 적용)
                response = self.serial_conn.read(5)
                
                # ==========================================
                # 💡 4. 프로토콜 검증 및 ACK/NAK 처리 
                # ==========================================
                if len(response) != 5:
                    # print(f"[IoT] {attempt + 1}회차 실패: 타임아웃 또는 데이터 잘림")
                    continue # 다음 루프로 넘어가서 재시도
                    
                if response[0] != self.STX or response[3] != self.ETX:
                    # print(f"[IoT] {attempt + 1}회차 실패: 패킷 구조 오류 (노이즈)")
                    continue # 다음 루프로 넘어가서 재시도
                    
                if (response[1] ^ response[2]) != response[4]:
                    # print(f"[IoT] {attempt + 1}회차 실패: 체크섬(Checksum) 불일치")
                    continue # 다음 루프로 넘어가서 재시도
                    
                # 패킷이 정상적으로 도착했을 때 ACK/NAK 판별
                if response[1] == self.ACK:
                    # print("[IoT] 명령 성공 (ACK 수신) 🎯")
                    return True # 완벽하게 성공했으므로 즉시 함수 종료
                    
                elif response[1] == self.NAK:
                    # print(f"[IoT] 명령 거부됨 (NAK 수신, CMD: {hex(response[2])})")
                    # NAK는 통신 에러가 아니라 아두이노가 "나 이거 안 해!"라고 거부한 것이므로
                    # 재시도할 필요 없이 바로 실패(False)를 반환합니다.
                    return False 

            except Exception as e:
                # print(f"[IoT] {attempt + 1}회차 통신 에러: {e}")
                self.serial_conn.close() # 포트가 꼬였을 수 있으니 닫아줌
                self.serial_conn = None
            
            # 재시도 전에 0.5초 대기 (아두이노가 정신 차릴 시간)
            time.sleep(0.5)

        # print("[IoT] 3회 재시도 모두 실패했습니다. 통신을 포기합니다.")
        return False

    # ==========================================
    # 2. 센서 데이터 (Sensor)
    # ==========================================
    def get_ambient_light_level(self) -> int:
        sensor_paths = glob.glob('/sys/bus/iio/devices/iio:device*/in_illuminance_raw')
        if not sensor_paths: return -1
        try:
            with open(sensor_paths[0], 'r') as f:
                return int(f.read().strip())
        except Exception:
            return -1

    def is_room_dark(self, threshold=30) -> bool:
        lux = self.get_ambient_light_level()
        if lux == -1: return False
        return lux < threshold

    # ==========================================
    # 3. 조명 제어 (Lighting)
    # ==========================================
    def turn_on_light(self) -> bool:
        if not self.is_room_dark():
            # print("[IoT] 이미 밝습니다. 조명을 켜지 않습니다.")
            return False
        return self._send_packet(self.CMD_ON)

    def turn_off_light(self) -> bool:
        if self.is_room_dark():
            # print("[IoT] 이미 어둡습니다. 조명을 끄지 않습니다.")
            return False
        return self._send_packet(self.CMD_OFF)
    

if __name__ == "__main__":
    iot = IoTService()
    iot.connect_arduino()
    iot.turn_off_light()