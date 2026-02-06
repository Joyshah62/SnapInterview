from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout
)
from PySide6.QtCore import Signal

class LoginWindow(QWidget):
    login_successful = Signal(dict)  # emits user row dict on login/signup success

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SnapInterview Login")
        self.setFixedSize(350, 250)

        # Email
        self.email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")

        # Password
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)

        # Buttons
        self.login_button = QPushButton("Login")
        self.signup_button = QPushButton("Sign Up")

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.login_button)
        btn_layout.addWidget(self.signup_button)

        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red")

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addLayout(btn_layout)
        layout.addWidget(self.status_label)
        layout.addStretch()
        self.setLayout(layout)

    def set_status(self, text):
        self.status_label.setText(text)
