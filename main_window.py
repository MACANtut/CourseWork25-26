import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QFrame, QPushButton, QLineEdit, 
                               QGridLayout, QScrollArea, QDialog, 
                               QListWidget, QListWidgetItem, QComboBox, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QStackedWidget, QDateEdit, QMessageBox, QCheckBox)
from PySide6.QtCore import Qt, QTimer, QDate, QSize, QPoint
from PySide6.QtGui import QColor, QFont, QPixmap, QPainter
from PySide6.QtCharts import QChart, QChartView, QBarSet, QBarSeries, QBarCategoryAxis, QValueAxis
import config
from filters import ProductFilter
from widgets import (
    CategoryConfirmationDialog, ImageLoader, CartItemWidget, DeleteProductDialog,
    PeriodSelectionDialog, AddProductDialog, ProductDetailWidget, BrandCard,
    ProductCard, CategoryDropdown, AddBrandDialog, image_loader, OrderDetailsDialog
)


class MainWindow(QMainWindow):
    def __init__(self, username="user101", user_id=None, current_user=None):
        super().__init__()
        self.username = username
        self.user_id = user_id
        self.current_user = current_user or {}
        
        if self.current_user:
            self.current_user['is_first_user'] = self.current_user.get('is_first_user', False)
        else:
            self.current_user = {'is_first_user': False}
        
        self.setWindowTitle("Магазин спортивных товаров")
        self.setGeometry(100, 100, 1750, 800)
        self.setMinimumSize(1400, 1000)
        self.setStyleSheet("background-color: white;")
        
        # Инициализируем атрибуты до создания таймера
        self.current_mode = "products"
        self.categories = [
            "Аксессуары и дополнения",
            "Зимние виды спорта", 
            "Водные виды спорта",
            "Велоспорт",
            "Единоборства и бокс",
            "Спортивный инвентарь",
            "Тренажеры и фитнес",
            "Одежда и обувь"
        ]
        self.brand_cards = []
        self.product_cards = []
        self.cart_items = []
        self.cart_widgets = []
        self.order_history = []
        self.all_products = []
        self.new_employee_row = None
        self.selected_period = None
        
        self.product_filter = ProductFilter()
        self.product_filter.load_brand_mappings()
        
        # Теперь создаем таймер
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.handle_resize)  # Теперь метод существует
        
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: white;")
        self.setCentralWidget(main_widget)
        
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: white;")
        main_layout.addWidget(self.content_stack, 1)
        
        self.create_content_sections()
        self.load_products_from_db()
        self.load_cart_from_db()
        self.load_order_history()
        self.show_products()
    
    def handle_resize(self):
        """Обработчик изменения размера окна"""
        if self.current_mode == "products":
            self.update_grid_layout()
        elif self.current_mode == "brands":
            self.update_brands_grid_layout()
    
    def create_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2c3e50, stop:1 #34495e); 
            color: white; 
            border-right: 1px solid #dee2e6;
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 20)
        
        display_name = self.current_user.get('first_name', '') + ' ' + self.current_user.get('last_name', '') if self.current_user else self.username
        title_label = QLabel(display_name)
        title_label.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: white; 
            border-bottom: 2px solid rgba(255,255,255,0.3); 
            padding-bottom: 10px;
        """)
        layout.addWidget(title_label)
        
        main_buttons = ["Бренды", "Категории", "Корзина"]
        for button_text in main_buttons:
            button = QPushButton(button_text)
            button.setFixedHeight(40)
            
            if button_text == "Корзина" and self.current_user.get('is_first_user', False):
                button.setStyleSheet("""
                    QPushButton { 
                        background-color: rgba(255,255,255,0.1); 
                        border: 1px solid rgba(255,255,255,0.3); 
                        border-radius: 5px; 
                        font-size: 14px; 
                        font-weight: bold; 
                        color: #7f8c8d; 
                        text-align: left; 
                        padding-left: 15px; 
                    } 
                    QPushButton:hover { 
                        background-color: rgba(255,255,255,0.1); 
                        border-color: rgba(255,255,255,0.3); 
                    }
                """)
                button.setEnabled(False)
                button.clicked.connect(self.show_disabled_cart_message)
            else:
                button.setStyleSheet("""
                    QPushButton { 
                        background-color: rgba(255,255,255,0.1); 
                        border: 1px solid rgba(255,255,255,0.3); 
                        border-radius: 5px; 
                        font-size: 14px; 
                        font-weight: bold; 
                        color: white; 
                        text-align: left; 
                        padding-left: 15px; 
                    } 
                    QPushButton:hover { 
                        background-color: rgba(255,255,255,0.2); 
                        border-color: #3498db; 
                    }
                """)
                if button_text == "Бренды":
                    button.clicked.connect(self.show_brands)
                elif button_text == "Категории":
                    button.clicked.connect(lambda: self.toggle_category_dropdown())
                elif button_text == "Корзина":
                    button.clicked.connect(self.show_cart)
            
            layout.addWidget(button)
        
        layout.addStretch()
        
        bottom_buttons = ["Сотрудники", "Продажи", "Добавить товар"]
        for button_text in bottom_buttons:
            button = QPushButton(button_text)
            button.setFixedHeight(40)
            
            if not self.current_user.get('is_first_user', False):
                button.setVisible(False)
                button.setEnabled(False)
            else:
                button.setStyleSheet("""
                    QPushButton { 
                        background-color: rgba(255,255,255,0.1); 
                        border: 1px solid rgba(255,255,255,0.3); 
                        border-radius: 5px; 
                        font-size: 14px; 
                        font-weight: bold; 
                        color: white; 
                        text-align: left; 
                        padding-left: 15px; 
                    } 
                    QPushButton:hover { 
                        background-color: rgba(255,255,255,0.2); 
                        border-color: #3498db; 
                    }
                """)
                if button_text == "Сотрудники":
                    button.clicked.connect(self.show_employees)
                elif button_text == "Продажи":
                    button.clicked.connect(self.show_sales)
                elif button_text == "Добавить товар":
                    button.clicked.connect(self.show_add_product_dialog)
            
            layout.addWidget(button)
        
        return sidebar
    
    def show_disabled_cart_message(self):
        QMessageBox.information(
            self,
            "Корзина недоступна",
            "Функция корзины недоступна для первого пользователя в системе.\n\n"
            "Пожалуйста, зарегистрируйте нового пользователя для использования корзины."
        )
    
    def show_disabled_function_message(self):
        QMessageBox.information(
            self,
            "Функция недоступна",
            "Эта функция доступна только для администратора (первого пользователя).\n\n"
            "Пожалуйста, обратитесь к администратору для выполнения этой операции."
        )
    
    def toggle_category_dropdown(self):
        if not hasattr(self, 'category_dropdown'):
            self.category_dropdown = QListWidget()
            self.category_dropdown.setVisible(False)
            self.category_dropdown.setWindowFlags(Qt.WindowType.Popup)
            self.category_dropdown.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
            
            all_categories_item = QListWidgetItem("Все категории")
            all_categories_item.setData(Qt.ItemDataRole.UserRole, "")
            self.category_dropdown.addItem(all_categories_item)
            
            for category in self.categories:
                item = QListWidgetItem(category)
                item.setData(Qt.ItemDataRole.UserRole, category)
                self.category_dropdown.addItem(item)
            
            self.category_dropdown.itemSelectionChanged.connect(self.on_categories_selected)
        
        if self.category_dropdown.isVisible():
            self.category_dropdown.hide()
        else:
            sidebar = self.centralWidget().layout().itemAt(0).widget()
            sidebar_pos = sidebar.mapToGlobal(QPoint(0, 0))
            
            dropdown_x = sidebar_pos.x() + sidebar.width() - 5
            dropdown_y = sidebar_pos.y() + 120
            
            self.category_dropdown.move(dropdown_x, dropdown_y)
            self.category_dropdown.show()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_timer.start(100)
    
    def on_categories_selected(self):
        selected_items = self.category_dropdown.selectedItems()
        
        selected_categories = []
        for item in selected_items:
            category_value = item.data(Qt.ItemDataRole.UserRole)
            selected_categories.append(category_value)
        
        if "" in selected_categories:
            self.product_filter.selected_categories = []
        else:
            self.product_filter.set_selected_categories(selected_categories)
        
        self.update_filters_indicators()
        self.category_dropdown.hide()
        self.show_products()
    
    def show_product_details(self, product_data):
        detail_widget = ProductDetailWidget(product_data, self)
        
        old_widget = self.content_stack.widget(1)
        if old_widget:
            self.content_stack.removeWidget(old_widget)
        
        self.content_stack.insertWidget(1, detail_widget)
        
        self.content_stack.setCurrentIndex(1)
        self.current_mode = "product_details"
    
    def show_all_products(self):
        self.current_mode = "products"
        self.product_filter.reset_filters()
        
        if hasattr(self, 'category_dropdown'):
            self.category_dropdown.clearSelection()
        
        self.reset_brand_selection()
        self.update_filters_indicators()
        self.content_stack.setCurrentIndex(0)
        if hasattr(self, 'category_dropdown'):
            self.category_dropdown.hide()
        self.display_filtered_products()
    
    def show_products(self):
        self.current_mode = "products"
        self.content_stack.setCurrentIndex(0)
        if hasattr(self, 'category_dropdown'):
            self.category_dropdown.hide()
        
        self.update_filters_indicators()
        self.display_filtered_products()
    
    def show_brands(self):
        self.current_mode = "brands"
        self.content_stack.setCurrentIndex(4)
        if hasattr(self, 'category_dropdown'):
            self.category_dropdown.hide()
        self.load_brands_from_db()
        
        if hasattr(self, 'brand_cards'):
            for card in self.brand_cards:
                brand_id = card.brand_data.get('id')
                if brand_id:
                    card.is_selected = brand_id in self.product_filter.selected_brands
                    card.update_appearance()
    
    def show_cart(self):
        if self.current_user.get('is_first_user', False):
            self.show_disabled_cart_message()
            return
            
        self.current_mode = "cart"
        self.content_stack.setCurrentIndex(2)
        if hasattr(self, 'category_dropdown'):
            self.category_dropdown.hide()
        self.load_cart_from_db()
        self.load_order_history()
    
    def show_employees(self):
        if not self.current_user.get('is_first_user', False):
            self.show_disabled_function_message()
            return
            
        self.current_mode = "employees"
        self.content_stack.setCurrentIndex(3)
        if hasattr(self, 'category_dropdown'):
            self.category_dropdown.hide()
        self.load_employees_from_db()
    
    def show_sales(self):
        if not self.current_user.get('is_first_user', False):
            self.show_disabled_function_message()
            return
            
        self.current_mode = "sales"
        self.content_stack.setCurrentIndex(5)
        if hasattr(self, 'category_dropdown'):
            self.category_dropdown.hide()
        
        if hasattr(self, 'sales_chart_view'):
            self.update_sales_chart()
        else:
            self.update_sales_chart()
    
    def show_add_product_dialog(self):
        if not self.current_user.get('is_first_user', False):
            self.show_disabled_function_message()
            return
            
        dialog = AddProductDialog(self)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self.load_products_from_db()
    
    def on_brand_selected(self, brand_id, is_selected):
        pass
    
    def apply_brand_filter_and_go_back(self):
        selected_brands = []
        for card in self.brand_cards:
            if card.is_selected:
                brand_id = card.brand_data.get('id')
                if brand_id:
                    selected_brands.append(brand_id)
        
        if not selected_brands:
            self.product_filter.selected_brands = []
        else:
            self.product_filter.set_selected_brands(selected_brands)
        
        self.update_filters_indicators()
        self.show_products()
    
    def clear_brand_filter_completely(self):
        self.product_filter.selected_brands = []
        self.reset_brand_selection()
        self.update_filters_indicators()
        self.display_filtered_products()
        self.show_products()
    
    def update_brand_cards_selection(self):
        if hasattr(self, 'brand_cards'):
            for card in self.brand_cards:
                brand_id = card.brand_data.get('id')
                if brand_id:
                    if brand_id in self.product_filter.selected_brands:
                        if not card.is_selected:
                            card.is_selected = True
                            card.update_appearance()
                    else:
                        if card.is_selected:
                            card.is_selected = False
                            card.update_appearance()
    
    def update_filters_indicators(self):
        if hasattr(self, 'filters_container'):
            for i in reversed(range(self.filters_layout.count())):
                widget = self.filters_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
        
        if not self.product_filter.has_active_filters():
            no_filter_label = QLabel("Нет активных фильтров")
            no_filter_label.setStyleSheet("font-size: 14px; color: #6c757d; font-style: italic;")
            self.filters_layout.addWidget(no_filter_label)
            return
        
        if self.product_filter.selected_categories:
            if len(self.product_filter.selected_categories) == 1:
                category_text = self.product_filter.selected_categories[0]
            else:
                category_text = f"{len(self.product_filter.selected_categories)} категорий"
            
            category_widget = self.create_filter_indicator(
                "Категории", 
                category_text,
                lambda: self.clear_category_filter()
            )
            self.filters_layout.addWidget(category_widget)
        
        if self.product_filter.selected_brands:
            selected_names = self.product_filter.get_selected_brand_names()
            if selected_names:
                if len(selected_names) == 1:
                    brands_text = selected_names[0]
                else:
                    brands_text = f"{len(selected_names)} брендов"
                
                brands_widget = self.create_filter_indicator(
                    "Бренды", 
                    brands_text,
                    lambda: self.clear_brand_filter()
                )
                self.filters_layout.addWidget(brands_widget)
        
        if self.product_filter.search_text:
            search_widget = self.create_filter_indicator(
                "Поиск", 
                f"'{self.product_filter.search_text}'",
                lambda: self.clear_search_filter()
            )
            self.filters_layout.addWidget(search_widget)
        
        if self.product_filter.has_active_filters():
            clear_all_button = QPushButton("Сбросить все")
            clear_all_button.setFixedSize(100, 30)
            clear_all_button.setStyleSheet("""
                QPushButton { 
                    background-color: #e74c3c; 
                    color: white; 
                    border: none; 
                    border-radius: 4px; 
                    font-size: 12px; 
                    font-weight: bold; 
                    padding: 2px 5px;
                } 
                QPushButton:hover { 
                    background-color: #c0392b; 
                }
            """)
            clear_all_button.clicked.connect(self.show_all_products)
            self.filters_layout.addWidget(clear_all_button)
    
    def create_filter_indicator(self, label, value, clear_callback):
        widget = QWidget()
        widget.setFixedHeight(35)
        widget.setStyleSheet("""
            QWidget {
                background-color: #e3f2fd;
                border: 1px solid #3498db;
                border-radius: 6px;
                margin: 2px;
            }
        """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(8)
        
        filter_label = QLabel(f"{label}: {value}")
        filter_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(filter_label)
        
        layout.addStretch()
        
        clear_button = QPushButton("×")
        clear_button.setFixedSize(20, 20)
        clear_button.setStyleSheet("""
            QPushButton { 
                background-color: #95a5a6; 
                color: white; 
                border: none; 
                border-radius: 10px; 
                font-size: 12px; 
                font-weight: bold; 
            } 
            QPushButton:hover { 
                background-color: #7f8c8d; 
            }
        """)
        clear_button.clicked.connect(clear_callback)
        layout.addWidget(clear_button)
        
        return widget
    
    def clear_brand_filter(self):
        self.product_filter.selected_brands = []
        self.update_filters_indicators()
        self.show_products()
    
    def clear_category_filter(self):
        self.product_filter.selected_categories = []
        
        if hasattr(self, 'category_dropdown'):
            self.category_dropdown.clearSelection()
        
        self.update_filters_indicators()
        self.show_products()
    
    def clear_search_filter(self):
        self.search_bar.clear()
        self.product_filter.search_text = ""
        self.update_filters_indicators()
        self.display_filtered_products()
    
    def create_products_section(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background-color: white; border: none;")
        
        container = QWidget()
        container.setStyleSheet("background-color: white;")
        scroll_area.setWidget(container)
        
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 20, 30, 20)
        
        search_container = QWidget()
        search_container.setStyleSheet("background-color: white;")
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        search_layout.addStretch()
        self.search_bar = QLineEdit()
        self.search_bar.setFixedHeight(40)
        self.search_bar.setFixedWidth(400)
        self.search_bar.setPlaceholderText("Поиск товара...")
        self.search_bar.setStyleSheet("""
            QLineEdit { 
                border: 2px solid #dee2e6; 
                border-radius: 20px; 
                padding: 0 15px; 
                font-size: 14px; 
                background-color: white; 
                color: #000000;
            } 
            QLineEdit:focus { 
                border-color: #3498db; 
            }
        """)
        self.search_bar.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_bar)
        search_layout.addStretch()
        
        layout.addWidget(search_container)
        
        self.filters_container = QWidget()
        self.filters_container.setStyleSheet("background-color: white; border: 1px solid #dee2e6; border-radius: 8px; padding: 5px;")
        self.filters_layout = QHBoxLayout(self.filters_container)
        self.filters_layout.setSpacing(8)
        self.filters_layout.setContentsMargins(10, 5, 10, 5)
        
        layout.addWidget(self.filters_container)
        
        section_title = QLabel("Товары")
        section_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(section_title)
        
        self.cards_grid_widget = QWidget()
        self.cards_grid_widget.setStyleSheet("background-color: white;")
        layout.addWidget(self.cards_grid_widget, 1)
        
        self.grid_layout = QGridLayout(self.cards_grid_widget)
        self.grid_layout.setSpacing(15)
        
        self.update_filters_indicators()
        
        return scroll_area
    
    def on_search_text_changed(self):
        search_text = self.search_bar.text()
        self.product_filter.set_search_text(search_text)
        self.update_filters_indicators()
        self.display_filtered_products()
    
    def load_products_from_db(self):
        try:
            self.all_products = config.get_all_products()
        except Exception:
            self.all_products = []
        self.display_filtered_products()
    
    def display_filtered_products(self):
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        self.product_cards = []
        
        if not self.all_products:
            no_products_label = QLabel("Нет товаров для отображения")
            no_products_label.setStyleSheet("font-size: 16px; color: #6c757d;")
            no_products_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(no_products_label, 0, 0)
            return
        
        filtered_products = self.product_filter.filter_products(self.all_products)
        
        if not filtered_products:
            filter_info = QLabel(f"Нет товаров, соответствующих фильтрам: {self.product_filter.get_filter_summary()}")
            filter_info.setStyleSheet("font-size: 16px; color: #6c757d; padding: 20px;")
            filter_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            filter_info.setWordWrap(True)
            self.grid_layout.addWidget(filter_info, 0, 0)
            return
    
        for product_data in filtered_products:
            product_card = ProductCard(product_data, self)
            self.product_cards.append(product_card)
        
        self.update_grid_layout()
    
    def load_cart_from_db(self):
        if self.current_user.get('is_first_user', False):
            return
        
        if not self.user_id:
            return
        
        try:
            self.cart_items = config.get_user_cart(self.user_id)
        except Exception:
            self.cart_items = []
        
        self.update_cart_display()
    
    def add_to_cart(self, product_id, product_name, price):
        if self.current_user.get('is_first_user', False):
            self.show_disabled_cart_message()
            return
        
        if not self.user_id:
            QMessageBox.warning(self, "Ошибка", "Необходимо войти в систему")
            return
        
        success, message = config.add_to_cart(self.user_id, product_id)
        
        if success:
            self.load_cart_from_db()
            
            if self.current_mode == "cart":
                self.update_cart_display()
        else:
            QMessageBox.warning(self, "Ошибка", message)
    
    def create_cart_section(self):
        cart_widget = QWidget()
        cart_widget.setStyleSheet("background-color: white;")
        cart_layout = QVBoxLayout(cart_widget)
        cart_layout.setSpacing(20)
        cart_layout.setContentsMargins(30, 20, 30, 20)
        
        cart_title = QLabel("Корзина")
        cart_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;")
        cart_layout.addWidget(cart_title)
        
        if self.current_user.get('is_first_user', False):
            disabled_message = QLabel("Корзина недоступна для первого пользователя в системе.\n\nЗарегистрируйте нового пользователя для использования корзины.")
            disabled_message.setStyleSheet("font-size: 16px; color: #e74c3c; font-weight: bold; padding: 20px; text-align: center;")
            disabled_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
            disabled_message.setWordWrap(True)
            cart_layout.addWidget(disabled_message)
            
            back_button = QPushButton("Назад")
            back_button.setFixedHeight(45)
            back_button.setStyleSheet("QPushButton { background-color: #95a5a6; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #7f8c8d; }")
            back_button.clicked.connect(self.show_all_products)
            cart_layout.addWidget(back_button)
            
            return cart_widget
        
        content_container = QWidget()
        content_container.setStyleSheet("background-color: white;")
        content_layout = QHBoxLayout(content_container)
        
        left_widget = QWidget()
        left_widget.setStyleSheet("background-color: white;")
        left_layout = QVBoxLayout(left_widget)
        
        cart_label = QLabel("В корзине:")
        cart_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #495057;")
        left_layout.addWidget(cart_label)
        
        self.cart_scroll = QScrollArea()
        self.cart_scroll.setWidgetResizable(True)
        self.cart_scroll.setFixedHeight(300)
        self.cart_scroll.setStyleSheet("background-color: white; border: 1px solid #dee2e6; border-radius: 8px;")
        
        self.cart_items_widget = QWidget()
        self.cart_items_widget.setStyleSheet("background-color: white;")
        self.cart_items_layout = QVBoxLayout(self.cart_items_widget)
        self.cart_items_layout.setSpacing(8)
        self.cart_items_layout.setContentsMargins(15, 15, 15, 15)
        
        self.total_label = QLabel("Общая стоимость: 0.00 руб.")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; padding: 10px; border-top: 2px solid #dee2e6;")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.cart_scroll.setWidget(self.cart_items_widget)
        left_layout.addWidget(self.cart_scroll)
        left_layout.addWidget(self.total_label)
        
        checkout_button = QPushButton("Оформить заказ")
        checkout_button.setFixedHeight(45)
        checkout_button.setStyleSheet("QPushButton { background-color: #3498db; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #2980b9; }")
        checkout_button.clicked.connect(self.checkout_order)
        left_layout.addWidget(checkout_button)
        
        right_widget = QWidget()
        right_widget.setStyleSheet("background-color: white;")
        right_layout = QVBoxLayout(right_widget)
        
        history_label = QLabel("История покупок:")
        history_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #495057;")
        right_layout.addWidget(history_label)
        
        history_scroll = QScrollArea()
        history_scroll.setWidgetResizable(True)
        history_scroll.setFixedHeight(250)
        history_scroll.setStyleSheet("background-color: white; border: 1px solid #dee2e6; border-radius: 8px;")
        
        self.history_widget = QWidget()
        self.history_widget.setStyleSheet("background-color: white;")
        self.history_layout = QVBoxLayout(self.history_widget)
        self.history_layout.setSpacing(8)
        self.history_layout.setContentsMargins(15, 15, 15, 15)
        
        history_scroll.setWidget(self.history_widget)
        right_layout.addWidget(history_scroll)
        
        back_button = QPushButton("Назад")
        back_button.setFixedHeight(45)
        back_button.setStyleSheet("QPushButton { background-color: #95a5a6; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #7f8c8d; }")
        back_button.clicked.connect(self.show_all_products)
        right_layout.addWidget(back_button)
        
        content_layout.addWidget(left_widget)
        content_layout.addWidget(right_widget)
        content_layout.setStretchFactor(left_widget, 60)
        content_layout.setStretchFactor(right_widget, 40)
        
        cart_layout.addWidget(content_container)
        
        return cart_widget
    
    def update_cart_display(self):
        if self.current_user.get('is_first_user', False):
            return
            
        for i in reversed(range(self.cart_items_layout.count())):
            widget = self.cart_items_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        if not self.cart_items:
            empty_label = QLabel("Корзина пуста")
            empty_label.setStyleSheet("font-size: 16px; color: #6c757d;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cart_items_layout.addWidget(empty_label)
        else:
            header_widget = QWidget()
            header_widget.setFixedHeight(30)
            header_layout = QHBoxLayout(header_widget)
            header_layout.setContentsMargins(15, 0, 15, 0)
            
            name_header = QLabel("Товар")
            name_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057; min-width: 150px;")
            header_layout.addWidget(name_header)
            
            article_header = QLabel("Артикул")
            article_header.setFixedWidth(100)
            article_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            article_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
            header_layout.addWidget(article_header)
            
            header_layout.addStretch()
            
            price_header = QLabel("Цена")
            price_header.setFixedWidth(80)
            price_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            price_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
            header_layout.addWidget(price_header)
            
            total_header = QLabel("Сумма")
            total_header.setFixedWidth(100)
            total_header.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            total_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
            header_layout.addWidget(total_header)
            
            actions_header = QLabel("Действия")
            actions_header.setFixedWidth(80)
            actions_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            actions_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
            header_layout.addWidget(actions_header)
            
            self.cart_items_layout.addWidget(header_widget)
            
            self.cart_widgets = []
            for item in self.cart_items:
                cart_item_widget = CartItemWidget(
                    item['product_id'],
                    item['article'],
                    item['name'],
                    item['price'],
                    item['quantity'],
                    self.user_id
                )
                self.cart_widgets.append(cart_item_widget)
                self.cart_items_layout.addWidget(cart_item_widget)
        
        self.update_cart_total()
    
    def update_cart_total(self):
        total = 0
        for widget in self.cart_widgets:
            total += widget.get_total_price()
        
        self.total_label.setText(f"Общая стоимость: {total:.2f} руб.")
    
    def checkout_order(self):
        if self.current_user.get('is_first_user', False):
            QMessageBox.information(
                self,
                "Корзина недоступна",
                "Функция корзины недоступна для первого пользователя в системе."
            )
            return
        
        if not self.cart_items:
            QMessageBox.warning(self, "Корзина пуста", "Добавьте товары в корзину перед оформлением заказа")
            return
        
        total = self.calculate_cart_total()
        
        # Убрали окно подтверждения - сразу создаем заказ
        success, result = config.create_order(self.user_id, self.cart_items)
        
        if success:
            QMessageBox.information(
                self, 
                "Заказ оформлен", 
                f"Ваш заказ №{result} успешно оформлен!\nСумма заказа: {total:.2f} руб."
            )
            
            self.load_cart_from_db()
            self.load_order_history()
            
            if self.current_mode == "sales":
                self.update_sales_chart()
        else:
            QMessageBox.warning(self, "Ошибка", result)
    
    def calculate_cart_total(self):
        total = 0
        for item in self.cart_items:
            total += float(item['price']) * item['quantity']
        return total
    
    def load_order_history(self):
        if self.current_user.get('is_first_user', False):
            return
        
        if not self.user_id:
            return
        
        try:
            self.order_history = config.get_user_orders(self.user_id)
        except Exception:
            self.order_history = []
        
        self.update_order_history_display()
    
    def update_order_history_display(self):
        if self.current_user.get('is_first_user', False):
            return
            
        if hasattr(self, 'history_layout'):
            for i in reversed(range(self.history_layout.count())):
                widget = self.history_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
        
        if not self.order_history:
            empty_label = QLabel("История покупок пуста")
            empty_label.setStyleSheet("font-size: 16px; color: #6c757d;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if hasattr(self, 'history_layout'):
                self.history_layout.addWidget(empty_label)
        else:
            header_widget = QWidget()
            header_widget.setFixedHeight(30)
            header_layout = QHBoxLayout(header_widget)
            header_layout.setContentsMargins(15, 0, 15, 0)
            
            id_header = QLabel("№ заказа")
            id_header.setFixedWidth(80)
            id_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
            header_layout.addWidget(id_header)
            
            date_header = QLabel("Дата")
            date_header.setFixedWidth(120)
            date_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
            header_layout.addWidget(date_header)
            
            items_header = QLabel("Товаров")
            items_header.setFixedWidth(70)
            items_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
            header_layout.addWidget(items_header)
            
            total_header = QLabel("Сумма")
            total_header.setFixedWidth(100)
            total_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
            header_layout.addWidget(total_header)
            
            status_header = QLabel("Статус")
            status_header.setFixedWidth(80)
            status_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
            header_layout.addWidget(status_header)
            
            if hasattr(self, 'history_layout'):
                self.history_layout.addWidget(header_widget)
            
            for order in self.order_history:
                order_widget = self.create_order_history_item(order)
                if hasattr(self, 'history_layout'):
                    self.history_layout.addWidget(order_widget)
    
    def create_order_history_item(self, order):
        widget = QWidget()
        widget.setFixedHeight(40)
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                margin: 2px 0;
            }
            QWidget:hover {
                background-color: #e9ecef;
            }
        """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(15, 5, 15, 5)
        
        order_id_label = QLabel(f"#{order['order_id']}")
        order_id_label.setFixedWidth(80)
        order_id_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #3498db;")
        layout.addWidget(order_id_label)
        
        date_label = QLabel(order['order_date'])
        date_label.setFixedWidth(120)
        date_label.setStyleSheet("font-size: 14px; color: #495057;")
        layout.addWidget(date_label)
        
        items_label = QLabel(str(order['items_count']))
        items_label.setFixedWidth(70)
        items_label.setStyleSheet("font-size: 14px; color: #495057;")
        layout.addWidget(items_label)
        
        total_label = QLabel(f"{order['total_amount']} руб.")
        total_label.setFixedWidth(100)
        total_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2ecc71;")
        layout.addWidget(total_label)
        
        status_label = QLabel(order['status'])
        status_label.setFixedWidth(80)
        if order['status'] == 'Завершен':
            status_label.setStyleSheet("font-size: 14px; color: #2ecc71; font-weight: bold;")
        else:
            status_label.setStyleSheet("font-size: 14px; color: #e74c3c; font-weight: bold;")
        layout.addWidget(status_label)
        
        details_btn = QPushButton("Детали")
        details_btn.setFixedSize(60, 25)
        details_btn.setStyleSheet("""
            QPushButton { 
                background-color: #3498db; 
                color: white; 
                border: none; 
                border-radius: 3px; 
                font-size: 11px; 
                font-weight: bold; 
            } 
            QPushButton:hover { 
                background-color: #2980b9; 
            }
        """)
        details_btn.clicked.connect(lambda checked, oid=order['order_id']: self.show_order_details(oid))
        layout.addWidget(details_btn)
        
        layout.addStretch()
        
        return widget
    
    def show_order_details(self, order_id):
        dialog = OrderDetailsDialog(order_id, self)
        dialog.exec()
    
    def create_employees_section(self):
        employees_widget = QWidget()
        employees_widget.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(employees_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 20, 30, 20)
        
        title_label = QLabel("Сотрудники")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;")
        layout.addWidget(title_label)
        
        self.employees_table = QTableWidget()
        self.employees_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #dee2e6;
                font-size: 13px;
                color: #000000;
            }
            QTableWidget::item {
                color: #000000;
                border-bottom: 1px solid #dee2e6;
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #000000;
                font-weight: bold;
                font-size: 14px;
                padding: 8px;
                border: none;
                border-right: 1px solid #dee2e6;
                border-bottom: 2px solid #dee2e6;
            }
            QLineEdit {
                color: #000000;
            }
        """)
        
        self.employees_table.setColumnCount(7)
        self.employees_table.setHorizontalHeaderLabels(["Фамилия", "Имя", "Отчество", "Должность", "Email", "Дата найма", "Активность"])
        self.employees_table.verticalHeader().setDefaultSectionSize(40)
        self.employees_table.setRowCount(0)
        
        self.employees_table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)
        self.employees_table.cellChanged.connect(self.on_employee_cell_changed)
        
        layout.addWidget(self.employees_table, 1)
        
        buttons_widget = QWidget()
        buttons_widget.setStyleSheet("background-color: white;")
        buttons_layout = QHBoxLayout(buttons_widget)
        
        self.add_employee_button = QPushButton("Добавить сотрудника")
        self.add_employee_button.setFixedHeight(45)
        self.add_employee_button.setStyleSheet("""
            QPushButton { 
                background-color: #2ecc71; 
                color: white; 
                border: none; 
                border-radius: 8px; 
                font-size: 16px; 
                font-weight: bold; 
            } 
            QPushButton:hover { 
                background-color: #27ae60; 
            }
        """)
        self.add_employee_button.clicked.connect(self.add_employee_row)
        
        back_button = QPushButton("Назад")
        back_button.setFixedHeight(45)
        back_button.setStyleSheet("""
            QPushButton { 
                background-color: #95a5a6; 
                color: white; 
                border: none; 
                border-radius: 8px; 
                font-size: 16px; 
                font-weight: bold; 
            } 
            QPushButton:hover { 
                background-color: #7f8c8d; 
            }
        """)
        back_button.clicked.connect(self.show_all_products)
        
        buttons_layout.addWidget(self.add_employee_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(back_button)
        
        layout.addWidget(buttons_widget)
        
        return employees_widget
    
    def add_employee_row(self):
        if self.new_employee_row is not None:
            QMessageBox.information(self, "Информация", "Завершите редактирование текущей строки перед добавлением новой")
            return
    
        current_row_count = self.employees_table.rowCount()
        self.employees_table.insertRow(current_row_count)
        self.new_employee_row = current_row_count
        
        current_date_item = QTableWidgetItem(QDate.currentDate().toString('dd.MM.yyyy'))
        current_date_item.setForeground(QColor("#000000"))
        self.employees_table.setItem(current_row_count, 5, current_date_item)
        
        active_item = QTableWidgetItem("Да")
        active_item.setForeground(QColor("#000000"))
        self.employees_table.setItem(current_row_count, 6, active_item)
        
        position_item = QTableWidgetItem("Админ")
        position_item.setForeground(QColor("#000000"))
        self.employees_table.setItem(current_row_count, 3, position_item)
        
        self.employees_table.scrollToBottom()
    
        QMessageBox.information(self, "Информация", 
            "Заполните все обязательные поля (Фамилия, Имя, Email).")
    
    def on_employee_cell_changed(self, row, column):
        if row == self.new_employee_row:
            self.check_new_employee_row(row)
    
    def check_new_employee_row(self, row):
        required_columns = [0, 1, 4]
        
        all_filled = True
        for col in required_columns:
            item = self.employees_table.item(row, col)
            if not item or not item.text().strip():
                all_filled = False
                break
        
        if all_filled:
            email_item = self.employees_table.item(row, 4)
            if email_item and email_item.text().strip():
                email = email_item.text().strip()
                if '@' not in email or '.' not in email:
                    QMessageBox.warning(self, "Ошибка", "Введите корректный email адрес")
                    email_item.setBackground(QColor("#ffe6e6"))
                    all_filled = False
                else:
                    if email_item.background() == QColor("#ffe6e6"):
                        email_item.setBackground(QColor("white"))
        
        if all_filled:
            self.save_new_employee(row)
    
    def save_new_employee(self, row):
        try:
            last_name_item = self.employees_table.item(row, 0)
            first_name_item = self.employees_table.item(row, 1)
            email_item = self.employees_table.item(row, 4)
            
            if not last_name_item or not last_name_item.text().strip():
                QMessageBox.warning(self, "Ошибка", "Поле 'Фамилия' обязательно для заполнения")
                return
                
            if not first_name_item or not first_name_item.text().strip():
                QMessageBox.warning(self, "Ошибка", "Поле 'Имя' обязательно для заполнения")
                return
                
            if not email_item or not email_item.text().strip():
                QMessageBox.warning(self, "Ошибка", "Поле 'Email' обязательно для заполнения")
                return
            
            employee_data = {
                'last_name': last_name_item.text().strip(),
                'first_name': first_name_item.text().strip(),
                'email': email_item.text().strip()
            }
            
            patronymic_item = self.employees_table.item(row, 2)
            if patronymic_item and patronymic_item.text().strip():
                employee_data['patronymic'] = patronymic_item.text().strip()
            else:
                employee_data['patronymic'] = None
            
            position_item = self.employees_table.item(row, 3)
            if position_item and position_item.text().strip():
                employee_data['position'] = position_item.text().strip()
            else:
                employee_data['position'] = 'Админ'
            
            hire_date_item = self.employees_table.item(row, 5)
            hire_date = ""
            if hire_date_item and hire_date_item.text().strip():
                date_text = hire_date_item.text().strip()
                try:
                    if '.' in date_text:
                        day, month, year = date_text.split('.')
                        hire_date = f"{year}-{month}-{day}"
                    elif '/' in date_text:
                        day, month, year = date_text.split('/')
                        hire_date = f"{year}-{month}-{day}"
                    else:
                        hire_date = date_text
                except Exception:
                    hire_date = QDate.currentDate().toString('yyyy-MM-dd')
            else:
                hire_date = QDate.currentDate().toString('yyyy-MM-dd')
            
            employee_data['hire_date'] = hire_date
            
            is_active_item = self.employees_table.item(row, 6)
            if is_active_item and is_active_item.text().strip():
                is_active_text = is_active_item.text().strip().lower()
                employee_data['is_active'] = is_active_text in ['да', 'yes', 'true', '1', '✓']
            else:
                employee_data['is_active'] = True
            
            if '@' not in employee_data['email'] or '.' not in employee_data['email']:
                QMessageBox.warning(self, "Ошибка", "Введите корректный email адрес")
                if email_item:
                    email_item.setBackground(QColor("#ffe6e6"))
                return
            else:
                if email_item and email_item.background() == QColor("#ffe6e6"):
                    email_item.setBackground(QColor("white"))
            
            success, result = config.add_employee(employee_data)
            
            if success:
                self.new_employee_row = None
                self.load_employees_from_db()
                QMessageBox.information(self, "Успех", result)
            else:
                QMessageBox.warning(self, "Ошибка", result)
                
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")    
    
    def load_employees_from_db(self):
        try:
            employees = config.get_all_employees()
        except Exception:
            employees = []
        
        self.employees_table.cellChanged.disconnect(self.on_employee_cell_changed)
        
        self.employees_table.setRowCount(0)
        
        if not employees:
            self.employees_table.cellChanged.connect(self.on_employee_cell_changed)
            return
        
        self.employees_table.setRowCount(len(employees))
        
        for row, employee in enumerate(employees):
            last_name = employee.get('last_name', '')
            item = QTableWidgetItem(last_name)
            item.setForeground(QColor("#000000"))
            self.employees_table.setItem(row, 0, item)
            
            first_name = employee.get('first_name', '')
            item = QTableWidgetItem(first_name)
            item.setForeground(QColor("#000000"))
            self.employees_table.setItem(row, 1, item)
            
            patronymic = employee.get('patronymic', '')
            item = QTableWidgetItem(patronymic)
            item.setForeground(QColor("#000000"))
            self.employees_table.setItem(row, 2, item)
            
            position = employee.get('position', 'Админ')
            item = QTableWidgetItem(position)
            item.setForeground(QColor("#000000"))
            self.employees_table.setItem(row, 3, item)
            
            email = employee.get('email', '')
            item = QTableWidgetItem(email)
            item.setForeground(QColor("#000000"))
            self.employees_table.setItem(row, 4, item)
            
            hire_date = employee.get('hire_date', '')
            if hire_date:
                try:
                    if '-' in hire_date and len(hire_date) >= 10:
                        year, month, day = hire_date[:10].split('-')
                        hire_date = f"{day}.{month}.{year}"
                except:
                    pass
            item = QTableWidgetItem(str(hire_date))
            item.setForeground(QColor("#000000"))
            self.employees_table.setItem(row, 5, item)
            
            is_active = employee.get('is_active', False)
            is_active_str = 'Да' if is_active else 'Нет'
            item = QTableWidgetItem(is_active_str)
            item.setForeground(QColor("#000000"))
            self.employees_table.setItem(row, 6, item)
        
        self.employees_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.employees_table.cellChanged.connect(self.on_employee_cell_changed)
        self.new_employee_row = None
    
    def create_brands_section(self):
        brands_widget = QWidget()
        brands_widget.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout(brands_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        brands_content = self.create_brands_content_section()
        layout.addWidget(brands_content, 1)
        
        buttons_widget = QWidget()
        buttons_widget.setStyleSheet("background-color: white; border-top: 1px solid #dee2e6;")
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(30, 15, 30, 15)
        
        if self.current_user.get('is_first_user', False):
            self.add_brand_button_bottom = QPushButton("Добавить бренд")
            self.add_brand_button_bottom.setFixedHeight(45)
            self.add_brand_button_bottom.setStyleSheet("""
                QPushButton { 
                    background-color: #2ecc71; 
                    color: white; 
                    border: none; 
                    border-radius: 8px; 
                    font-size: 16px; 
                    font-weight: bold; 
                    min-width: 150px;
                } 
                QPushButton:hover { 
                    background-color: #27ae60; 
                }
            """)
            self.add_brand_button_bottom.clicked.connect(self.show_add_brand_dialog)
            buttons_layout.addWidget(self.add_brand_button_bottom)
        
        cancel_button = QPushButton("Отменить")
        cancel_button.setFixedHeight(45)
        cancel_button.setStyleSheet("""
            QPushButton { 
                background-color: #95a5a6; 
                color: white; 
                border: none; 
                border-radius: 8px; 
                font-size: 16px; 
                font-weight: bold; 
                min-width: 120px;
            } 
            QPushButton:hover { 
                background-color: #7f8c8d; 
            }
        """)
        cancel_button.clicked.connect(self.clear_brand_filter_completely)
        
        confirm_button = QPushButton("Применить")
        confirm_button.setFixedHeight(45)
        confirm_button.setStyleSheet("""
            QPushButton { 
                background-color: #3498db; 
                color: white; 
                border: none; 
                border-radius: 8px; 
                font-size: 16px; 
                font-weight: bold; 
                min-width: 150px;
            } 
            QPushButton:hover { 
                background-color: #2980b9; 
            }
        """)
        confirm_button.clicked.connect(self.apply_brand_filter_and_go_back)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(confirm_button)
        
        layout.addWidget(buttons_widget)
        
        return brands_widget
    
    def create_brands_content_section(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background-color: white; border: none;")
        
        container = QWidget()
        container.setStyleSheet("background-color: white;")
        scroll_area.setWidget(container)
        
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(15)
        container_layout.setContentsMargins(30, 20, 30, 20)
        
        section_title = QLabel("Бренды")
        section_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        container_layout.addWidget(section_title)
        
        instruction_label = QLabel("Выберите бренды для фильтрации товаров. Нажмите на кнопку 'Выбрать' чтобы выбрать, затем нажмите 'Применить'")
        instruction_label.setStyleSheet("font-size: 14px; color: #6c757d;")
        instruction_label.setWordWrap(True)
        container_layout.addWidget(instruction_label)
        
        self.brands_grid_widget = QWidget()
        self.brands_grid_widget.setStyleSheet("background-color: white;")
        container_layout.addWidget(self.brands_grid_widget, 1)
        
        self.brands_grid_layout = QGridLayout(self.brands_grid_widget)
        self.brands_grid_layout.setSpacing(15)
        
        return scroll_area
    
    def reset_brand_selection(self):
        for card in self.brand_cards:
            if card.is_selected:
                card.is_selected = False
                card.update_appearance()
        self.product_filter.set_selected_brands([])
    
    def load_brands_from_db(self):
        for i in reversed(range(self.brands_grid_layout.count())):
            widget = self.brands_grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        self.brand_cards = []
        
        try:
            brands = config.get_all_brands()
            self.product_filter.load_brand_mappings()
        except Exception:
            brands = []
        
        if not brands:
            no_brands_label = QLabel("Нет сохраненных брендов.")
            no_brands_label.setStyleSheet("font-size: 16px; color: #6c757d;")
            no_brands_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.brands_grid_layout.addWidget(no_brands_label, 0, 0)
            return
        
        for brand_data in brands:
            brand_card = BrandCard(brand_data, True)
            
            if brand_data['id'] in self.product_filter.selected_brands:
                brand_card.is_selected = True
                brand_card.update_appearance()
            self.brand_cards.append(brand_card)
        
        self.update_brands_grid_layout()
    
    def create_sales_section(self):
        sales_widget = QWidget()
        sales_widget.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout(sales_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 20, 30, 20)
        
        title_label = QLabel("Продажи")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;")
        layout.addWidget(title_label)
        
        period_container = QWidget()
        period_container.setStyleSheet("background-color: white;")
        period_layout = QHBoxLayout(period_container)
        
        period_layout.addStretch()
        
        period_button = QPushButton("Выбрать период")
        period_button.setFixedHeight(40)
        period_button.setStyleSheet("""
            QPushButton { 
                background-color: #3498db; 
                color: white; 
                border: none; 
                border-radius: 8px; 
                font-size: 14px; 
                font-weight: bold; 
                min-width: 150px;
            } 
            QPushButton:hover { 
                background-color: #2980b9; 
            }
        """)
        period_button.clicked.connect(self.select_period)
        period_layout.addWidget(period_button)
        
        period_layout.addStretch()
        
        layout.addWidget(period_container)
        
        self.period_label = QLabel("Период не выбран")
        self.period_label.setStyleSheet("font-size: 14px; color: #6c757d; font-style: italic;")
        self.period_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.period_label)
        
        chart_container = QWidget()
        chart_container.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px;")
        chart_container.setMinimumHeight(400)
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(10, 10, 10, 10)
        
        self.sales_chart_view = QChartView()
        self.sales_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_layout.addWidget(self.sales_chart_view)
        
        layout.addWidget(chart_container, 1)
        
        buttons_widget = QWidget()
        buttons_widget.setStyleSheet("background-color: white;")
        buttons_layout = QHBoxLayout(buttons_widget)
        
        back_button = QPushButton("Назад")
        back_button.setFixedHeight(45)
        back_button.setStyleSheet("""
            QPushButton { 
                background-color: #95a5a6; 
                color: white; 
                border: none; 
                border-radius: 8px; 
                font-size: 16px; 
                font-weight: bold; 
                min-width: 120px;
            } 
            QPushButton:hover { 
                background-color: #7f8c8d; 
            }
        """)
        back_button.clicked.connect(self.show_all_products)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(back_button)
        
        layout.addWidget(buttons_widget)
        
        self.create_initial_sales_chart()
        
        return sales_widget
    
    def create_initial_sales_chart(self):
        try:
            sales_data = config.get_sales_data()
            chart = self.create_sales_chart(sales_data)
        except Exception:
            chart = self.create_sales_chart(None)
        
        self.sales_chart_view.setChart(chart)
    
    def create_sales_chart(self, sales_data=None):
        if sales_data is None or len(sales_data) == 0:
            set0 = QBarSet("Продажи")
            set0.append(0)
            
            categories = ["Нет данных"]
            chart_title = "Продажи (нет данных)"
        else:
            set0 = QBarSet("Продажи")
            
            for sale in sales_data:
                set0.append(sale['total_sales'])
            
            categories = [sale['date'] for sale in sales_data]
            chart_title = f"Продажи ({len(sales_data)} дней)"
        
        set0.setColor(QColor("#3498db"))
        
        series = QBarSeries()
        series.append(set0)
        
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(chart_title)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        axisX = QBarCategoryAxis()
        axisX.append(categories)
        chart.addAxis(axisX, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axisX)
        
        max_value = 0
        if sales_data and len(sales_data) > 0:
            max_value = max(sale['total_sales'] for sale in sales_data)
        
        if max_value == 0:
            max_value = 1000
        
        axisY = QValueAxis()
        axisY.setRange(0, max_value * 1.1)
        axisY.setTitleText("Сумма (руб)")
        axisY.setLabelFormat("%.0f")
        chart.addAxis(axisY, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axisY)
        
        chart.setTitleFont(QFont("Arial", 14, QFont.Weight.Bold))
        chart.setTitleBrush(QColor("#2c3e50"))
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.setBackgroundBrush(QColor("#f8f9fa"))
        
        return chart
    
    def update_sales_chart(self):
        try:
            if not self.current_user.get('is_first_user', False):
                chart = self.create_sales_chart(None)
                self.sales_chart_view.setChart(chart)
                return
            
            sales_data = []
            
            if self.selected_period:
                start_date, end_date = self.selected_period
                sales_data = config.get_sales_data(
                    start_date.toString('yyyy-MM-dd'),
                    end_date.toString('yyyy-MM-dd')
                )
            else:
                sales_data = config.get_sales_data()
            
            if not sales_data:
                empty_chart = self.create_sales_chart(None)
                self.sales_chart_view.setChart(empty_chart)
                return
                
            chart = self.create_sales_chart(sales_data)
            
            self.sales_chart_view.setChart(chart)
        except Exception:
            chart = self.create_sales_chart(None)
            self.sales_chart_view.setChart(chart)
    
    def select_period(self):
        dialog = PeriodSelectionDialog(self)
        
        for date_edit in [dialog.start_date_edit, dialog.end_date_edit]:
            calendar = date_edit.calendarWidget()
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
                }
                QCalendarWidget QMenu {
                    color: #000000;
                }
                QCalendarWidget QWidget {
                    alternate-background-color: #f8f9fa;
                }
            """)
        
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            start_date, end_date = dialog.get_period()
            self.selected_period = (start_date, end_date)
            
            period_text = f"Период: с {start_date.toString('dd.MM.yyyy')} по {end_date.toString('dd.MM.yyyy')}"
            self.period_label.setText(period_text)
            
            self.update_sales_chart()
    
    def update_grid_layout(self):
        columns_count = self.get_columns_count()
        
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)
        
        for i, card in enumerate(self.product_cards):
            row = i // columns_count
            col = i % columns_count
            self.grid_layout.addWidget(card, row, col)
        
        self.adjust_cards_size()
    
    def update_brands_grid_layout(self):
        columns_count = self.get_columns_count()
        
        for i in reversed(range(self.brands_grid_layout.count())):
            self.brands_grid_layout.itemAt(i).widget().setParent(None)
        
        for i, card in enumerate(self.brand_cards):
            row = i // columns_count
            col = i % columns_count
            self.brands_grid_layout.addWidget(card, row, col)
        
        self.adjust_cards_size()
    
    def get_columns_count(self):
        content_width = self.centralWidget().width() - 250
        available_width = content_width - 60
        
        if available_width >= 1600:
            return 5
        elif available_width >= 1300:
            return 4
        elif available_width >= 1000:
            return 3
        elif available_width >= 700:
            return 2
        else:
            return 1
    
    def adjust_cards_size(self):
        if self.current_mode == "products":
            cards = self.product_cards
        elif self.current_mode == "brands":
            cards = self.brand_cards
        else:
            return
            
        if not cards:
            return
            
        content_width = self.centralWidget().width() - 250
        available_width = content_width - 60
        
        if available_width > 0:
            columns_count = self.get_columns_count()
            card_width = (available_width - (columns_count - 1) * 15) // columns_count
            
            if self.current_mode == "products":
                card_height = card_width * 1.2
            else:
                card_height = card_width * 0.8
                
            card_width = max(180, min(card_width, 300))
            card_height = max(220, min(card_height, 350))
            
            for card in cards:
                card.setFixedSize(card_width, card_height)
    
    def show_add_brand_dialog(self):
        if not self.current_user.get('is_first_user', False):
            self.show_disabled_function_message()
            return
            
        dialog = AddBrandDialog(self)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            self.load_brands_from_db()

    def create_content_sections(self):
        products_section = self.create_products_section()
        self.content_stack.addWidget(products_section)
        
        placeholder_widget = QWidget()
        placeholder_widget.setStyleSheet("background-color: white;")
        self.content_stack.addWidget(placeholder_widget)
        
        cart_section = self.create_cart_section()
        self.content_stack.addWidget(cart_section)
        
        employees_section = self.create_employees_section()
        self.content_stack.addWidget(employees_section)
        
        brands_section = self.create_brands_section()
        self.content_stack.addWidget(brands_section)
        
        sales_section = self.create_sales_section()
        self.content_stack.addWidget(sales_section)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())