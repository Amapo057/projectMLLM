#include <SoftwareSerial.h>
#include <RCSwitch.h>

SoftwareSerial bt(2, 4);
RCSwitch mySwitch = RCSwitch();

#define STX 0xFF
#define ETX 0xFE
#define CMD_TOGGLE 0x01
#define CMD_ON     0x02
#define CMD_OFF    0x03
#define ACK        0xA0
#define NAK        0xA1

uint8_t buf[5];
uint8_t idx = 0;

void sendResponse(uint8_t cmd, uint8_t data) {
  uint8_t pkt[5] = {STX, cmd, data, ETX, (uint8_t)(cmd ^ data)};
  Serial.write(pkt, 5);
}

bool parsePacket(uint8_t* p) {
  // 구조 검증
  if (p[0] != STX || p[3] != ETX) return false;
  // 체크섬 검증
  if ((p[1] ^ p[2]) != p[4]) return false;
  return true;
}

void handleCommand(uint8_t cmd, uint8_t data) {
  switch (cmd) {
    case CMD_TOGGLE:
    case CMD_ON:
    case CMD_OFF:
      mySwitch.send(13156820, 24);
      sendResponse(ACK, cmd);
      break;
    default:
      sendResponse(NAK, cmd);
  }
}

void setup() {
  Serial.begin(9600);
  bt.begin(9600);
  pinMode(10, OUTPUT);
  digitalWrite(10, LOW);
  mySwitch.enableTransmit(10);
  mySwitch.setProtocol(1);
  mySwitch.setPulseLength(299);
  mySwitch.setRepeatTransmit(10);
}

void loop() {
  while (Serial.available()) {
    uint8_t b = bt.read();
    if (b == STX) idx = 0;       // STX 감지 시 버퍼 초기화
    buf[idx++] = b;
    if (idx == 5) {               // 5바이트 수신 완료
      if (parsePacket(buf)) handleCommand(buf[1], buf[2]);
      else sendResponse(NAK, 0x00);
      idx = 0;
    }
  }
}