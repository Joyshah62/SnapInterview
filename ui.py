from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SnapInterview Server")
        self.setFixedSize(420, 520)
        
        self.status_label = QLabel("🔴 Server stopped")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setMinimumHeight(300)  # Reserve space for QR code
        
        self.start_button = QPushButton("▶ Start Server")
        self.stop_button = QPushButton("⏹ Stop Server")
        self.stop_button.setEnabled(False)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        
        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.qr_label)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def set_qr(self, pixmap: QPixmap):
        self.qr_label.setPixmap(
            pixmap.scaled(300, 300, Qt.KeepAspectRatio)
        )
    
    def clear_qr(self):
        """Clear the QR code display"""
        self.qr_label.clear()
    
    def set_connected(self, connected: bool):
        if connected:
            self.status_label.setText("🟢 Mobile connected")
        else:
            self.status_label.setText("🟡 Server running, no client")
    
    def set_server_running(self, running: bool):
        if running:
            self.status_label.setText("🟡 Server running, no client")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.status_label.setText("🔴 Server stopped")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)