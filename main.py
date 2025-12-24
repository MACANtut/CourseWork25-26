import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from authorization import LoginWindow
import config

def check_and_init_database():
    if not config.connect_postgres():
        QMessageBox.critical(None, "Ошибка", 
            "Не удалось подключиться к базе данных.\n"
            "Проверьте подключение к интернету и настройки базы данных.")
        return False
    
    if not config.check_tables_exist():
        if not config.create_tables():
            QMessageBox.warning(None, "Предупреждение",
                "Не удалось создать таблицы в базе данных.\n"
                "Приложение будет работать в ограниченном режиме.")
            return False
    
    return True

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QMainWindow { 
            background-color: #ffffff; 
        }
        QMessageBox {
            background-color: #ffffff;
        }
        QMessageBox QLabel {
            color: #2c3e50;
            font-size: 14px;
        }
        QMessageBox QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: bold;
        }
        QMessageBox QPushButton:hover {
            background-color: #2980b9;
        }
    """)
    
    if os.path.exists("C:/Users/lolko/OneDrive/Рабочий стол/3 курс/Прога/image/icon.ico"):
        app.setWindowIcon(QIcon("C:/Users/lolko/OneDrive/Рабочий стол/3 курс/Прога/image/icon.ico"))
    
    if not check_and_init_database():
        reply = QMessageBox.question(None, "База данных недоступна",
            "Не удалось подключиться к базе данных.\n"
            "Хотите продолжить работу в автономном режиме?\n"
            "Некоторые функции будут недоступны.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.No:
            sys.exit(1)
    
    login_window = LoginWindow()
    login_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()