# screens/home_screen.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from services.gemini_service import GeminiWorker
# from widgets.orb_painter import OrbPainter (나중에 추가될 UI 컴포넌트)

class HomeScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.gemini_worker = None

    def init_ui(self):
        self.setWindowTitle("Jarvis MLLM")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.showFullScreen()
        self.setStyleSheet("background-color: black;")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_widget.setLayout(layout)
        
    def handle_stt_result(self, stt_text: str):
        # UI에서 처리할 워커 로직...
        pass