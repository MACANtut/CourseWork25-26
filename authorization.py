import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QMessageBox, 
                               QDialog, QGridLayout, QDateEdit, QComboBox)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from main_window import MainWindow
import config

connect_postgres = config.connect_postgres
hash_password = config.hash_password
create_tables = config.create_tables
check_tables_exist = config.check_tables_exist
register_user = config.register_user
authenticate_user = config.authenticate_user

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Авторизация")
        self.setFixedSize(500, 600)
        self.setStyleSheet("background-color: #ffffff;")
        
        self.init_ui()
        self.current_user = None
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title_label = QLabel("Магазин спортивных товаров")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin-bottom: 20px;")
        layout.addWidget(title_label)
        
        self.login_widget = QWidget()
        self.login_widget.setVisible(True)
        login_layout = QVBoxLayout(self.login_widget)
        login_layout.setSpacing(10)
        
        login_title = QLabel("Вход в систему")
        login_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        login_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        login_layout.addWidget(login_title)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Логин")
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #dee2e6;
                border-radius: 5px;
                font-size: 14px;
                background-color: white;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        login_layout.addWidget(self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #dee2e6;
                border-radius: 5px;
                font-size: 14px;
                background-color: white;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        login_layout.addWidget(self.password_input)
        
        login_button = QPushButton("Войти")
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        login_button.clicked.connect(self.login)
        login_layout.addWidget(login_button)
        
        register_button = QPushButton("Регистрация")
        register_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        register_button.clicked.connect(self.show_register)
        login_layout.addWidget(register_button)
        
        layout.addWidget(self.login_widget)
        
        self.register_widget = QWidget()
        self.register_widget.setVisible(False)
        register_layout = QVBoxLayout(self.register_widget)
        register_layout.setSpacing(8)
        
        register_title = QLabel("Регистрация")
        register_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        register_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        register_layout.addWidget(register_title)
        
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        labels = ["Имя:", "Фамилия:", "Отчество:", "Дата рождения:", "Email:", "Логин:", "Пароль:"]
        self.register_fields = {}
        
        for i, label_text in enumerate(labels):
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 14px; color: #2c3e50;")
            grid_layout.addWidget(label, i, 0)
            
            if label_text == "Дата рождения:":
                field = QDateEdit()
                field.setDate(QDate(2000, 1, 1))
                field.setCalendarPopup(True)
                field.setStyleSheet("""
                    QDateEdit {
                        padding: 8px;
                        border: 2px solid #dee2e6;
                        border-radius: 5px;
                        font-size: 14px;
                        background-color: white;
                        color: #2c3e50;
                    }
                    QDateEdit:focus {
                        border-color: #3498db;
                    }
                """)
                
                calendar = field.calendarWidget()
                calendar.setStyleSheet("""
                    QCalendarWidget QAbstractItemView:enabled {
                        color: #000000;
                    }
                    QCalendarWidget QAbstractItemView:disabled {
                        color: #cccccc;
                    }
                    QCalendarWidget QToolButton {
                        color: #000000;
                        font-size: 12px;
                    }
                    QCalendarWidget QSpinBox {
                        color: #000000;
                        font-size: 12px;
                    }
                    QCalendarWidget QMenu {
                        color: #000000;
                    }
                    QCalendarWidget QWidget {
                        alternate-background-color: #f8f9fa;
                    }
                    QCalendarWidget QTableView {
                        gridline-color: #dee2e6;
                    }
                    QCalendarWidget QToolButton#qt_calendar_monthbutton,
                    QCalendarWidget QToolButton#qt_calendar_yearbutton {
                        color: #000000;
                        font-weight: bold;
                    }
                    QCalendarWidget QToolButton::menu-indicator {
                        image: none;
                    }
                """)
                
            elif label_text == "Пароль:":
                field = QLineEdit()
                field.setEchoMode(QLineEdit.EchoMode.Password)
            else:
                field = QLineEdit()
            
            if isinstance(field, QLineEdit):
                field.setStyleSheet("""
                    QLineEdit {
                        padding: 8px;
                        border: 2px solid #dee2e6;
                        border-radius: 5px;
                        font-size: 14px;
                        background-color: white;
                        color: #2c3e50;
                    }
                    QLineEdit:focus {
                        border-color: #3498db;
                    }
                """)
            
            grid_layout.addWidget(field, i, 1)
            self.register_fields[label_text] = field
        
        register_layout.addLayout(grid_layout)
        
        buttons_layout = QHBoxLayout()
        
        back_button = QPushButton("Назад")
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        back_button.clicked.connect(self.show_login)
        buttons_layout.addWidget(back_button)
        
        submit_button = QPushButton("Зарегистрироваться")
        submit_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        submit_button.clicked.connect(self.register)
        buttons_layout.addWidget(submit_button)
        
        register_layout.addLayout(buttons_layout)
        
        layout.addWidget(self.register_widget)
    
    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return
        
        success, result = authenticate_user(username, password)
        
        if success:
            self.current_user = result
            
            is_first_user = self.check_if_first_user(result['user_id'])
            result['is_first_user'] = is_first_user
            
            QMessageBox.information(self, "Успех", f"Добро пожаловать, {result['first_name']}!")
            self.open_main_window()
        else:
            QMessageBox.warning(self, "Ошибка", result)
    
    def check_if_first_user(self, user_id):
        connection = connect_postgres()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            cursor.execute("SELECT MIN(user_id) FROM users")
            min_user_id = cursor.fetchone()[0]
            
            cursor.close()
            connection.close()
            
            return user_id == min_user_id
            
        except Exception:
            return False
    
    def show_register(self):
        self.login_widget.setVisible(False)
        self.register_widget.setVisible(True)
    
    def show_login(self):
        self.register_widget.setVisible(False)
        self.login_widget.setVisible(True)
    
    def register(self):
        user_data = {
            'first_name': self.register_fields["Имя:"].text().strip(),
            'last_name': self.register_fields["Фамилия:"].text().strip(),
            'patronymic': self.register_fields["Отчество:"].text().strip(),
            'birth_date': self.register_fields["Дата рождения:"].date().toString("yyyy-MM-dd"),
            'email': self.register_fields["Email:"].text().strip(),
            'username': self.register_fields["Логин:"].text().strip(),
            'password': self.register_fields["Пароль:"].text().strip()
        }
        
        required_fields = ['first_name', 'last_name', 'email', 'username', 'password']
        for field in required_fields:
            if not user_data[field]:
                QMessageBox.warning(self, "Ошибка", "Заполните все обязательные поля")
                return
        
        if '@' not in user_data['email'] or '.' not in user_data['email']:
            QMessageBox.warning(self, "Ошибка", "Введите корректный email адрес")
            return
        
        success, message = register_user(user_data)
        
        if success:
            QMessageBox.information(self, "Успех", message)
            self.show_login()
            self.username_input.setText(user_data['username'])
        else:
            QMessageBox.warning(self, "Ошибка", message)
    
    def open_main_window(self):
        self.main_window = MainWindow(
            username=self.username_input.text(),
            user_id=self.current_user['user_id'],
            current_user=self.current_user
        )
        self.main_window.show()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())