import json
from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QStackedWidget, QFrame, QScrollArea, QSizePolicy,
    QProgressBar
)
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt, Signal, QThread


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
        title.setStyleSheet("color: #60a5fa; margin: 20px 0;")
        
        subtitle = QLabel("Login or create an account to continue")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #94a3b8; margin-bottom: 30px; font-size: 14px;")
        
        # Email input
        email_label = QLabel("Email")
        email_label.setStyleSheet("font-weight: bold; color: #e2e8f0;")
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #475569;
                border-radius: 8px;
                font-size: 14px;
                background: #334155;
                color: #f1f5f9;
            }
            QLineEdit:focus {
                border-color: #60a5fa;
            }
        """)
        
        # Password input
        password_label = QLabel("Password")
        password_label.setStyleSheet("font-weight: bold; color: #e2e8f0; margin-top: 15px;")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #475569;
                border-radius: 8px;
                font-size: 14px;
                background: #334155;
                color: #f1f5f9;
            }
            QLineEdit:focus {
                border-color: #60a5fa;
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
                background-color: transparent;
                color: #60a5fa;
                padding: 12px;
                border: 2px solid #60a5fa;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #334155;
            }
            QPushButton:pressed {
                background-color: #475569;
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
        self.setStyleSheet("background-color: #1e293b;")
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
                color: #94a3b8;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                text-align: left;
                font-size: 15px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #e2e8f0;
            }
            QPushButton:checked {
                background-color: #1e3a5f;
                color: #60a5fa;
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
        title.setStyleSheet("color: #f1f5f9;")
        
        # Server status indicator
        self.status_indicator = QLabel("🔴 Stopped")
        self.status_indicator.setStyleSheet("""
            background-color: #422;
            color: #fca5a5;
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
                background-color: #334155;
                color: #64748b;
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
                background-color: #334155;
                color: #64748b;
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
                background-color: #0f172a;
                border: 2px solid #334155;
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
        qr_title.setStyleSheet("color: #f1f5f9; margin: 20px 0 10px 0;")
        
        qr_subtitle = QLabel("Open the mobile app and scan this code")
        qr_subtitle.setAlignment(Qt.AlignCenter)
        qr_subtitle.setStyleSheet("color: #94a3b8; margin-bottom: 20px; font-size: 14px;")
        
        self.qr_label = QLabel("Start server to display QR code")
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setMinimumSize(400, 400)
        self.qr_label.setStyleSheet("""
            background-color: #1e293b;
            border: 3px dashed #475569;
            border-radius: 12px;
            color: #64748b;
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
        self.setStyleSheet("background-color: #1e293b;")
        
        self.start_button.clicked.connect(self.start_server_requested.emit)
        self.stop_button.clicked.connect(self.stop_server_requested.emit)
    
    def set_qr(self, pixmap: QPixmap):
        self.qr_label.setStyleSheet("""
            background-color: #1e293b;
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
            background-color: #1e293b;
            border: 3px dashed #475569;
            border-radius: 12px;
            color: #64748b;
            font-style: italic;
            font-size: 14px;
        """)
    
    def set_connected(self, connected: bool):
        if connected:
            self.status_indicator.setText("🟢 Connected")
            self.status_indicator.setStyleSheet("""
                background-color: #14532d;
                color: #86efac;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            """)
        else:
            self.status_indicator.setText("🟡 Waiting for client...")
            self.status_indicator.setStyleSheet("""
                background-color: #422006;
                color: #fcd34d;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            """)
    
    def set_server_running(self, running: bool):
        if running:
            self.status_indicator.setText("🟡 Waiting for client...")
            self.status_indicator.setStyleSheet("""
                background-color: #422006;
                color: #fcd34d;
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
                background-color: #422;
                color: #fca5a5;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            """)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)


