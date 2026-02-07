from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QStackedWidget, QFrame, QScrollArea, QSizePolicy
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
        # Container for centering
        container = QWidget()
        container.setMaximumWidth(400)
        
        # Title
        title = QLabel("SnapInterview")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #2563eb; margin: 20px 0;")
        
        subtitle = QLabel("Login or create an account to continue")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #64748b; margin-bottom: 30px; font-size: 14px;")
        
        # Email input
        email_label = QLabel("Email")
        email_label.setStyleSheet("font-weight: bold; color: #334155;")
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
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
                padding: 12px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #2563eb;
            }
        """)
        
        # Buttons
        self.login_button = QPushButton("Login")
        self.login_button.setMinimumHeight(45)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 12px;
                border: none;
                border-radius: 8px;
                font-size: 15px;
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
        self.signup_button.setMinimumHeight(45)
        self.signup_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #2563eb;
                padding: 12px;
                border: 2px solid #2563eb;
                border-radius: 8px;
                font-size: 15px;
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
        btn_layout.setSpacing(12)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("margin-top: 10px; font-size: 13px;")
        self.status_label.setWordWrap(True)
        
        # Container layout
        container_layout = QVBoxLayout()
        container_layout.addStretch()
        container_layout.addWidget(title)
        container_layout.addWidget(subtitle)
        container_layout.addWidget(email_label)
        container_layout.addWidget(self.email_input)
        container_layout.addWidget(password_label)
        container_layout.addWidget(self.password_input)
        container_layout.addSpacing(25)
        container_layout.addLayout(btn_layout)
        container_layout.addWidget(self.status_label)
        container_layout.addStretch()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container.setLayout(container_layout)
        
        # Main layout (centers the container)
        main_layout = QHBoxLayout()
        main_layout.addStretch()
        main_layout.addWidget(container)
        main_layout.addStretch()
        self.setLayout(main_layout)
        
        # Connect signals
        self.login_button.clicked.connect(self._on_login)
        self.signup_button.clicked.connect(self._on_signup)
        self.password_input.returnPressed.connect(self._on_login)
    
    def _on_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        if email and password:
            self.login_requested.emit(email, password)
        else:
            self.set_status("Please enter both email and password", True)
    
    def _on_signup(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        if email and password:
            self.signup_requested.emit(email, password)
        else:
            self.set_status("Please enter both email and password", True)
    
    def set_status(self, text: str, is_error: bool = True):
        self.status_label.setText(text)
        if is_error:
            self.status_label.setStyleSheet("color: #dc2626; margin-top: 10px; font-size: 13px;")
        else:
            self.status_label.setStyleSheet("color: #16a34a; margin-top: 10px; font-size: 13px;")
    
    def clear_inputs(self):
        self.email_input.clear()
        self.password_input.clear()
        self.status_label.clear()


class SidebarButton(QPushButton):
    """Custom styled sidebar button"""
    def __init__(self, text, icon=""):
        super().__init__(f"{icon}  {text}")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(50)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #64748b;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                text-align: left;
                font-size: 15px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                color: #334155;
            }
            QPushButton:checked {
                background-color: #dbeafe;
                color: #2563eb;
                font-weight: 600;
            }
        """)


