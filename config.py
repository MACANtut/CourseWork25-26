import psycopg2
from psycopg2 import OperationalError
import hashlib
from datetime import datetime

def connect_postgres():
    db_params = {
        'host': '5.183.188.132',
        'database': '2025_psql_gri',
        'user': '2025_psql_g_usr',
        'password': 'aYQ2XzT2plld4zli', 
        'port': '5432'
    }
    
    try:
        connection = psycopg2.connect(**db_params)
        return connection
    except OperationalError:
        return None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(user_data):
    connection = connect_postgres()
    if not connection:
        return False, "Ошибка подключения к базе данных"
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (user_data['email'],))
        if cursor.fetchone():
            cursor.close()
            connection.close()
            return False, "Пользователь с таким email уже существует"
        
        cursor.execute("SELECT user_id FROM user_credentials WHERE username = %s", (user_data['username'],))
        if cursor.fetchone():
            cursor.close()
            connection.close()
            return False, "Пользователь с таким логином уже существует"
        
        cursor.execute("""
            INSERT INTO users (first_name, last_name, patronymic, birth_date, email)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING user_id
        """, (
            user_data['first_name'],
            user_data['last_name'],
            user_data['patronymic'] if user_data['patronymic'] else None,
            user_data['birth_date'] if user_data['birth_date'] else None,
            user_data['email']
        ))
        
        user_id = cursor.fetchone()[0]
        
        password_hash = hash_password(user_data['password'])
        
        cursor.execute("""
            INSERT INTO user_credentials (user_id, username, password_hash)
            VALUES (%s, %s, %s)
        """, (user_id, user_data['username'], password_hash))
        
        connection.commit()
        
        cursor.close()
        connection.close()
        
        return True, f"Пользователь {user_data['first_name']} {user_data['last_name']} успешно зарегистрирован"
        
    except Exception as e:
        if connection:
            connection.rollback()
            cursor.close()
            connection.close()
        return False, f"Ошибка при регистрации: {e}"

def authenticate_user(username, password):
    connection = connect_postgres()
    if not connection:
        return False, "Ошибка подключения к базе данных"
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT uc.user_id, uc.password_hash, u.first_name, u.last_name, u.email
            FROM user_credentials uc
            JOIN users u ON uc.user_id = u.user_id
            WHERE uc.username = %s
        """, (username,))
        
        user_result = cursor.fetchone()
        
        if not user_result:
            cursor.close()
            connection.close()
            return False, "Неверный логин или пароль"
        
        user_id, stored_hash, first_name, last_name, email = user_result
        
        input_hash = hash_password(password)
        
        if input_hash != stored_hash:
            cursor.close()
            connection.close()
            return False, "Неверный логин или пароль"
        
        cursor.close()
        connection.close()
        
        return True, {
            'user_id': user_id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'username': username
        }
        
    except Exception as e:
        cursor.close()
        connection.close()
        return False, f"Ошибка аутентификации: {e}"

def create_tables():
    connection = connect_postgres()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                patronymic VARCHAR(50),
                birth_date DATE,
                email VARCHAR(100) UNIQUE NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_credentials (
                credential_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                employee_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                position VARCHAR(50) DEFAULT 'Админ',
                hire_date DATE DEFAULT CURRENT_DATE,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS brands (
                brand_id SERIAL PRIMARY KEY,
                brand_name VARCHAR(100) UNIQUE NOT NULL,
                image_url TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id SERIAL PRIMARY KEY,
                article VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(200) NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                brand_id INTEGER REFERENCES brands(brand_id) ON DELETE SET NULL,
                category VARCHAR(100),
                material VARCHAR(100),
                color VARCHAR(50),
                size VARCHAR(20),
                country VARCHAR(50),
                gender VARCHAR(20),
                season VARCHAR(20),
                image_url TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                cart_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                article VARCHAR(50) REFERENCES products(article) ON DELETE CASCADE,
                quantity INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, article)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount DECIMAL(10, 2) NOT NULL,
                status VARCHAR(20) DEFAULT 'Завершен'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                order_item_id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(order_id) ON DELETE CASCADE,
                article VARCHAR(50) REFERENCES products(article) ON DELETE SET NULL,
                product_name VARCHAR(200) NOT NULL,
                quantity INTEGER NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                total_price DECIMAL(10, 2) NOT NULL
            )
        """)
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
        
    except Exception:
        if connection:
            connection.rollback()
            cursor.close()
            connection.close()
        return False