class _FetchInterviewAnalysisWorker(QThread):
    """Fetch interview logs and evaluations from S3, match by session_id."""
    data_loaded = Signal(list)  # list of {session_id, log_data, evaluation_data, last_modified}
    error_occurred = Signal(str)

    def __init__(self, s3_handler, username: str):
        super().__init__()
        self.s3_handler = s3_handler
        self.username = username

    def run(self):
        try:
            # Fetch logs (username/logfile/*.json)
            log_files = self.s3_handler.list_user_files(self.username, folder="logfile")
            logs_by_session = {}
            for f in log_files:
                key = f.get("key", "")
                if not key.endswith(".json") or ".evaluation." in key:
                    continue
                content = self.s3_handler.get_file_content(key)
                if not content:
                    continue
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    continue
                # session_id from key: .../interview_log_20260207_061821.json
                stem = key.split("/")[-1].replace(".json", "").replace("interview_log_", "")
                logs_by_session[stem] = {"data": data, "last_modified": f.get("last_modified")}

            # Fetch evaluations (username/evaluations/*.json)
            eval_files = self.s3_handler.list_user_files(self.username, folder="evaluations")
            evals_by_session = {}
            for f in eval_files:
                key = f.get("key", "")
                if not key.endswith(".json"):
                    continue
                content = self.s3_handler.get_file_content(key)
                if not content:
                    continue
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    continue
                stem = key.split("/")[-1].replace(".evaluation.json", "").replace("interview_log_", "")
                evals_by_session[stem] = {"data": data, "last_modified": f.get("last_modified")}

            # Combine: all sessions from logs, attach evaluation if present
            combined = []
            for session_id, log_item in logs_by_session.items():
                eval_item = evals_by_session.get(session_id)
                last_mod = log_item.get("last_modified") or eval_item.get("last_modified") if eval_item else log_item.get("last_modified")
                combined.append({
                    "session_id": session_id,
                    "log_data": log_item["data"],
                    "evaluation_data": eval_item["data"] if eval_item else None,
                    "last_modified": last_mod,
                })
            combined.sort(key=lambda x: x.get("last_modified") or "", reverse=True)
            self.data_loaded.emit(combined)
        except Exception as e:
            self.error_occurred.emit(str(e))


