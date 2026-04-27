from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QEvent

class HomeScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Jarvis MLLM")
        
        # 1. 프레임 제거 및 항상 위 설정
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowDoesNotAcceptFocus # 클릭 방해 금지 (선택사항)
        )
        
        # 2. 풀스크린 및 마우스 커서 숨기기
        self.showFullScreen()
        self.setCursor(Qt.CursorShape.BlankCursor)
        
        # 3. OLED용 리얼 블랙 설정
        self.setStyleSheet("background-color: #000000;")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_widget.setLayout(layout)

    def keyPressEvent(self, event):
        # 개발용: Esc 누르면 자비스 종료
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def mouseDoubleClickEvent(self, event):
        """
        비상구: 화면의 아무 곳이나 마우스로 더블 클릭(또는 터치 두 번)하면 종료됩니다.
        """
        # print("[UI] 더블 클릭 감지. 자비스 창을 닫습니다.")
        self.close()

    def handle_stt_result(self, stt_text: str):
        # 나중에 여기에 텍스트 애니메이션 등을 넣으시면 됩니다.
        pass