def get_all_products():
    connection = connect_postgres()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT 
                p.product_id,
                p.article,
                p.name,
                p.price,
                p.category,
                p.material,
                p.color,
                p.size,
                p.country,
                p.gender,
                p.season,
                p.image_url,
                b.brand_name
            FROM products p
            LEFT JOIN brands b ON p.brand_id = b.brand_id
            ORDER BY p.name
        """)
        
        products = []
        for row in cursor.fetchall():
            products.append({
                'id': row[0],
                'article': row[1],
                'name': row[2],
                'price': str(row[3]),
                'category': row[4] if row[4] else '',
                'material': row[5] if row[5] else '',
                'color': row[6] if row[6] else '',
                'size': row[7] if row[7] else '',
                'country': row[8] if row[8] else '',
                'gender': row[9] if row[9] else '',
                'season': row[10] if row[10] else '',
                'image_url': row[11] if row[11] else '',
                'brand': row[12] if row[12] else ''
            })
        
        cursor.close()
        connection.close()
        return products
        
    except Exception:
        cursor.close()
        connection.close()
        return []

def add_product(product_data):
    connection = connect_postgres()
    if not connection:
        return False, "Ошибка подключения к базе данных"
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("SELECT product_id FROM products WHERE article = %s", (product_data['article'],))
        if cursor.fetchone():
            cursor.close()
            connection.close()
            return False, "Товар с таким артикулом уже существует"
        
        brand_id = None
        if product_data.get('brand') and product_data['brand'].strip():
            cursor.execute("SELECT brand_id FROM brands WHERE brand_name = %s", (product_data['brand'],))
            brand_result = cursor.fetchone()
            if brand_result:
                brand_id = brand_result[0]
        
        image_url = product_data.get('image_url', '')
        if image_url == '':
            image_url = None
        
        cursor.execute("""
            INSERT INTO products (
                article, name, price, brand_id, category, material,
                color, size, country, gender, season, image_url
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING product_id
        """, (
            product_data['article'],
            product_data['name'],
            float(product_data['price']),
            brand_id,
            product_data.get('category', '') or None,
            product_data.get('material', '') or None,
            product_data.get('color', '') or None,
            product_data.get('size', '') or None,
            product_data.get('country', '') or None,
            product_data.get('gender', '') or None,
            product_data.get('season', '') or None,
            image_url
        ))
        
        product_id = cursor.fetchone()[0]
        
        connection.commit()
        cursor.close()
        connection.close()
        return True, product_id
        
    except Exception as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return False, f"Ошибка при добавлении товара: {e}"

def delete_product(product_id):
    connection = connect_postgres()
    if not connection:
        return False, "Ошибка подключения к базе данных"
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("SELECT name FROM products WHERE product_id = %s", (product_id,))
        product_name = cursor.fetchone()
        if not product_name:
            cursor.close()
            connection.close()
            return False, "Товар не найден"
        
        product_name = product_name[0]
        
        cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        
        connection.commit()
        cursor.close()
        connection.close()
        return True, f"Товар '{product_name}' успешно удален"
        
    except Exception as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return False, f"Ошибка при удалении товара: {e}"

def get_all_employees():
    connection = connect_postgres()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT 
                u.first_name,
                u.last_name,
                u.patronymic,
                u.email,
                e.position,
                e.hire_date,
                e.is_active
            FROM employees e
            JOIN users u ON e.user_id = u.user_id
            ORDER BY u.last_name, u.first_name
        """)
        
        employees = []
        for row in cursor.fetchall():
            employees.append({
                'first_name': row[0],
                'last_name': row[1],
                'patronymic': row[2] if row[2] else '',
                'email': row[3],
                'position': row[4] if row[4] else '',
                'hire_date': row[5].strftime('%d.%m.%Y') if row[5] else '',
                'is_active': row[6] if row[6] else False
            })
        
        cursor.close()
        connection.close()
        return employees
        
    except Exception:
        cursor.close()
        connection.close()
        return []

