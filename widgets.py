import sys
import os
import hashlib
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QFrame, QPushButton, QLineEdit, 
                               QGridLayout, QScrollArea, QDialog, 
                               QListWidget, QListWidgetItem, QComboBox, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QStackedWidget, QDateEdit, QMessageBox, QCheckBox)
from PySide6.QtCore import Qt, QTimer, QDate, QUrl, QSize, QObject, Signal, Slot
from PySide6.QtGui import QColor, QPainter, QFont, QPixmap, QIcon, QPainterPath
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtCharts import QChart, QChartView, QBarSet, QBarSeries, QBarCategoryAxis, QValueAxis
import config
from filters import ProductFilter


class CategoryConfirmationDialog(QDialog):
    def __init__(self, category_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор категории")
        self.setFixedSize(400, 200)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        message_label = QLabel(f"Вы выбрали категорию:\n<b>{category_name}</b>")
        message_label.setStyleSheet("font-size: 16px; color: #495057;")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setSpacing(15)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.setFixedHeight(40)
        self.ok_button.setStyleSheet("QPushButton { background-color: #3498db; color: white; border: none; border-radius: 5px; font-size: 14px; font-weight: bold; } QPushButton:hover { background-color: #2980b9; }")
        self.ok_button.clicked.connect(self.accept)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addStretch()
        
        layout.addWidget(buttons_container)


class ImageLoader(QObject):
    image_loaded = Signal(str, QPixmap)
    
    def __init__(self):
        super().__init__()
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self._on_image_downloaded)
        self.cache_dir = Path("image_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.pending_requests = {}
        
    def load_image(self, url, target_widget=None, default_icon=None):
        if not url or not url.strip():
            return self._get_default_icon(default_icon)
        
        if not url.startswith(('http://', 'https://')):
            if os.path.exists(url):
                pixmap = QPixmap(url)
                if not pixmap.isNull():
                    pixmap = self._scale_pixmap(pixmap, QSize(120, 120))
                    return pixmap
            return self._get_default_icon(default_icon)
        
        cached_path = self._get_cached_path(url)
        if cached_path.exists():
            pixmap = QPixmap(str(cached_path))
            if not pixmap.isNull():
                pixmap = self._scale_pixmap(pixmap, QSize(120, 120))
                return pixmap
        
        if target_widget:
            request = QNetworkRequest(QUrl(url))
            request.setRawHeader(b"User-Agent", b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            request.setAttribute(QNetworkRequest.Attribute.CacheLoadControlAttribute, 
                                 QNetworkRequest.CacheLoadControl.AlwaysNetwork)
            
            request_id = id(request)
            self.pending_requests[request_id] = {
                'url': url,
                'target': target_widget,
                'default': default_icon
            }
            
            reply = self.network_manager.get(request)
            reply.setProperty('request_id', request_id)
            
        return self._get_default_icon(default_icon)
    
    @Slot(QNetworkReply)
    def _on_image_downloaded(self, reply):
        request_id = reply.property('request_id')
        request_info = self.pending_requests.get(request_id)
        
        if not request_info:
            reply.deleteLater()
            return
        
        try:
            error = reply.error()
            if error != QNetworkReply.NetworkError.NoError:
                pixmap = self._get_default_icon(request_info['default'])
            else:
                data = reply.readAll()
                if data.isEmpty():
                    pixmap = self._get_default_icon(request_info['default'])
                else:
                    cached_path = self._get_cached_path(request_info['url'])
                    with open(cached_path, 'wb') as f:
                        f.write(data.data())
                    
                    pixmap = QPixmap()
                    if pixmap.loadFromData(data):
                        pixmap = self._scale_pixmap(pixmap, QSize(120, 120))
                    else:
                        pixmap = self._get_default_icon(request_info['default'])
            
            if request_info['target']:
                if isinstance(request_info['target'], QLabel):
                    request_info['target'].setPixmap(pixmap)
                elif hasattr(request_info['target'], 'set_icon'):
                    request_info['target'].set_icon(pixmap)
            
            self.image_loaded.emit(request_info['url'], pixmap)
            
        except Exception:
            pass
        finally:
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
            reply.deleteLater()
    
    def _get_cached_path(self, url):
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.png"
    
    def _scale_pixmap(self, pixmap, size):
        return pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, 
                            Qt.TransformationMode.SmoothTransformation)
    
    def _get_default_icon(self, icon_type=None):
        size = QSize(120, 120)
        pixmap = QPixmap(size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if icon_type == 'brand':
            painter.setBrush(QColor("#3498db"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(10, 10, 100, 100)
            
            painter.setPen(QColor("white"))
            painter.setFont(QFont("Arial", 32, QFont.Weight.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "B")
        else:
            painter.setBrush(QColor("#f8f9fa"))
            painter.setPen(QColor("#dee2e6"))
            painter.drawRect(10, 10, 100, 100)
            
            painter.setPen(QColor("#95a5a6"))
            painter.setFont(QFont("Arial", 32))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "📦")
        
        painter.end()
        return pixmap


image_loader = ImageLoader()


class CartItemWidget(QWidget):
    def __init__(self, product_id, article, product_name, price, quantity=1, user_id=None, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.article = article
        self.product_name = product_name
        self.price = float(price) if price else 0
        self.quantity = quantity
        self.user_id = user_id
        
        self.setFixedHeight(50)
        self.setStyleSheet("""
            CartItemWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                margin: 2px 0;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 5, 15, 5)
        
        name_label = QLabel(product_name)
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057; padding: 5px;")
        name_label.setMinimumWidth(150)
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        article_label = QLabel(f"Арт: {article}")
        article_label.setFixedWidth(100)
        article_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        article_label.setStyleSheet("font-size: 12px; color: #6c757d; padding: 2px;")
        layout.addWidget(article_label)
        
        price_label = QLabel(f"{self.price:.2f} руб.")
        price_label.setFixedWidth(80)
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_label.setStyleSheet("font-size: 14px; color: #495057; padding: 2px;")
        layout.addWidget(price_label)
        
        self.quantity_label = QLabel(str(quantity))
        self.quantity_label.setFixedWidth(30)
        self.quantity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quantity_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057; background-color: white; border: 1px solid #dee2e6; border-radius: 3px; padding: 2px;")
        
        minus_btn = QPushButton("-")
        minus_btn.setFixedSize(25, 25)
        minus_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; border: none; border-radius: 3px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #2980b9; }")
        minus_btn.clicked.connect(self.decrease_quantity)
        
        plus_btn = QPushButton("+")
        plus_btn.setFixedSize(25, 25)
        plus_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; border: none; border-radius: 3px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #2980b9; }")
        plus_btn.clicked.connect(self.increase_quantity)
        
        self.total_label = QLabel(f"{self.price * quantity:.2f} руб.")
        self.total_label.setFixedWidth(100)
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.total_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2ecc71; padding: 2px;")
        layout.addWidget(self.total_label)
        
        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(25, 25)
        delete_btn.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; border: none; border-radius: 3px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #c0392b; }")
        delete_btn.clicked.connect(self.delete_item)
        
        layout.addWidget(minus_btn)
        layout.addWidget(self.quantity_label)
        layout.addWidget(plus_btn)
        layout.addSpacing(10)
        layout.addWidget(delete_btn)
    
    def increase_quantity(self):
        self.quantity += 1
        self.quantity_label.setText(str(self.quantity))
        self.total_label.setText(f"{self.price * self.quantity:.2f} руб.")
        
        if self.user_id:
            config.update_cart_item(self.user_id, self.article, self.quantity)
        
        self.update_cart_total()
    
    def decrease_quantity(self):
        if self.quantity > 1:
            self.quantity -= 1
            self.quantity_label.setText(str(self.quantity))
            self.total_label.setText(f"{self.price * self.quantity:.2f} руб.")
            
            if self.user_id:
                config.update_cart_item(self.user_id, self.article, self.quantity)
            
            self.update_cart_total()
        else:
            self.delete_item()
    
    def delete_item(self):
        if self.user_id:
            config.remove_from_cart(self.user_id, self.article)
        
        self.setParent(None)
        self.deleteLater()
        self.update_cart_total()
    
    def update_cart_total(self):
        parent = self.parent()
        while parent and not hasattr(parent, 'update_cart_total'):
            parent = parent.parent()
        
        if parent and hasattr(parent, 'update_cart_total'):
            parent.update_cart_total()
    
    def get_total_price(self):
        return self.price * self.quantity


class DeleteProductDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Удаление товара")
        self.setFixedSize(400, 150)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 25, 30, 25)
        
        message_label = QLabel("Вы действительно хотите удалить товар?")
        message_label.setStyleSheet("font-size: 16px; color: #495057;")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message_label)
        
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setSpacing(15)
        
        self.cancel_button = QPushButton("Отменить")
        self.cancel_button.setFixedHeight(40)
        self.cancel_button.setStyleSheet("QPushButton { background-color: #95a5a6; color: white; border: none; border-radius: 5px; font-size: 14px; font-weight: bold; } QPushButton:hover { background-color: #7f8c8d; }")
        self.cancel_button.clicked.connect(self.reject)
        
        self.confirm_button = QPushButton("Подтвердить")
        self.confirm_button.setFixedHeight(40)
        self.confirm_button.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; border: none; border-radius: 5px; font-size: 14px; font-weight: bold; } QPushButton:hover { background-color: #c0392b; }")
        self.confirm_button.clicked.connect(self.accept)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.confirm_button)
        
        layout.addWidget(buttons_container)


class PeriodSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор периода (только для администратора)")
        self.setFixedSize(500, 400)
        self.setModal(True)
        self.setStyleSheet("background-color: white; color: #000000;")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title_label = QLabel("Выберите период")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        dates_widget = QWidget()
        dates_widget.setStyleSheet("background-color: white; color: #000000;")
        dates_layout = QVBoxLayout(dates_widget)
        dates_layout.setSpacing(15)
        
        start_date_widget = QWidget()
        start_date_widget.setStyleSheet("background-color: white; color: #000000;")
        start_date_layout = QVBoxLayout(start_date_widget)
        
        start_label = QLabel("Дата начала:")
        start_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        start_date_layout.addWidget(start_label)
        
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setFixedHeight(45)
        self.start_date_edit.setStyleSheet("""
            QDateEdit { 
                background-color: white; 
                border: 2px solid #dee2e6; 
                border-radius: 6px; 
                padding: 0 15px; 
                font-size: 14px; 
                color: #000000;
            } 
            QDateEdit:focus { 
                border-color: #3498db; 
            }
        """)
        start_date_layout.addWidget(self.start_date_edit)
        
        end_date_widget = QWidget()
        end_date_widget.setStyleSheet("background-color: white; color: #000000;")
        end_date_layout = QVBoxLayout(end_date_widget)
        
        end_label = QLabel("Дата окончания:")
        end_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        end_date_layout.addWidget(end_label)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setFixedHeight(45)
        self.end_date_edit.setStyleSheet("""
            QDateEdit { 
                background-color: white; 
                border: 2px solid #dee2e6; 
                border-radius: 6px; 
                padding: 0 15px; 
                font-size: 14px; 
                color: #000000;
            } 
            QDateEdit:focus { 
                border-color: #3498db; 
            }
        """)
        end_date_layout.addWidget(self.end_date_edit)
        
        dates_layout.addWidget(start_date_widget)
        dates_layout.addWidget(end_date_widget)
        
        layout.addWidget(dates_widget)
        
        buttons_container = QWidget()
        buttons_container.setStyleSheet("background-color: white; color: #000000;")
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setSpacing(15)
        
        self.cancel_button = QPushButton("Отменить")
        self.cancel_button.setFixedHeight(45)
        self.cancel_button.setStyleSheet("""
            QPushButton { 
                background-color: #95a5a6; 
                color: #000000; 
                border: none; 
                border-radius: 8px; 
                font-size: 16px; 
                font-weight: bold; 
            } 
            QPushButton:hover { 
                background-color: #7f8c8d; 
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        
        self.confirm_button = QPushButton("Применить")
        self.confirm_button.setFixedHeight(45)
        self.confirm_button.setStyleSheet("""
            QPushButton { 
                background-color: #3498db; 
                color: #000000; 
                border: none; 
                border-radius: 8px; 
                font-size: 16px; 
                font-weight: bold; 
            } 
            QPushButton:hover { 
                background-color: #2980b9; 
            }
        """)
        self.confirm_button.clicked.connect(self.accept)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.confirm_button)
        
        layout.addWidget(buttons_container)
    
    def get_period(self):
        return self.start_date_edit.date(), self.end_date_edit.date()


class AddProductDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить товар")
        self.setFixedSize(600, 850)
        self.setModal(True)
        self.setStyleSheet("""
            background-color: white;
            color: #000000;
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        title_label = QLabel("Добавление нового товара")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        brand_names = [""]
        try:
            brands_from_db = config.get_all_brands()
            brand_names += [brand['name'] for brand in brands_from_db]
        except Exception:
            pass
        
        fields_data = [
            ("Название товара", "QLineEdit"),
            ("Цена", "QLineEdit"),
            ("Артикул", "QLineEdit"),
            ("Бренд", "QComboBox", brand_names),
            ("Категория", "QComboBox"),
            ("Материал", "QLineEdit"),
            ("Цвет", "QLineEdit"),
            ("Размер", "QLineEdit"),
            ("Страна производитель", "QLineEdit"),
            ("Пол", "QComboBox"),
            ("Сезон", "QComboBox"),
            ("Ссылка на изображение", "QLineEdit")
        ]
        
        self.fields = {}
        
        for field_info in fields_data:
            if len(field_info) == 3:
                field_name, field_type, items = field_info
                field_widget = self.create_field_widget(field_name, field_type, items)
            else:
                field_name, field_type = field_info
                field_widget = self.create_field_widget(field_name, field_type)
            self.fields[field_name] = field_widget
            layout.addWidget(field_widget)
        
        layout.addStretch()
        
        buttons_container = QWidget()
        buttons_container.setStyleSheet("background-color: white; color: #000000;")
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(0)
        
        self.cancel_button = QPushButton("Отменить")
        self.cancel_button.setFixedHeight(40)
        self.cancel_button.setFixedWidth(120)
        self.cancel_button.setStyleSheet("""
            QPushButton { 
                background-color: #95a5a6; 
                color: #000000; 
                border: none; 
                border-radius: 6px; 
                font-size: 14px; 
                font-weight: bold; 
            } 
            QPushButton:hover { 
                background-color: #7f8c8d; 
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        
        self.add_button = QPushButton("Добавить")
        self.add_button.setFixedHeight(40)
        self.add_button.setFixedWidth(120)
        self.add_button.setStyleSheet("""
            QPushButton { 
                background-color: #3498db; 
                color: #000000; 
                border: none; 
                border-radius: 6px; 
                font-size: 14px; 
                font-weight: bold; 
            } 
            QPushButton:hover { 
                background-color: #2980b9; 
            }
        """)
        self.add_button.clicked.connect(self.on_add_clicked)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.add_button)
        
        layout.addWidget(buttons_container)
    
    def create_field_widget(self, field_name, field_type, items=None):
        widget = QWidget()
        widget.setStyleSheet("background-color: white; color: #000000;")
        widget.setMinimumHeight(75)
        layout = QVBoxLayout(widget)
        layout.setSpacing(5)
        
        label = QLabel(field_name + ":")
        label.setStyleSheet("font-size: 13px; font-weight: bold; color: #495057;")
        layout.addWidget(label)
        
        if field_type == "QLineEdit":
            input_field = QLineEdit()
            input_field.setFixedHeight(40)
            input_field.setStyleSheet("""
                QLineEdit { 
                    background-color: white; 
                    border: 1px solid #dee2e6; 
                    border-radius: 4px; 
                    padding: 8px 10px; 
                    font-size: 14px; 
                    color: #000000; 
                } 
                QLineEdit:focus { 
                    border-color: #3498db; 
                }
            """)
            if field_name == "Ссылка на изображение":
                input_field.setPlaceholderText("https://example.com/image.jpg")
        elif field_type == "QComboBox":
            input_field = QComboBox()
            input_field.setFixedHeight(40)
            input_field.setStyleSheet("""
                QComboBox { 
                    background-color: white; 
                    border: 1px solid #dee2e6; 
                    border-radius: 4px; 
                    padding: 6px 10px; 
                    font-size: 14px; 
                    color: #000000; 
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    color: #000000;
                    selection-background-color: #3498db;
                    selection-color: white;
                }
            """)
            if items:
                input_field.addItems(items)
            elif field_name == "Категория":
                input_field.addItems(["", "Аксессуары и дополнения", "Зимние виды спорта", "Водные виды спорта", "Велоспорт", "Единоборства и бокс", "Спортивный инвентарь", "Тренажеры и фитнес", "Одежда и обувь"])
            elif field_name == "Пол":
                input_field.addItems(["", "Мужской", "Женский", "Унисекс"])
            elif field_name == "Сезон":
                input_field.addItems(["", "Весна", "Лето", "Осень", "Зима", "Всесезонный"])
        
        layout.addWidget(input_field)
        return widget
    
    def on_add_clicked(self):
        product_data = {}
        for field_name, field_widget in self.fields.items():
            input_field = field_widget.layout().itemAt(1).widget()
            if isinstance(input_field, QLineEdit):
                product_data[field_name] = input_field.text()
            elif isinstance(input_field, QComboBox):
                product_data[field_name] = input_field.currentText()
        
        required_fields = ["Название товара", "Цена", "Артикул"]
        for field_name in required_fields:
            if not product_data.get(field_name, '').strip():
                QMessageBox.warning(self, "Ошибка", f"Поле '{field_name}' обязательно для заполнения")
                return
        
        db_product_data = {
            'name': product_data['Название товара'],
            'price': product_data['Цена'],
            'article': product_data['Артикул'],
            'brand': product_data.get('Бренд', ''),
            'category': product_data.get('Категория', ''),
            'material': product_data.get('Материал', ''),
            'color': product_data.get('Цвет', ''),
            'size': product_data.get('Размер', ''),
            'country': product_data.get('Страна производитель', ''),
            'gender': product_data.get('Пол', ''),
            'season': product_data.get('Сезон', ''),
            'image_url': product_data.get('Ссылка на изображение', '')
        }
        
        success, result = config.add_product(db_product_data)
        
        if success:
            QMessageBox.information(self, "Успех", f"Товар '{product_data['Название товара']}' успешно добавлен!")
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", result)


class ProductDetailWidget(QWidget):
    def __init__(self, product_data, main_window=None, parent=None):
        super().__init__(parent)
        self.product_data = product_data
        self.main_window = main_window
        
        self.setStyleSheet("background-color: white; color: #000000;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 20, 30, 20)
        
        title_label = QLabel("Детали товара")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: white; color: #000000;")
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(30)
        
        image_container = QWidget()
        image_container.setStyleSheet("background-color: white; color: #000000;")
        image_layout = QVBoxLayout(image_container)
        image_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        image_title = QLabel("Изображение товара")
        image_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057; margin-bottom: 10px;")
        image_layout.addWidget(image_title)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(300, 300)
        self.image_label.setStyleSheet("border: 1px solid #dee2e6; border-radius: 10px; background-color: #f8f9fa;")
        
        if product_data.get('image_url'):
            pixmap = image_loader.load_image(
                product_data['image_url'],
                self.image_label,
                'product'
            )
            self.image_label.setPixmap(pixmap.scaled(280, 280, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            pixmap = image_loader._get_default_icon('product')
            self.image_label.setPixmap(pixmap.scaled(280, 280, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        image_layout.addWidget(self.image_label)
        
        info_container = QWidget()
        info_container.setStyleSheet("background-color: white; color: #000000;")
        info_layout = QVBoxLayout(info_container)
        
        product_name_label = QLabel(product_data.get('name', 'Название товара'))
        product_name_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50; margin-bottom: 20px;")
        info_layout.addWidget(product_name_label)
        
        info_widget = QWidget()
        info_widget.setStyleSheet("background-color: white; color: #000000;")
        info_widget_layout = QVBoxLayout(info_widget)
        info_widget_layout.setSpacing(12)
        
        fields = [
            ("Цена", f"{product_data.get('price', '0')} руб."),
            ("Артикул", product_data.get('article', 'Не указан')),
            ("Бренд", product_data.get('brand', 'Не указан')),
            ("Категория", product_data.get('category', 'Не указана')),
            ("Материал", product_data.get('material', 'Не указан')),
            ("Цвет", product_data.get('color', 'Не указан')),
            ("Пол", product_data.get('gender', 'Не указан')),
            ("Размер", product_data.get('size', 'Не указан')),
            ("Сезон", product_data.get('season', 'Не указан')),
            ("Страна производитель", product_data.get('country', 'Не указана'))
        ]
        
        for field_name, field_value in fields:
            field_widget = self.create_info_field(field_name, field_value)
            info_widget_layout.addWidget(field_widget)
        
        info_layout.addWidget(info_widget)
        info_layout.addStretch()
        
        content_layout.addWidget(image_container, 40)
        content_layout.addWidget(info_container, 60)
        
        main_layout.addWidget(content_widget, 1)
        
        buttons_widget = QWidget()
        buttons_widget.setStyleSheet("background-color: white; color: #000000;")
        buttons_layout = QHBoxLayout(buttons_widget)
        
        if main_window and not main_window.current_user.get('is_first_user', False):
            add_to_cart_button = QPushButton("В корзину")
            add_to_cart_button.setFixedHeight(45)
            add_to_cart_button.setStyleSheet("QPushButton { background-color: #2ecc71; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #27ae60; }")
            add_to_cart_button.clicked.connect(self.add_to_cart)
            buttons_layout.addWidget(add_to_cart_button)
        
        if main_window and main_window.current_user.get('is_first_user', False):
            delete_button = QPushButton("Удалить товар")
            delete_button.setFixedHeight(45)
            delete_button.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #c0392b; }")
            delete_button.clicked.connect(self.show_delete_confirmation)
            buttons_layout.addWidget(delete_button)
        
        buttons_layout.addStretch()
        
        back_button = QPushButton("Назад")
        back_button.setFixedHeight(45)
        back_button.setStyleSheet("QPushButton { background-color: #95a5a6; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #7f8c8d; }")
        back_button.clicked.connect(self.go_back)
        buttons_layout.addWidget(back_button)
        
        main_layout.addWidget(buttons_widget)
    
    def create_info_field(self, field_name, field_value):
        field_widget = QWidget()
        field_widget.setStyleSheet("background-color: white; color: #000000;")
        field_layout = QHBoxLayout(field_widget)
        field_layout.setContentsMargins(0, 0, 0, 0)
        
        name_label = QLabel(f"{field_name}:")
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057; min-width: 200px;")
        
        value_label = QLabel(field_value)
        value_label.setStyleSheet("font-size: 16px; color: #6c757d;")
        value_label.setWordWrap(True)
        
        field_layout.addWidget(name_label)
        field_layout.addWidget(value_label)
        field_layout.addStretch()
        
        return field_widget
    
    def add_to_cart(self):
        if self.main_window and self.main_window.current_user.get('is_first_user', False):
            QMessageBox.information(self, "Информация", 
                "Функция корзины недоступна для администратора.\n\n"
                "Пожалуйста, зарегистрируйте нового пользователя для использования корзины.")
            return
        
        if self.main_window:
            self.main_window.add_to_cart(
                self.product_data['id'],
                self.product_data['name'],
                self.product_data.get('price', '0')
            )
            QMessageBox.information(self, "Корзина", f"Товар '{self.product_data['name']}' добавлен в корзину!")
    
    def go_back(self):
        if self.main_window:
            self.main_window.show_products()
    
    def show_delete_confirmation(self):
        dialog = DeleteProductDialog(self)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            success, message = config.delete_product(self.product_data['id'])
            if success:
                QMessageBox.information(self, "Успех", message)
                # Обновляем список товаров в главном окне
                if self.main_window:
                    self.main_window.load_products_from_db()
                self.go_back()  # Возвращаемся к списку товаров
            else:
                QMessageBox.warning(self, "Ошибка", message)

class BrandCard(QFrame):
    def __init__(self, brand_data, is_first_user=True, parent=None):
        super().__init__(parent)
        self.brand_data = brand_data
        self.is_selected = False
        self.setMinimumSize(150, 200)
        self.setStyleSheet("""
            BrandCard {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                margin: 5px;
            }
            BrandCard:hover {
                border-color: #3498db;
                background-color: #e9ecef;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(80, 80)
        
        if brand_data.get('image_url'):
            pixmap = image_loader.load_image(
                brand_data['image_url'], 
                self.icon_label,
                'brand'
            )
            self.icon_label.setPixmap(pixmap)
        else:
            pixmap = image_loader._get_default_icon('brand')
            self.icon_label.setPixmap(pixmap)
        
        layout.addWidget(self.icon_label)
        
        self.name_label = QLabel(brand_data.get('name', 'Название'))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057; margin-top: 5px;")
        layout.addWidget(self.name_label)
        
        self.selection_indicator = QLabel("")
        self.selection_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.selection_indicator.setStyleSheet("font-size: 12px; color: #27ae60; font-weight: bold;")
        layout.addWidget(self.selection_indicator)
        
        self.selection_button = QPushButton("Выбрать")
        self.selection_button.setFixedSize(80, 25)
        self.selection_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.selection_button.clicked.connect(self.toggle_selection)
        layout.addWidget(self.selection_button, 0, Qt.AlignmentFlag.AlignCenter)
    
    def toggle_selection(self):
        self.is_selected = not self.is_selected
        self.update_appearance()
    
    def update_appearance(self):
        if self.is_selected:
            self.setStyleSheet("""
                BrandCard {
                    background-color: #e3f2fd;
                    border: 2px solid #3498db;
                    border-radius: 10px;
                    margin: 5px;
                }
                BrandCard:hover {
                    border-color: #2980b9;
                    background-color: #bbdefb;
                }
            """)
            self.selection_button.setText("Отменить")
            self.selection_button.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            self.selection_indicator.setText("✓ Выбран")
        else:
            self.setStyleSheet("""
                BrandCard {
                    background-color: #f8f9fa;
                    border: 2px solid #dee2e6;
                    border-radius: 10px;
                    margin: 5px;
                }
                BrandCard:hover {
                    border-color: #3498db;
                    background-color: #e9ecef;
                }
            """)
            self.selection_button.setText("Выбрать")
            self.selection_button.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            self.selection_indicator.setText("")


class ProductCard(QFrame):
    def __init__(self, product_data, main_window=None, parent=None):
        super().__init__(parent)
        self.product_data = product_data
        self.main_window = main_window
        self.setMinimumSize(180, 220)
        self.setStyleSheet("""
            ProductCard {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                margin: 5px;
            }
            ProductCard:hover {
                border-color: #3498db;
                background-color: #e9ecef;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(120, 120)
        self.image_label.setStyleSheet("border: 1px solid #dee2e6; border-radius: 5px;")
        
        if product_data.get('image_url'):
            pixmap = image_loader.load_image(
                product_data['image_url'],
                self.image_label,
                'product'
            )
            self.image_label.setPixmap(pixmap)
        else:
            pixmap = image_loader._get_default_icon('product')
            self.image_label.setPixmap(pixmap)
        
        layout.addWidget(self.image_label)
        
        name_label = QLabel(product_data.get('name', 'Товар'))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        name_label.setWordWrap(True)
        name_label.setMaximumWidth(160)
        layout.addWidget(name_label)
        
        price_label = QLabel(f"{product_data.get('price', '0')} руб.")
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_label.setStyleSheet("font-size: 12px; color: #2ecc71; font-weight: bold;")
        layout.addWidget(price_label)
        
        details_button = QPushButton("О товаре")
        details_button.setFixedHeight(30)
        details_button.setStyleSheet("QPushButton { background-color: #3498db; color: white; border: none; border-radius: 5px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #2980b9; }")
        details_button.clicked.connect(self.show_product_details)
        layout.addWidget(details_button)
    
    def show_product_details(self):
        if self.main_window:
            self.main_window.show_product_details(self.product_data)


class CategoryDropdown(QWidget):
    def __init__(self, categories, parent=None):
        super().__init__(parent)
        self.categories = categories
        self.setVisible(False)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet("""
            CategoryDropdown {
                background-color: white;
                border: 2px solid #3498db;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)
        
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: none;
                outline: none;
                font-size: 14px;
                color: #000000;
                border-radius: 6px;
            }
            QListWidget::item {
                padding: 10px 15px;
                border-bottom: 1px solid #f8f9fa;
                color: #000000;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
                border-radius: 4px;
            }
            QListWidget::item:hover:!selected {
                background-color: #e9ecef;
                color: #000000;
                border-radius: 4px;
            }
        """)
        
        all_categories_item = QListWidgetItem("Все категории")
        all_categories_item.setData(Qt.ItemDataRole.UserRole, "")
        self.list_widget.addItem(all_categories_item)
        
        for category in self.categories:
            item = QListWidgetItem(category)
            item.setData(Qt.ItemDataRole.UserRole, category)
            self.list_widget.addItem(item)
        
        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.list_widget)
        self.setFixedWidth(250)
        self.setFixedHeight(300)
    
    def on_selection_changed(self):
        selected_items = self.list_widget.selectedItems()
        
        all_categories_selected = False
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.text() == "Все категории" and item.isSelected():
                all_categories_selected = True
                for j in range(self.list_widget.count()):
                    other_item = self.list_widget.item(j)
                    if other_item.text() != "Все категории":
                        other_item.setSelected(False)
                break
        
        if not all_categories_selected:
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.text() == "Все категории" and item.isSelected():
                    item.setSelected(False)
                    break
        
        self.hide_dropdown()
        
        selected_categories = []
        for item in selected_items:
            category_value = item.data(Qt.ItemDataRole.UserRole)
            selected_categories.append(category_value)
        
        main_window = self.parent()
        if hasattr(main_window, 'on_categories_selected'):
            main_window.on_categories_selected(selected_categories)
    
    def show_dropdown(self):
        self.setVisible(True)
        self.raise_()
        self.sync_selection()
        
    def hide_dropdown(self):
        self.setVisible(False)
    
    def sync_selection(self):
        self.list_widget.clearSelection()
        
        main_window = self.parent()
        if not main_window or not hasattr(main_window, 'product_filter'):
            return
        
        current_filter = main_window.product_filter
        
        if not current_filter.selected_categories:
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.text() == "Все категории":
                    item.setSelected(True)
                    break
        else:
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                category_value = item.data(Qt.ItemDataRole.UserRole)
                if category_value in current_filter.selected_categories:
                    item.setSelected(True)
    
    def mousePressEvent(self, event):
        global_pos = event.globalPosition().toPoint()
        if not self.geometry().contains(global_pos):
            self.hide_dropdown()
        super().mousePressEvent(event)


class AddBrandDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить бренд")
        self.setFixedSize(750, 400)
        self.setModal(True)
        self.setStyleSheet("background-color: white; color: #000000;")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title_label = QLabel("Добавление нового бренда")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        form_widget = QWidget()
        form_widget.setStyleSheet("background-color: white; color: #000000;")
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(15)
        
        name_widget = QWidget()
        name_widget.setStyleSheet("background-color: white; color: #000000;")
        name_layout = QVBoxLayout(name_widget)
        
        name_label = QLabel("Название бренда:")
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        name_layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setFixedHeight(45)
        self.name_input.setStyleSheet("""
            QLineEdit { 
                background-color: white; 
                border: 2px solid #dee2e6; 
                border-radius: 8px; 
                padding: 0 15px; 
                font-size: 14px; 
                color: #2c3e50;
            } 
            QLineEdit:focus { 
                border-color: #3498db; 
            }
        """)
        name_layout.addWidget(self.name_input)
        form_layout.addWidget(name_widget)
        
        image_widget = QWidget()
        image_widget.setStyleSheet("background-color: white; color: #000000;")
        image_layout = QVBoxLayout(image_widget)
        
        image_label = QLabel("Ссылка на изображение (опционально):")
        image_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        image_layout.addWidget(image_label)
        
        self.image_input = QLineEdit()
        self.image_input.setFixedHeight(45)
        self.image_input.setStyleSheet("""
            QLineEdit { 
                background-color: white; 
                border: 2px solid #dee2e6; 
                border-radius: 8px; 
                padding: 0 15px; 
                font-size: 14px; 
                color: #2c3e50;
            } 
            QLineEdit:focus { 
                border-color: #3498db; 
            }
        """)
        self.image_input.setPlaceholderText("https://example.com/image.png или C:/path/to/image.png")
        image_layout.addWidget(self.image_input)
        form_layout.addWidget(image_widget)
        
        layout.addWidget(form_widget)
        
        buttons_widget = QWidget()
        buttons_widget.setStyleSheet("background-color: white; color: #000000;")
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setSpacing(15)
        
        self.cancel_button = QPushButton("Отменить")
        self.cancel_button.setFixedHeight(45)
        self.cancel_button.setStyleSheet("""
            QPushButton { 
                background-color: #95a5a6; 
                color: #000000; 
                border: none; 
                border-radius: 8px; 
                font-size: 16px; 
                font-weight: bold; 
            } 
            QPushButton:hover { 
                background-color: #7f8c8d; 
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        
        self.add_button = QPushButton("Добавить")
        self.add_button.setFixedHeight(45)
        self.add_button.setStyleSheet("""
            QPushButton { 
                background-color: #3498db; 
                color: #000000; 
                border: none; 
                border-radius: 8px; 
                font-size: 16px; 
                font-weight: bold; 
            } 
            QPushButton:hover { 
                background-color: #2980b9; 
            }
        """)
        self.add_button.clicked.connect(self.add_brand)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.add_button)
        
        layout.addWidget(buttons_widget)
    
    def add_brand(self):
        brand_name = self.name_input.text().strip()
        image_url = self.image_input.text().strip() or None
        
        if not brand_name:
            QMessageBox.warning(self, "Ошибка", "Введите название бренда")
            return
        
        success, result = config.add_brand(brand_name, image_url)
        
        if success:
            QMessageBox.information(self, "Успех", f"Бренд '{brand_name}' успешно добавлен!")
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", result)


class OrderDetailsDialog(QDialog):
    def __init__(self, order_id, parent=None):
        super().__init__(parent)
        self.order_id = order_id
        self.setWindowTitle(f"Детали заказа #{order_id}")
        self.setFixedSize(700, 600)
        self.setModal(True)
        self.setStyleSheet("background-color: white; color: #000000;")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel(f"Заказ #{order_id}")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;")
        layout.addWidget(title_label)
        
        self.info_container = QWidget()
        self.info_container.setStyleSheet("background-color: white; color: #000000;")
        self.info_layout = QVBoxLayout(self.info_container)
        self.info_layout.setSpacing(8)
        
        layout.addWidget(self.info_container)
        
        products_label = QLabel("Товары в заказе:")
        products_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057;")
        layout.addWidget(products_label)
        
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels(["Товар", "Артикул", "Кол-во", "Цена", "Сумма"])
        self.products_table.setRowCount(0)
        
        self.products_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.products_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.products_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.products_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.products_table.verticalHeader().setVisible(False)
        
        self.products_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #dee2e6;
                font-size: 13px;
            }
            QTableWidget::item {
                color: #000000;
                border-bottom: 1px solid #dee2e6;
                padding: 6px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #495057;
                font-weight: bold;
                font-size: 13px;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #dee2e6;
            }
        """)
        
        layout.addWidget(self.products_table, 1)
        
        close_button = QPushButton("Закрыть")
        close_button.setFixedHeight(40)
        close_button.setStyleSheet("""
            QPushButton { 
                background-color: #3498db; 
                color: #000000; 
                border: none; 
                border-radius: 6px; 
                font-size: 14px; 
                font-weight: bold; 
            } 
            QPushButton:hover { 
                background-color: #2980b9; 
            }
        """)
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.load_order_data()
    
    def load_order_data(self):
        order_details = config.get_order_details(self.order_id)
        
        if not order_details:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить детали заказа")
            self.reject()
            return
        
        self.add_info_row("Дата заказа:", order_details['order_date'])
        self.add_info_row("Статус:", order_details['status'])
        self.add_info_row("Покупатель:", order_details['customer_name'])
        self.add_info_row("Email:", order_details['customer_email'])
        self.add_info_row("Общая сумма:", f"{order_details['total_amount']} руб.")
        
        self.products_table.setRowCount(len(order_details['items']))
        
        for i, item in enumerate(order_details['items']):
            name_item = QTableWidgetItem(item['product_name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.products_table.setItem(i, 0, name_item)
            
            article_item = QTableWidgetItem(item['article'])
            article_item.setFlags(article_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.products_table.setItem(i, 1, article_item)
            
            qty_item = QTableWidgetItem(str(item['quantity']))
            qty_item.setFlags(qty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.products_table.setItem(i, 2, qty_item)
            
            price_item = QTableWidgetItem(f"{item['price']} руб.")
            price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.products_table.setItem(i, 3, price_item)
            
            total_item = QTableWidgetItem(f"{item['total_price']} руб.")
            total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            total_item.setForeground(QColor("#2ecc71"))
            self.products_table.setItem(i, 4, total_item)
    
    def add_info_row(self, label, value):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057; min-width: 120px;")
        
        value_widget = QLabel(value)
        value_widget.setStyleSheet("font-size: 14px; color: #6c757d;")
        
        layout.addWidget(label_widget)
        layout.addWidget(value_widget)
        layout.addStretch()
        
        self.info_layout.addWidget(widget)