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
            self.serial_conn = serial.Serial(possible_ports[0], self.baudrate, timeout=1)
            time.sleep(2) # 아두이노 부팅 대기
            # print(f"[IoT] 스마트 홈 제어기 연결 완료 ({possible_ports[0]})")
            return True
            
        except serial.SerialException as e:
            # print(f"[오류] 아두이노 연결 실패: {e}")
            self.serial_conn = None
            return False

    def _send_packet(self, cmd: int, data: int = 0x00) -> bool:
        """5바이트 프로토콜 패킷을 생성하여 전송하고 ACK를 확인합니다."""
        if self.serial_conn is None or not self.serial_conn.is_open:
            # print("[IoT] 연결이 끊어져 재연결을 시도합니다.")
            if not self.connect_arduino():
                return False
                
        # 체크섬(XOR) 계산
        checksum = cmd ^ data
        # 전송할 5바이트 배열 생성
        packet = bytes([self.STX, cmd, data, self.ETX, checksum])

        try:
            # 수신 버퍼에 남아있는 이전 쓰레기 데이터 비우기
            self.serial_conn.reset_input_buffer() 
            
            # 패킷 전송
            self.serial_conn.write(packet)
            
            # 아두이노의 응답(5바이트) 대기
            response = self.serial_conn.read(5)
            
            if len(response) != 5:
                # print(f"[IoT] 응답 타임아웃 또는 패킷 잘림 (수신: {len(response)} bytes)")
                return False
                
            # 응답 패킷 구조 검증 (STX, ETX)
            if response[0] != self.STX or response[3] != self.ETX:
                # print("[IoT] 잘못된 응답 패킷 구조")
                return False
                
            # 응답 패킷 체크섬 검증
            if (response[1] ^ response[2]) != response[4]:
                # print("[IoT] 응답 패킷 체크섬 오류")
                return False
                
            # ACK / NAK 확인
            if response[1] == self.ACK:
                # print(f"[IoT] 명령 성공 (ACK 수신)")
                return True
            elif response[1] == self.NAK:
                # print(f"[IoT] 명령 거부 (NAK 수신, 원인 CMD: {hex(response[2])})")
                return False
            else:
                # print(f"[IoT] 알 수 없는 응답 코드: {hex(response[1])}")
                return False
                
        except Exception as e:
            # print(f"[오류] 패킷 전송 중 예외 발생: {e}")
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

    def is_room_dark(self, threshold=35) -> bool:
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