class HomeView(QWidget):
    """Home view with server controls and QR code"""
    start_server_requested = Signal()
    stop_server_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        # Header with title and server controls
        header = QWidget()
        header_layout = QHBoxLayout()
        
        title = QLabel("Server Control")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #1e293b;")
        
        # Server status indicator
        self.status_indicator = QLabel("🔴 Stopped")
        self.status_indicator.setStyleSheet("""
            background-color: #fee2e2;
            color: #991b1b;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 13px;
        """)
        
        # Server control buttons
        self.start_button = QPushButton("▶ Start Server")
        self.start_button.setMinimumWidth(140)
        self.start_button.setMinimumHeight(40)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #16a34a;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
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
        self.stop_button.setMinimumWidth(140)
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
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
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.status_indicator)
        header_layout.addSpacing(15)
        header_layout.addWidget(self.start_button)
        header_layout.addWidget(self.stop_button)
        header.setLayout(header_layout)
        
        # QR Code section
        qr_container = QFrame()
        qr_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
            }
        """)
        
        qr_layout = QVBoxLayout()
        
        qr_title = QLabel("Scan QR Code to Connect")
        qr_title.setAlignment(Qt.AlignCenter)
        qr_title_font = QFont()
        qr_title_font.setPointSize(16)
        qr_title_font.setBold(True)
        qr_title.setFont(qr_title_font)
        qr_title.setStyleSheet("color: #334155; margin: 20px 0 10px 0;")
        
        qr_subtitle = QLabel("Open the mobile app and scan this code")
        qr_subtitle.setAlignment(Qt.AlignCenter)
        qr_subtitle.setStyleSheet("color: #64748b; margin-bottom: 20px; font-size: 14px;")
        
        self.qr_label = QLabel("Start server to display QR code")
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setMinimumSize(400, 400)
        self.qr_label.setStyleSheet("""
            background-color: #f8fafc;
            border: 3px dashed #cbd5e1;
            border-radius: 12px;
            color: #94a3b8;
            font-style: italic;
            font-size: 14px;
        """)
        
        qr_layout.addWidget(qr_title)
        qr_layout.addWidget(qr_subtitle)
        qr_layout.addWidget(self.qr_label)
        qr_layout.addSpacing(20)
        qr_layout.setContentsMargins(30, 10, 30, 30)
        qr_container.setLayout(qr_layout)
        
        layout = QVBoxLayout()
        layout.addWidget(header)
        layout.addSpacing(30)
        layout.addWidget(qr_container, 1)
        layout.addStretch()
        layout.setContentsMargins(40, 30, 40, 30)
        self.setLayout(layout)
        
        self.start_button.clicked.connect(self.start_server_requested.emit)
        self.stop_button.clicked.connect(self.stop_server_requested.emit)
    
    def set_qr(self, pixmap: QPixmap):
        self.qr_label.setStyleSheet("""
            background-color: white;
            border: none;
            border-radius: 12px;
            padding: 20px;
        """)
        self.qr_label.setPixmap(
            pixmap.scaled(350, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
    
    def clear_qr(self):
        self.qr_label.clear()
        self.qr_label.setText("Start server to display QR code")
        self.qr_label.setStyleSheet("""
            background-color: #f8fafc;
            border: 3px dashed #cbd5e1;
            border-radius: 12px;
            color: #94a3b8;
            font-style: italic;
            font-size: 14px;
        """)
    
    def set_connected(self, connected: bool):
        if connected:
            self.status_indicator.setText("🟢 Connected")
            self.status_indicator.setStyleSheet("""
                background-color: #dcfce7;
                color: #166534;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            """)
        else:
            self.status_indicator.setText("🟡 Waiting for client...")
            self.status_indicator.setStyleSheet("""
                background-color: #fef3c7;
                color: #854d0e;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            """)
    
    def set_server_running(self, running: bool):
        if running:
            self.status_indicator.setText("🟡 Waiting for client...")
            self.status_indicator.setStyleSheet("""
                background-color: #fef3c7;
                color: #854d0e;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            """)
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.status_indicator.setText("🔴 Stopped")
            self.status_indicator.setStyleSheet("""
                background-color: #fee2e2;
                color: #991b1b;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            """)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)


class SummaryView(QWidget):
    """Summary view for interview details"""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        # Header
        header = QWidget()
        header_layout = QHBoxLayout()
        
        title = QLabel("Interview Summary")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #1e293b;")
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setMinimumHeight(40)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        header.setLayout(header_layout)
        
        # Stats cards
        stats_layout = QHBoxLayout()
        
        # Total interviews card
        total_card = self._create_stat_card("📊 Total Interviews", "0", "#3b82f6")
        stats_layout.addWidget(total_card)
        
        # Completed card
        completed_card = self._create_stat_card("✅ Completed", "0", "#10b981")
        stats_layout.addWidget(completed_card)
        
        # In Progress card
        progress_card = self._create_stat_card("⏳ In Progress", "0", "#f59e0b")
        stats_layout.addWidget(progress_card)
        
        # Recent interviews section
        recent_section = QFrame()
        recent_section.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
            }
        """)
        
        recent_layout = QVBoxLayout()
        
        recent_title = QLabel("Recent Interviews")
        recent_title_font = QFont()
        recent_title_font.setPointSize(16)
        recent_title_font.setBold(True)
        recent_title.setFont(recent_title_font)
        recent_title.setStyleSheet("color: #334155; margin-bottom: 15px;")
        
        # Placeholder content
        placeholder = QLabel("No interviews recorded yet.\nStart the server and conduct interviews to see them here.")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("""
            color: #94a3b8;
            font-size: 14px;
            padding: 60px;
            background-color: #f8fafc;
            border-radius: 8px;
        """)
        
        recent_layout.addWidget(recent_title)
        recent_layout.addWidget(placeholder)
        recent_layout.setContentsMargins(30, 20, 30, 30)
        recent_section.setLayout(recent_layout)
        
        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(header)
        layout.addSpacing(30)
        layout.addLayout(stats_layout)
        layout.addSpacing(30)
        layout.addWidget(recent_section, 1)
        layout.setContentsMargins(40, 30, 40, 30)
        self.setLayout(layout)
    
    def _create_stat_card(self, title: str, value: str, color: str):
        """Create a statistics card"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-left: 4px solid {color};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 500;")
        
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(28)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet(f"color: {color}; margin-top: 5px;")
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch()
        card.setLayout(layout)
        
        return card


