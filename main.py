# main.py
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from service import stt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 1. 윈도우 기본 설정 (타이틀 바 없는 전체 화면)
        self.setWindowTitle("Jarvis MLLM")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.showFullScreen()  # 스팀덱(리눅스 데스크탑 모드)에 맞춰 전체 화면 실행
        
        # 2. 배경을 완전한 검은색으로 설정
        self.setStyleSheet("background-color: black;")
        
        # 3. 중앙 위젯 설정 (나중에 여기에 OrbPainter가 들어갈 예정)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 4. 레이아웃 (정중앙 정렬)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_widget.setLayout(layout)
        
    def keyPressEvent(self, event):
        # 테스트용: ESC 키를 누르면 프로그램 강제 종료
        if event.key() == Qt.Key.Key_Escape:
            self.close()

if __name__ == "__main__":
    # app = QApplication(sys.argv)
    
    # # 마우스 커서 숨기기 (선택 사항: 완전히 깔끔한 화면을 원할 때)
    # # app.setOverrideCursor(Qt.CursorShape.BlankCursor)
    
    # window = MainWindow()
    # window.show()
    
    # sys.exit(app.exec())
    stt_module = stt.STT()
    result = stt_module.listen_and_recognize()
    if result:
        print(result)
    else:
        print("실패")