def add_employee(employee_data):
    connection = connect_postgres()
    if not connection:
        return False, "Ошибка подключения к базе данных"
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (employee_data['email'],))
        user_result = cursor.fetchone()
        
        if not user_result:
            cursor.execute("""
                INSERT INTO users (first_name, last_name, patronymic, email)
                VALUES (%s, %s, %s, %s)
                RETURNING user_id
            """, (
                employee_data['first_name'],
                employee_data['last_name'],
                employee_data.get('patronymic'),
                employee_data['email']
            ))
            user_id = cursor.fetchone()[0]
        else:
            user_id = user_result[0]
        
        cursor.execute("SELECT employee_id FROM employees WHERE user_id = %s", (user_id,))
        if cursor.fetchone():
            cursor.close()
            connection.close()
            return False, "Сотрудник с таким email уже существует"
        
        hire_date = employee_data.get('hire_date', '')
        if hire_date:
            try:
                if '.' in hire_date:
                    day, month, year = hire_date.split('.')
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year
                    hire_date = f"{year}-{month}-{day}"
                elif '/' in hire_date:
                    day, month, year = hire_date.split('/')
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year
                    hire_date = f"{year}-{month}-{day}"
            except Exception:
                hire_date = datetime.now().strftime('%Y-%m-%d')
        else:
            hire_date = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute("""
            INSERT INTO employees (user_id, position, hire_date, is_active)
            VALUES (%s, %s, %s, %s)
            RETURNING employee_id
        """, (
            user_id,
            employee_data.get('position', 'Админ'),
            hire_date,
            employee_data.get('is_active', True)
        ))
        
        employee_id = cursor.fetchone()[0]
        
        connection.commit()
        cursor.close()
        connection.close()
        return True, f"Сотрудник успешно добавлен"
        
    except Exception as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return False, f"Ошибка при добавлении сотрудника: {e}"

def check_tables_exist():
    connection = connect_postgres()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            ) AND EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'user_credentials'
            ) AND EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'employees'
            ) AND EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'brands'
            ) AND EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'products'
            ) AND EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'cart'
            ) AND EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'orders'
            ) AND EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'order_items'
            )
        """)
        
        exists = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        
        return exists
        
    except Exception:
        cursor.close()
        connection.close()
        return False

def get_all_brands():
    connection = connect_postgres()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT brand_id, brand_name, image_url
            FROM brands
            ORDER BY brand_name
        """)
        
        brands = []
        for row in cursor.fetchall():
            brands.append({
                'id': row[0],
                'name': row[1],
                'image_url': row[2] if row[2] else ""
            })
        
        cursor.close()
        connection.close()
        return brands
        
    except Exception:
        cursor.close()
        connection.close()
        return []

def add_brand(brand_name, image_url=None):
    connection = connect_postgres()
    if not connection:
        return False, "Ошибка подключения к базе данных"
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("SELECT brand_id FROM brands WHERE brand_name = %s", (brand_name,))
        if cursor.fetchone():
            cursor.close()
            connection.close()
            return False, "Бренд с таким названием уже существует"
        
        if image_url == "":
            image_url = None
        
        cursor.execute("""
            INSERT INTO brands (brand_name, image_url)
            VALUES (%s, %s)
            RETURNING brand_id
        """, (brand_name, image_url))
        
        brand_id = cursor.fetchone()[0]
        
        connection.commit()
        cursor.close()
        connection.close()
        return True, brand_id
        
    except Exception as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return False, f"Ошибка при добавлении бренда: {e}"

def get_brand_id_by_name(brand_name):
    connection = connect_postgres()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("SELECT brand_id FROM brands WHERE brand_name = %s", (brand_name,))
        result = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return result[0] if result else None
        
    except Exception:
        cursor.close()
        connection.close()
        return None

