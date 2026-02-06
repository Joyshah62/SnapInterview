# from PySide6.QtWidgets import (
#     QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
# )
# from PySide6.QtGui import QPixmap
# from PySide6.QtCore import Qt

# class MainWindow(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("SnapInterview Server")
#         self.setFixedSize(420, 520)
        
#         self.status_label = QLabel("🔴 Server stopped")
#         self.status_label.setAlignment(Qt.AlignCenter)
        
#         self.qr_label = QLabel()
#         self.qr_label.setAlignment(Qt.AlignCenter)
#         self.qr_label.setMinimumHeight(300)  # Reserve space for QR code
        
#         self.start_button = QPushButton("▶ Start Server")
#         self.stop_button = QPushButton("⏹ Stop Server")
#         self.stop_button.setEnabled(False)
        
#         button_layout = QHBoxLayout()
#         button_layout.addWidget(self.start_button)
#         button_layout.addWidget(self.stop_button)
        
#         layout = QVBoxLayout()
#         layout.addWidget(self.status_label)
#         layout.addWidget(self.qr_label)
#         layout.addLayout(button_layout)
        
#         self.setLayout(layout)
    
#     def set_qr(self, pixmap: QPixmap):
#         self.qr_label.setPixmap(
#             pixmap.scaled(300, 300, Qt.KeepAspectRatio)
#         )
    
#     def clear_qr(self):
#         """Clear the QR code display"""
#         self.qr_label.clear()
    
#     def set_connected(self, connected: bool):
#         if connected:
#             self.status_label.setText("🟢 Mobile connected")
#         else:
#             self.status_label.setText("🟡 Server running, no client")
    
#     def set_server_running(self, running: bool):
#         if running:
#             self.status_label.setText("🟡 Server running, no client")
#             self.start_button.setEnabled(False)
#             self.stop_button.setEnabled(True)
#         else:
#             self.status_label.setText("🔴 Server stopped")
#             self.start_button.setEnabled(True)
#             self.stop_button.setEnabled(False)

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
)
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt, Signal

class MainWindow(QWidget):
    logout_requested = Signal()  # Signal for logout
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SnapInterview Server")
        self.setFixedSize(420, 560)
        
        self.current_user = None
        
        # User info section
        self.user_label = QLabel("Not logged in")
        self.user_label.setAlignment(Qt.AlignCenter)
        user_font = QFont()
        user_font.setBold(True)
        self.user_label.setFont(user_font)
        
        self.logout_button = QPushButton("🚪 Logout")
        self.logout_button.clicked.connect(self.logout_requested.emit)
        self.logout_button.setMaximumWidth(100)
        
        user_layout = QHBoxLayout()
        user_layout.addStretch()
        user_layout.addWidget(self.user_label)
        user_layout.addStretch()
        user_layout.addWidget(self.logout_button)
        
        # Server status
        self.status_label = QLabel("🔴 Server stopped")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # QR code
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setMinimumHeight(300)  # Reserve space for QR code
        
        # Server control buttons
        self.start_button = QPushButton("▶ Start Server")
        self.stop_button = QPushButton("⏹ Stop Server")
        self.stop_button.setEnabled(False)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        
        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(user_layout)
        layout.addSpacing(10)
        layout.addWidget(self.status_label)
        layout.addWidget(self.qr_label)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def set_user(self, user_data):
        """Set the current logged-in user"""
        self.current_user = user_data
        if user_data:
            display_name = user_data.get('full_name') or user_data.get('username')
            self.user_label.setText(f"👤 {display_name}")
        else:
            self.user_label.setText("Not logged in")
    
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