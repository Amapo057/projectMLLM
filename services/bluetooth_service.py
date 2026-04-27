import serial
import time
import threading

class BluetoothService:
    """
    Bluetooth Communication Service
    Communicates with Arduino based on the 5-byte binary protocol defined in light_switch.ino.
    
    Packet structure (5 bytes):
    [0] STX (0xFF)
    [1] CMD (Command)
    [2] DATA (Data payload)
    [3] ETX (0xFE)
    [4] Checksum (CMD ^ DATA)
    """
    
    # Protocol constants
    STX = 0xFF
    ETX = 0xFE
    
    # Commands
    CMD_TOGGLE = 0x01
    CMD_ON     = 0x02
    CMD_OFF    = 0x03
    
    # Responses
    ACK = 0xA0
    NAK = 0xA1

    def __init__(self, port="COM3", baudrate=9600, timeout=1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.lock = threading.Lock()

    def connect(self) -> bool:
        """Connects to the specified serial port (Bluetooth COM port)."""
        try:
            self.serial_conn = serial.Serial(
                port=self.port, 
                baudrate=self.baudrate, 
                timeout=self.timeout
            )
            # print(f"[BluetoothService] Connected to {self.port} at {self.baudrate} baud.")
            return True
        except serial.SerialException as e:
            # print(f"[BluetoothService] Failed to connect to {self.port}: {e}")
            return False

    def disconnect(self):
        """Disconnects the serial connection."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            # print("[BluetoothService] Disconnected.")

    def send_command(self, cmd: int, data: int = 0x00) -> bool:
        """
        Sends a command with optional data and waits for ACK.
        Constructs the 5-byte packet and validates checksum on the response.
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            # print("[BluetoothService] Error: Not connected.")
            return False

        checksum = cmd ^ data
        packet = bytearray([self.STX, cmd, data, self.ETX, checksum])

        with self.lock:
            try:
                self.serial_conn.write(packet)
                # # print(f"[BluetoothService] Sent: {[hex(x) for x in packet]}")
                return self._wait_for_response(cmd)
            except Exception as e:
                # print(f"[BluetoothService] Error sending command: {e}")
                return False

    def _wait_for_response(self, original_cmd: int) -> bool:
        """Reads from serial until a valid 5-byte response packet is received or timeout."""
        start_time = time.time()
        buf = bytearray()
        
        while time.time() - start_time < self.timeout:
            if self.serial_conn.in_waiting > 0:
                b = self.serial_conn.read(1)[0]
                
                # STX clears buffer and starts a new packet
                if b == self.STX:
                    buf = bytearray([b])
                elif len(buf) > 0:
                    buf.append(b)
                
                if len(buf) == 5:
                    if self._parse_packet(buf):
                        resp_cmd = buf[1]
                        resp_data = buf[2]
                        
                        if resp_cmd == self.ACK and resp_data == original_cmd:
                            # print(f"[BluetoothService] ACK received for command {hex(original_cmd)}")
                            return True
                        elif resp_cmd == self.NAK:
                            # print(f"[BluetoothService] NAK received for command {hex(resp_data)}")
                            return False
                        else:
                            # print(f"[BluetoothService] Unexpected response: {hex(resp_cmd)}")
                            return False
                    else:
                        # print("[BluetoothService] Invalid packet received (checksum/structure error).")
                        buf = bytearray() # Reset for next packet
            
            time.sleep(0.01)
            
        # print(f"[BluetoothService] Timeout waiting for response to command {hex(original_cmd)}.")
        return False

    def _parse_packet(self, packet: bytearray) -> bool:
        """Validates the structure and checksum of the received packet."""
        if len(packet) != 5:
            return False
        if packet[0] != self.STX or packet[3] != self.ETX:
            return False
        if (packet[1] ^ packet[2]) != packet[4]:
            return False
        return True

    # --- Convenience Methods for Specific Commands ---

    def turn_on(self) -> bool:
        """Sends ON command to the light switch."""
        # print("[BluetoothService] Turning ON light...")
        return self.send_command(self.CMD_ON)

    def turn_off(self) -> bool:
        """Sends OFF command to the light switch."""
        # print("[BluetoothService] Turning OFF light...")
        return self.send_command(self.CMD_OFF)

    def toggle(self) -> bool:
        """Sends TOGGLE command to the light switch."""
        # print("[BluetoothService] Toggling light...")
        return self.send_command(self.CMD_TOGGLE)

# Example Usage
if __name__ == "__main__":
    # Change "COM3" to the actual Bluetooth serial port assigned by Windows
    bt = BluetoothService(port="COM3")
    if bt.connect():
        bt.turn_on()
        time.sleep(1)
        bt.turn_off()
        bt.disconnect()