class SummaryView(QWidget):
    """Summary view: fetch interview logs + evaluations from S3, show analysis (no Q&A)."""

    def __init__(self):
        super().__init__()
        self.username = None
        self._fetch_worker = None
        try:
            from s3_handler import S3Handler
            self.s3_handler = S3Handler()
        except Exception:
            self.s3_handler = None
        self._setup_ui()

    def set_user(self, user_data):
        if user_data and isinstance(user_data, dict):
            self.username = user_data.get("username") or user_data.get("email", "").split("@")[0]
        else:
            self.username = None

    def _setup_ui(self):
        # Header
        header = QWidget()
        header_layout = QHBoxLayout()
        title = QLabel("Interview Summary")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #f1f5f9;")
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setMinimumHeight(40)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #e2e8f0;
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #475569; }
            QPushButton:disabled { background-color: #475569; color: #94a3b8; }
        """)
        self.refresh_btn.clicked.connect(self._on_refresh)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)
        header.setLayout(header_layout)

        # Stats
        stats_layout = QHBoxLayout()
        self.total_value_label = self._create_stat_card("📊 Total Interviews", "0", "#3b82f6", stats_layout)
        self.completed_value_label = self._create_stat_card("✅ With Analysis", "0", "#10b981", stats_layout)
        self.progress_value_label = self._create_stat_card("⏳ Logs Only", "0", "#f59e0b", stats_layout)

        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setVisible(False)

        # List area
        recent_section = QFrame()
        recent_section.setStyleSheet("""
            QFrame { background-color: #0f172a; border: 2px solid #334155; border-radius: 12px; }
        """)
        recent_layout = QVBoxLayout()
        recent_title = QLabel("Interview Analysis (from S3)")
        recent_title_font = QFont()
        recent_title_font.setPointSize(16)
        recent_title_font.setBold(True)
        recent_title.setFont(recent_title_font)
        recent_title.setStyleSheet("color: #f1f5f9; margin-bottom: 15px;")
        self.logs_scroll = QScrollArea()
        self.logs_scroll.setWidgetResizable(True)
        self.logs_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.logs_scroll.setStyleSheet("QScrollArea { border: none; background-color: #1e293b; border-radius: 8px; }")
        self.logs_container = QWidget()
        self.logs_layout = QVBoxLayout()
        self.logs_layout.setContentsMargins(12, 12, 12, 12)
        self.logs_layout.setSpacing(12)
        self.logs_container.setLayout(self.logs_layout)
        self.logs_scroll.setWidget(self.logs_container)
        self.empty_label = QLabel("No interviews yet.\nClick Refresh to load from S3.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #94a3b8; font-size: 14px; padding: 40px;")
        self.logs_layout.addWidget(self.empty_label)
        recent_layout.addWidget(recent_title)
        recent_layout.addWidget(self.loading_bar)
        recent_layout.addWidget(self.logs_scroll)
        recent_layout.setContentsMargins(20, 20, 20, 20)
        recent_section.setLayout(recent_layout)

        layout = QVBoxLayout()
        layout.addWidget(header)
        layout.addSpacing(20)
        layout.addLayout(stats_layout)
        layout.addSpacing(20)
        layout.addWidget(recent_section, 1)
        layout.setContentsMargins(40, 30, 40, 30)
        self.setLayout(layout)
        self.setStyleSheet("background-color: #1e293b;")

    def _create_stat_card(self, title: str, value: str, color: str, parent_layout: QHBoxLayout):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{ background-color: #0f172a; border-left: 4px solid {color}; border-radius: 8px; padding: 10px; }}
        """)
        layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 500;")
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
        parent_layout.addWidget(card)
        return value_label

    def _on_refresh(self):
        if not self.username:
            return
        if not self.s3_handler or not getattr(self.s3_handler, "s3_client", None):
            self._show_empty("S3 not configured. Set AWS credentials and S3_BUCKET_NAME in .env")
            return
        self.refresh_btn.setEnabled(False)
        self.loading_bar.setVisible(True)
        self._fetch_worker = _FetchInterviewAnalysisWorker(self.s3_handler, self.username)
        self._fetch_worker.data_loaded.connect(self._on_data_loaded)
        self._fetch_worker.error_occurred.connect(self._on_error)
        self._fetch_worker.finished.connect(self._on_fetch_finished)
        self._fetch_worker.start()

    def _on_data_loaded(self, combined: list):
        self.total_value_label.setText(str(len(combined)))
        with_eval = sum(1 for c in combined if c.get("evaluation_data"))
        self.completed_value_label.setText(str(with_eval))
        self.progress_value_label.setText(str(len(combined) - with_eval))

        while self.logs_layout.count():
            item = self.logs_layout.takeAt(0)
            w = item.widget()
            if w and w is not self.empty_label:
                w.deleteLater()
        if len(combined) == 0:
            self.empty_label.setText("No interview logs found in S3.")
            self.logs_layout.addWidget(self.empty_label)
            return
        for item in combined:
            card = self._build_analysis_card(item)
            self.logs_layout.addWidget(card)

    def _build_analysis_card(self, item: dict) -> QFrame:
        """One card per interview: session info + analysis (narrative only, no Q&A)."""
        log_data = item.get("log_data") or {}
        eval_data = item.get("evaluation_data")
        session_id = item.get("session_id", "—")
        meta = log_data.get("metadata") or {}
        role = meta.get("role", "—")
        difficulty = (meta.get("difficulty") or "—")
        qa_count = len(log_data.get("qa_pairs") or [])

        card = QFrame()
        card.setStyleSheet("""
            QFrame { background-color: #0f172a; border: 1px solid #334155; border-radius: 12px; padding: 0; }
            QFrame:hover { border-color: #475569; }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(18, 16, 18, 16)

        header = QLabel(f"📋 {session_id}  ·  {role}  ·  {difficulty}")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setStyleSheet("color: #f1f5f9;")
        layout.addWidget(header)

        # Analysis block (narrative only, no Q&A)
        analysis_parts = []
        if eval_data:
            fb = eval_data.get("final_feedback_for_candidate") or {}
            summary = fb.get("overall_summary", "").strip()
            if summary:
                analysis_parts.append(summary)
            top3 = fb.get("top_3_improvements") or []
            if top3:
                analysis_parts.append("Top improvements: " + "; ".join(top3))
            focus = fb.get("what_to_focus_on_next", "").strip()
            if focus:
                analysis_parts.append("Focus next: " + focus)
            hire = eval_data.get("hire_signal", "")
            if hire:
                analysis_parts.append(f"Hire signal: {hire}")
        # When no evaluation, derive analysis from the log file (topics + short answer summaries)
        if not analysis_parts:
            analysis_parts = self._analysis_from_log(log_data, role, difficulty, qa_count)

        analysis_text = "\n\n".join(analysis_parts)
        analysis_lbl = QLabel(analysis_text)
        analysis_lbl.setWordWrap(True)
        analysis_lbl.setStyleSheet("color: #cbd5e1; font-size: 13px; line-height: 1.4; margin-top: 8px; padding: 10px; background-color: #1e293b; border-radius: 8px;")
        layout.addWidget(analysis_lbl)
        card.setLayout(layout)
        return card

    def _analysis_from_log(self, log_data: dict, role: str, difficulty: str, qa_count: int) -> list:
        """Build analysis narrative from log file (topics + short answer summaries, no raw Q&A)."""
        parts = []
        qa_pairs = log_data.get("qa_pairs") or []
        if not qa_pairs:
            return [f"Interview for {role}, {difficulty}. No Q&A recorded in log."]
        # Topics covered (questions, truncated)
        topics = []
        for i, pair in enumerate(qa_pairs, 1):
            q = (pair.get("question") or "").strip()
            if q:
                topics.append(q if len(q) <= 55 else q[:52] + "...")
        if topics:
            parts.append("Topics covered: " + " | ".join(topics))
        # Short summary per exchange (question + brief answer glimpse, not full Q&A)
        summaries = []
        for i, pair in enumerate(qa_pairs, 1):
            q = (pair.get("question") or "").strip()
            a = (pair.get("answer") or "").strip()
            q_short = q if len(q) <= 45 else q[:42] + "..."
            a_short = (a[:100] + "...") if len(a) > 100 else a
            if q_short or a_short:
                summaries.append(f"• {q_short}: {a_short}")
        if summaries:
            parts.append("Discussion summary:\n" + "\n".join(summaries))
        if not parts:
            parts.append(f"Interview for {role}, {difficulty}. {qa_count} questions discussed.")
        return parts

    def _on_error(self, message: str):
        self._show_empty(f"Error loading from S3: {message}")

    def _on_fetch_finished(self):
        self.refresh_btn.setEnabled(True)
        self.loading_bar.setVisible(False)
        self._fetch_worker = None

    def _show_empty(self, text: str):
        self.empty_label.setText(text)
        while self.logs_layout.count():
            item = self.logs_layout.takeAt(0)
            w = item.widget()
            if w and w is not self.empty_label:
                w.deleteLater()
        self.logs_layout.addWidget(self.empty_label)


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
                background-color: #0f172a;
                border-right: 2px solid #334155;
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
        app_title.setStyleSheet("color: #60a5fa; margin-bottom: 10px; padding: 10px;")
        
        # User info
        self.user_label = QLabel("👤 User")
        self.user_label.setStyleSheet("""
            color: #e2e8f0;
            padding: 12px;
            background-color: #1e293b;
            border-radius: 8px;
            font-weight: 600;
            font-size: 13px;
        """)
        self.user_label.setWordWrap(True)
        
        # Navigation buttons
        nav_label = QLabel("NAVIGATION")
        nav_label.setStyleSheet("""
            color: #64748b;
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
                background-color: #422;
                color: #fca5a5;
                border: 1px solid #7f1d1d;
                border-radius: 8px;
                padding: 12px;
                text-align: center;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #7f1d1d;
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
        self.content_stack.setStyleSheet("background-color: #1e293b;")
        
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
            self.summary_view.set_user(user_data)
        else:
            self.user_label.setText("👤 User")
            self.summary_view.set_user(None)


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
        
        # Apply window stylesheet: dark theme for login and dashboard consistency
        self.setStyleSheet("""
            QWidget {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background-color: #1e293b;
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