def get_user_cart(user_id):
    connection = connect_postgres()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT 
                c.article,
                p.product_id,
                p.name,
                p.price,
                c.quantity
            FROM cart c
            JOIN products p ON c.article = p.article
            WHERE c.user_id = %s
        """, (user_id,))
        
        cart_items = []
        for row in cursor.fetchall():
            cart_items.append({
                'product_id': row[1],
                'article': row[0],
                'name': row[2],
                'price': str(row[3]),
                'quantity': row[4]
            })
        
        cursor.close()
        connection.close()
        return cart_items
        
    except Exception:
        cursor.close()
        connection.close()
        return []

def add_to_cart(user_id, product_id, quantity=1):
    connection = connect_postgres()
    if not connection:
        return False, "Ошибка подключения к базе данных"
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("SELECT article FROM products WHERE product_id = %s", (product_id,))
        product_result = cursor.fetchone()
        
        if not product_result:
            cursor.close()
            connection.close()
            return False, "Товар не найден"
        
        article = product_result[0]
        
        cursor.execute("""
            SELECT quantity FROM cart 
            WHERE user_id = %s AND article = %s
        """, (user_id, article))
        
        result = cursor.fetchone()
        
        if result:
            new_quantity = result[0] + quantity
            cursor.execute("""
                UPDATE cart 
                SET quantity = %s
                WHERE user_id = %s AND article = %s
            """, (new_quantity, user_id, article))
        else:
            cursor.execute("""
                INSERT INTO cart (user_id, article, quantity)
                VALUES (%s, %s, %s)
            """, (user_id, article, quantity))
        
        connection.commit()
        
        cursor.execute("SELECT name FROM products WHERE article = %s", (article,))
        product_name = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        return True, f"Товар '{product_name}' добавлен в корзину"
        
    except Exception as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return False, f"Ошибка при добавлении в корзину: {e}"

def update_cart_item(user_id, article, quantity):
    connection = connect_postgres()
    if not connection:
        return False, "Ошибка подключения к базе данных"
    
    try:
        cursor = connection.cursor()
        
        if quantity <= 0:
            cursor.execute("""
                DELETE FROM cart 
                WHERE user_id = %s AND article = %s
            """, (user_id, article))
        else:
            cursor.execute("""
                UPDATE cart 
                SET quantity = %s
                WHERE user_id = %s AND article = %s
            """, (quantity, user_id, article))
        
        connection.commit()
        
        cursor.execute("SELECT name FROM products WHERE article = %s", (article,))
        product_name = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        if quantity <= 0:
            return True, f"Товар удален из корзины"
        else:
            return True, f"Количество товара обновлено"
        
    except Exception as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return False, f"Ошибка при обновлении корзины: {e}"

def remove_from_cart(user_id, article):
    connection = connect_postgres()
    if not connection:
        return False, "Ошибка подключения к базе данных"
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            DELETE FROM cart 
            WHERE user_id = %s AND article = %s
        """, (user_id, article))
        
        connection.commit()
        
        cursor.execute("SELECT name FROM products WHERE article = %s", (article,))
        product_name = cursor.fetchone()
        
        cursor.close()
        connection.close()
        return True, f"Товар удален из корзины"
        
    except Exception as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return False, f"Ошибка при удалении из корзины: {e}"

def clear_cart(user_id):
    connection = connect_postgres()
    if not connection:
        return False, "Ошибка подключения к базе данных"
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            DELETE FROM cart 
            WHERE user_id = %s
        """, (user_id,))
        
        connection.commit()
        cursor.close()
        connection.close()
        return True, "Корзина очищена"
        
    except Exception as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return False, f"Ошибка при очистке корзины: {e}"

def get_product_by_article(article):
    connection = connect_postgres()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT product_id, article, name, price 
            FROM products WHERE article = %s
        """, (article,))
        result = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        if result:
            return {
                'product_id': result[0],
                'article': result[1],
                'name': result[2],
                'price': str(result[3])
            }
        return None
        
    except Exception:
        cursor.close()
        connection.close()
        return None

def get_product_by_id(product_id):
    connection = connect_postgres()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT product_id, article, name, price 
            FROM products WHERE product_id = %s
        """, (product_id,))
        result = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        if result:
            return {
                'product_id': result[0],
                'article': result[1],
                'name': result[2],
                'price': str(result[3])
            }
        return None
        
    except Exception:
        cursor.close()
        connection.close()
        return None

def get_brands_by_ids(brand_ids):
    connection = connect_postgres()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        
        if not brand_ids:
            return []
        
        placeholders = ','.join(['%s'] * len(brand_ids))
        cursor.execute(f"""
            SELECT brand_id, brand_name, image_url
            FROM brands
            WHERE brand_id IN ({placeholders})
            ORDER BY brand_name
        """, tuple(brand_ids))
        
        brands = []
        for row in cursor.fetchall():
            brands.append({
                'id': row[0],
                'name': row[1],
                'image_url': row[2] if row[2] else ""
            })
        
        cursor.close()
        connection.close()
        return brands
        
    except Exception:
        cursor.close()
        connection.close()
        return []

def create_order(user_id, cart_items):
    connection = connect_postgres()
    if not connection:
        return False, "Ошибка подключения к базе данных"
    
    try:
        cursor = connection.cursor()
        
        total_amount = sum(float(item['price']) * item['quantity'] for item in cart_items)
        
        cursor.execute("""
            INSERT INTO orders (user_id, total_amount, status)
            VALUES (%s, %s, %s)
            RETURNING order_id
        """, (user_id, total_amount, 'Завершен'))
        
        order_id = cursor.fetchone()[0]
        
        for item in cart_items:
            cursor.execute("""
                INSERT INTO order_items (order_id, article, product_name, quantity, price, total_price)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                order_id,
                item['article'],
                item['name'],
                item['quantity'],
                float(item['price']),
                float(item['price']) * item['quantity']
            ))
        
        cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
        
        connection.commit()
        cursor.close()
        connection.close()
        return True, order_id
        
    except Exception as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return False, f"Ошибка при создании заказа: {e}"

