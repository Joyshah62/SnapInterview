from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, 
    QHBoxLayout, QStackedWidget, QFrame
)
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt, Signal


class LoginView(QWidget):
    """Login/Signup view"""
    login_requested = Signal(str, str)  # email, password
    signup_requested = Signal(str, str)  # email, password
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        # Title
        title = QLabel("SnapInterview")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #2563eb; margin: 20px 0;")
        
        subtitle = QLabel("Login or create an account to continue")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #64748b; margin-bottom: 30px;")
        
        # Email input
        email_label = QLabel("Email")
        email_label.setStyleSheet("font-weight: bold; color: #334155;")
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #2563eb;
            }
        """)
        
        # Password input
        password_label = QLabel("Password")
        password_label.setStyleSheet("font-weight: bold; color: #334155; margin-top: 15px;")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #2563eb;
            }
        """)
        
        # Buttons
        self.login_button = QPushButton("Login")
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 12px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        
        self.signup_button = QPushButton("Sign Up")
        self.signup_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #2563eb;
                padding: 12px;
                border: 2px solid #2563eb;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #eff6ff;
            }
            QPushButton:pressed {
                background-color: #dbeafe;
            }
        """)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.login_button)
        btn_layout.addWidget(self.signup_button)
        btn_layout.setSpacing(10)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #dc2626; margin-top: 10px;")
        
        # Layout
        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(email_label)
        layout.addWidget(self.email_input)
        layout.addWidget(password_label)
        layout.addWidget(self.password_input)
        layout.addSpacing(20)
        layout.addLayout(btn_layout)
        layout.addWidget(self.status_label)
        layout.addStretch()
        
        # Add margins
        layout.setContentsMargins(40, 20, 40, 20)
        self.setLayout(layout)
        
        # Connect signals
        self.login_button.clicked.connect(self._on_login)
        self.signup_button.clicked.connect(self._on_signup)
        self.password_input.returnPressed.connect(self._on_login)
    
    def _on_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        if email and password:
            self.login_requested.emit(email, password)
    
    def _on_signup(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        if email and password:
            self.signup_requested.emit(email, password)
    
    def set_status(self, text: str, is_error: bool = True):
        self.status_label.setText(text)
        if is_error:
            self.status_label.setStyleSheet("color: #dc2626; margin-top: 10px;")
        else:
            self.status_label.setStyleSheet("color: #16a34a; margin-top: 10px;")
    
    def clear_inputs(self):
        self.email_input.clear()
        self.password_input.clear()
        self.status_label.clear()


class MainView(QWidget):
    """Main server control view"""
    start_server_requested = Signal()
    stop_server_requested = Signal()
    logout_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self._setup_ui()
    
    def _setup_ui(self):
        # Header with user info and logout
        self.user_label = QLabel("👤 Not logged in")
        user_font = QFont()
        user_font.setPointSize(12)
        user_font.setBold(True)
        self.user_label.setFont(user_font)
        self.user_label.setStyleSheet("color: #334155;")
        
        self.logout_button = QPushButton("🚪 Logout")
        self.logout_button.setMaximumWidth(100)
        self.logout_button.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        self.logout_button.clicked.connect(self.logout_requested.emit)
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(self.user_label)
        header_layout.addStretch()
        header_layout.addWidget(self.logout_button)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #e2e8f0; margin: 10px 0;")
        
        # Server status
        self.status_label = QLabel("🔴 Server stopped")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_font = QFont()
        status_font.setPointSize(14)
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("""
            padding: 15px;
            background-color: #f8fafc;
            border-radius: 8px;
            color: #334155;
        """)
        
        # QR code display
        self.qr_label = QLabel("QR Code will appear here")
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setMinimumHeight(320)
        self.qr_label.setStyleSheet("""
            background-color: #f8fafc;
            border: 2px dashed #cbd5e1;
            border-radius: 8px;
            color: #94a3b8;
            font-style: italic;
        """)
        
        # Control buttons
        self.start_button = QPushButton("▶ Start Server")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #16a34a;
                color: white;
                padding: 14px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #15803d;
            }
            QPushButton:disabled {
                background-color: #cbd5e1;
                color: #94a3b8;
            }
        """)
        
        self.stop_button = QPushButton("⏹ Stop Server")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                padding: 14px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
            QPushButton:disabled {
                background-color: #cbd5e1;
                color: #94a3b8;
            }
        """)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.setSpacing(10)
        
        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(header_layout)
        layout.addWidget(separator)
        layout.addWidget(self.status_label)
        layout.addSpacing(20)
        layout.addWidget(self.qr_label)
        layout.addSpacing(20)
        layout.addLayout(button_layout)
        layout.setContentsMargins(30, 20, 30, 20)
        
        self.setLayout(layout)
        
        # Connect signals
        self.start_button.clicked.connect(self.start_server_requested.emit)
        self.stop_button.clicked.connect(self.stop_server_requested.emit)
    
    def set_user(self, user_data):
        """Set the current logged-in user"""
        self.current_user = user_data
        if user_data:
            display_name = user_data.get('full_name') or user_data.get('username') or user_data.get('email')
            self.user_label.setText(f"👤 {display_name}")
        else:
            self.user_label.setText("👤 Not logged in")
    
    def set_qr(self, pixmap: QPixmap):
        self.qr_label.setStyleSheet("""
            background-color: white;
            border: 2px solid #cbd5e1;
            border-radius: 8px;
            padding: 10px;
        """)
        self.qr_label.setPixmap(
            pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
    
    def clear_qr(self):
        """Clear the QR code display"""
        self.qr_label.clear()
        self.qr_label.setText("QR Code will appear here")
        self.qr_label.setStyleSheet("""
            background-color: #f8fafc;
            border: 2px dashed #cbd5e1;
            border-radius: 8px;
            color: #94a3b8;
            font-style: italic;
        """)
    
    def set_connected(self, connected: bool):
        if connected:
            self.status_label.setText("🟢 Mobile connected")
            self.status_label.setStyleSheet("""
                padding: 15px;
                background-color: #f0fdf4;
                border-radius: 8px;
                color: #166534;
            """)
        else:
            self.status_label.setText("🟡 Server running, waiting for client...")
            self.status_label.setStyleSheet("""
                padding: 15px;
                background-color: #fefce8;
                border-radius: 8px;
                color: #854d0e;
            """)
    
    def set_server_running(self, running: bool):
        if running:
            self.status_label.setText("🟡 Server running, waiting for client...")
            self.status_label.setStyleSheet("""
                padding: 15px;
                background-color: #fefce8;
                border-radius: 8px;
                color: #854d0e;
            """)
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.status_label.setText("🔴 Server stopped")
            self.status_label.setStyleSheet("""
                padding: 15px;
                background-color: #f8fafc;
                border-radius: 8px;
                color: #334155;
            """)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)


class CombinedWindow(QWidget):
    """Main window that contains both login and main views"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SnapInterview")
        self.setFixedSize(500, 600)
        
        # Create stacked widget to switch between views
        self.stacked_widget = QStackedWidget()
        
        # Create views
        self.login_view = LoginView()
        self.main_view = MainView()
        
        # Add views to stacked widget
        self.stacked_widget.addWidget(self.login_view)  # index 0
        self.stacked_widget.addWidget(self.main_view)   # index 1
        
        # Set initial view to login
        self.stacked_widget.setCurrentIndex(0)
        
        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        # Apply window stylesheet
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
        """)
    
    def show_login(self):
        """Switch to login view"""
        self.login_view.clear_inputs()
        self.stacked_widget.setCurrentIndex(0)
    
    def show_main(self, user_data=None):
        """Switch to main view"""
        if user_data:
            self.main_view.set_user(user_data)
        self.stacked_widget.setCurrentIndex(1)