class DashboardView(QWidget):
    """Main dashboard with sidebar navigation"""
    logout_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self._setup_ui()
    
    def _setup_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar
        sidebar = QFrame()
        sidebar.setMaximumWidth(250)
        sidebar.setMinimumWidth(250)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border-right: 2px solid #e2e8f0;
            }
        """)
        
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(5)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        
        # App logo/title
        app_title = QLabel("SnapInterview")
        app_title_font = QFont()
        app_title_font.setPointSize(18)
        app_title_font.setBold(True)
        app_title.setFont(app_title_font)
        app_title.setStyleSheet("color: #2563eb; margin-bottom: 10px; padding: 10px;")
        
        # User info
        self.user_label = QLabel("👤 User")
        self.user_label.setStyleSheet("""
            color: #475569;
            padding: 12px;
            background-color: #e2e8f0;
            border-radius: 8px;
            font-weight: 600;
            font-size: 13px;
        """)
        self.user_label.setWordWrap(True)
        
        # Navigation buttons
        nav_label = QLabel("NAVIGATION")
        nav_label.setStyleSheet("""
            color: #94a3b8;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
            margin-top: 20px;
            margin-bottom: 5px;
            padding-left: 10px;
        """)
        
        self.home_btn = SidebarButton("Home", "🏠")
        self.summary_btn = SidebarButton("Summary", "📊")
        
        self.home_btn.setChecked(True)  # Default selection
        
        # Logout button
        self.logout_btn = QPushButton("🚪 Logout")
        self.logout_btn.setMinimumHeight(45)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #fee2e2;
                color: #991b1b;
                border: none;
                border-radius: 8px;
                padding: 12px;
                text-align: center;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #fecaca;
            }
        """)
        
        sidebar_layout.addWidget(app_title)
        sidebar_layout.addWidget(self.user_label)
        sidebar_layout.addWidget(nav_label)
        sidebar_layout.addWidget(self.home_btn)
        sidebar_layout.addWidget(self.summary_btn)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.logout_btn)
        
        sidebar.setLayout(sidebar_layout)
        
        # Content area with stacked widget
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: #f1f5f9;")
        
        # Create views
        self.home_view = HomeView()
        self.summary_view = SummaryView()
        
        self.content_stack.addWidget(self.home_view)    # index 0
        self.content_stack.addWidget(self.summary_view)  # index 1
        
        # Add to main layout
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.content_stack, 1)
        
        self.setLayout(main_layout)
        
        # Connect navigation
        self.home_btn.clicked.connect(lambda: self._switch_view(0))
        self.summary_btn.clicked.connect(lambda: self._switch_view(1))
        self.logout_btn.clicked.connect(self.logout_requested.emit)
    
    def _switch_view(self, index: int):
        """Switch between views and update button states"""
        self.content_stack.setCurrentIndex(index)
        
        # Update button checked states
        self.home_btn.setChecked(index == 0)
        self.summary_btn.setChecked(index == 1)
    
    def set_user(self, user_data):
        """Set the current logged-in user"""
        self.current_user = user_data
        if user_data:
            display_name = user_data.get('full_name') or user_data.get('username') or user_data.get('email')
            self.user_label.setText(f"👤 {display_name}")
        else:
            self.user_label.setText("👤 User")


class CombinedWindow(QWidget):
    """Main window that contains both login and dashboard views"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SnapInterview")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Create stacked widget to switch between views
        self.stacked_widget = QStackedWidget()
        
        # Create views
        self.login_view = LoginView()
        self.dashboard_view = DashboardView()
        
        # Add views to stacked widget
        self.stacked_widget.addWidget(self.login_view)     # index 0
        self.stacked_widget.addWidget(self.dashboard_view) # index 1
        
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
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            }
        """)
    
    def show_login(self):
        """Switch to login view"""
        self.login_view.clear_inputs()
        self.stacked_widget.setCurrentIndex(0)
    
    def show_dashboard(self, user_data=None):
        """Switch to dashboard view"""
        if user_data:
            self.dashboard_view.set_user(user_data)
        self.stacked_widget.setCurrentIndex(1)