def get_user_orders(user_id):
    connection = connect_postgres()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("SELECT MIN(user_id) FROM users")
        first_user_id = cursor.fetchone()[0]
        
        if user_id == first_user_id:
            cursor.close()
            connection.close()
            return []
        
        cursor.execute("""
            SELECT 
                o.order_id,
                o.order_date,
                o.total_amount,
                o.status,
                COUNT(oi.order_item_id) as items_count
            FROM orders o
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.user_id = %s
            GROUP BY o.order_id, o.order_date, o.total_amount, o.status
            ORDER BY o.order_date DESC
        """, (user_id,))
        
        orders = []
        for row in cursor.fetchall():
            orders.append({
                'order_id': row[0],
                'order_date': row[1].strftime('%d.%m.%Y %H:%M') if row[1] else '',
                'total_amount': str(row[2]),
                'status': row[3],
                'items_count': row[4]
            })
        
        cursor.close()
        connection.close()
        return orders
        
    except Exception:
        cursor.close()
        connection.close()
        return []

def get_sales_data(start_date=None, end_date=None):
    connection = connect_postgres()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("SELECT MIN(user_id) FROM users")
        first_user_id = cursor.fetchone()[0]
        
        query = """
            SELECT 
                DATE(o.order_date) as sale_date,
                COUNT(*) as orders_count,
                SUM(o.total_amount) as total_sales
            FROM orders o
            WHERE o.status = 'Завершен'
            AND o.user_id != %s
        """
        
        params = [first_user_id]
        
        if start_date and end_date:
            query += " AND DATE(o.order_date) BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        
        query += """
            GROUP BY DATE(o.order_date)
            ORDER BY sale_date
        """
        
        cursor.execute(query, params)
        
        sales_data = []
        for row in cursor.fetchall():
            sales_data.append({
                'date': row[0].strftime('%d.%m.%Y') if row[0] else '',
                'orders_count': row[1],
                'total_sales': float(row[2]) if row[2] else 0
            })
        
        cursor.close()
        connection.close()
        return sales_data
        
    except Exception:
        cursor.close()
        connection.close()
        return []

def get_order_details(order_id):
    connection = connect_postgres()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("SELECT MIN(user_id) FROM users")
        first_user_id = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT 
                o.order_id,
                o.order_date,
                o.total_amount,
                o.status,
                u.first_name,
                u.last_name,
                u.email
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            WHERE o.order_id = %s
            AND o.user_id != %s
        """, (order_id, first_user_id))
        
        order_result = cursor.fetchone()
        
        if not order_result:
            cursor.close()
            connection.close()
            return None
        
        cursor.execute("""
            SELECT 
                oi.product_name,
                oi.quantity,
                oi.price,
                oi.total_price,
                oi.article
            FROM order_items oi
            WHERE oi.order_id = %s
            ORDER BY oi.order_item_id
        """, (order_id,))
        
        items = []
        for row in cursor.fetchall():
            items.append({
                'product_name': row[0],
                'quantity': row[1],
                'price': str(row[2]),
                'total_price': str(row[3]),
                'article': row[4] if row[4] else 'Не указан'
            })
        
        cursor.close()
        connection.close()
        
        return {
            'order_id': order_result[0],
            'order_date': order_result[1].strftime('%d.%m.%Y %H:%M') if order_result[1] else '',
            'total_amount': str(order_result[2]),
            'status': order_result[3],
            'customer_name': f"{order_result[4]} {order_result[5]}",
            'customer_email': order_result[6],
            'items': items
        }
        
    except Exception:
        cursor.close()
        connection.close()
        return None