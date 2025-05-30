import datetime
import sqlite3
from contextlib import closing
import logging
import mysql
from flask import Flask, render_template, request, jsonify, url_for, redirect, session, flash
import requests
from mysql.connector import Error
import sys
from db import cur, cnx

app = Flask(__name__)
app.secret_key = '2weit-flower'

REGISTRATION_API_URL = "http://127.0.0.1:5000/registration"

def get_db_connection():
    conn = sqlite3.connect('reviews.db')
    conn.row_factory = sqlite3.Row
    return conn

def check_user_in_db(email, password):
    conn = sqlite3.connect('Users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?",(email, password))
    user = cursor.fetchone()

    conn.close()
    return user is not None


@app.route("/2weit/registration")
def registration_page():
    return render_template("registration.html")

@app.route("/2weit/register", methods=["POST"])
def register_user():
    try:

        user_data = {
            "name": request.form.get("name"),
            "username": request.form.get("username"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone"),
            "password": request.form.get("password")
        }

        if not all(user_data.values()):
            return jsonify({"success": False, "message": "All fields are required"}), 400

        response = requests.post(REGISTRATION_API_URL, json=user_data)

        if response.status_code == 201:
            return jsonify({
                "success": True,
                "message": "Регистрация прошла успешно!",
                "redirect": "/2weit"
            })
        else:
            error_message = response.json().get("message", "Ошибка регистрации")
            return jsonify({"success": False, "message": error_message}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/2weit", methods=['POST','GET'])
def main_page():
    return render_template("main.html")

LOGIN_API_URL = "http://127.0.0.1:5000/login"


@app.route("/2weit/login", methods=["GET", "POST"])
def login_page():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email == 'kristina@2weit.ru' and password == '2weit':
            return redirect(url_for('admin_page'))

        user_exists = check_user_in_db(email, password)

        if user_exists:
            return redirect(url_for('main_page'))
        else:
            flash('Пользователь с такими данными не найден')
            return render_template("login.html")

    return render_template("login.html")


@app.route("/2weit/logine", methods=["POST"])
def logine_user():
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"success": False, "message": "Необходимо отправить JSON данные"}), 400

        email = request_data.get("email")
        password = request_data.get("password")

        if not email or not password:
            return jsonify({"success": False, "message": "Все поля обязательны для заполнения"}), 400

        # Проверяем сначала специальный аккаунт администратора
        if email == 'kristina@2weit.ru' and password == '2weit':
            return jsonify({
                "success": True,
                "message": "Авторизация администратора прошла успешно!",
                "redirect": "/2weit/admin",
                "token": "user_token"  # Здесь должен быть реальный токен
            })

        # Проверяем обычного пользователя в БД
        user_exists = check_user_in_db({"email"}, {"password"})
        if user_exists:
            return jsonify({
                "success": True,
                "message": "Авторизация прошла успешно!",
                "redirect": "/2weit",
                "token": "user_token"
            })
        else:
            return jsonify({"success": False, "message": "Неверный email или пароль"}), 401

    except Exception as e:
        return jsonify({"success": False, "message": f"Ошибка сервера: {str(e)}"}), 500

@app.route("/2weit/reviews", methods=['GET'])
def reviews_page():
    #print(1)
    response = requests.get('http://127.0.0.1:5000/reviews')
   # print(response.json())
    param = response.json()
    coments=param['Reviews']
    print(coments)
    html = ""
    for coment in coments:
        html_temp = f"""
        <div class="review">
            <h3>{coment['username']}</h3>
            <p>{coment['comment']}</p>
            <small>{coment['date'] if coment['date'] else ''}</small>
        </div>
        """
        html += html_temp

    return render_template("reviews.html",param=html)

REVIEWS_API_URL = "http://127.0.0.1:5000/reviews"

@app.route("/2weit/review", methods=["POST"])
def review_user():
    try:
        request_data = request.get_json()
        print (1)
        if not request_data:
            return jsonify({"success": False, "message": "Необходимо отправить JSON данные"}), 400

        username = request_data.get("username")
        comment = request_data.get("comment")
        email = request_data.get("email")

        if not username or not comment:
            missing_fields = []
            if not username: missing_fields.append("username")
            if not comment: missing_fields.append("comment")
            if not email: missing_fields.append("email")

            return jsonify({
                "success": False,
                "message": "Все поля обязательны для заполнения",
                "missing_fields": missing_fields
            }), 400

        sql = "INSERT INTO Reviews (username, comment, email) VALUES (%s, %s)"
        cur.execute(sql, (username, comment, email))
        cur._connection.commit()

        return jsonify({
            "success": True,
            "message": "Отзыв успешно добавлен!",
            "redirect": "/2weit/reviews"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Ошибка сервера при добавлении отзыва: {str(e)}"
        }), 500

@app.route("/2weit/menu", methods=["GET"])
def menu_page():
    response = requests.get('http://127.0.0.1:5000/api/menu')
    param = response.json()
    print("Ответ API:", param)

    # Группируем цветы по имени, суммируя количество
    flowers_dict = {}
    for flower in param['flowers']:
        name = flower['name']
        if name in flowers_dict:
            flowers_dict[name]['quantity'] = flower['quantity']
        else:
            flowers_dict[name] = flower.copy()  # Создаем копию, чтобы не изменять оригинал

    html = ""
    for flower in flowers_dict.values():
        html_temp = f"""
            <div class="product-card">
                <div class="product-info">
                    <h3 class="product-name">{flower['name']}</h3>  
                    <p class="product-description">Сорт: {flower['sort']}</p>  
                    <p class="product-description">Цвет: {flower['color']}</p> 
                    <p class="product-description">В наличии: {flower['quantity']} шт.</p> 
                    <p class="product-price"> {flower['price']}₽ за штуку.</p>
                    <button class="action-btn add-to-cart" data-name="{flower['name']}"
                    data-sort="{flower['sort']}"
                    data-color="{flower['color']}"
                    data-price="{flower['price']}">
                    Добавить в корзину</button>
                </div>
            </div> 
            """
        html += html_temp

    return render_template("menu.html", param=html)

@app.route('/2weit/order/cart', methods=['POST'])
def cart_page():
    flower_name = request.form.get('flower_name')
    flower_sort = request.form.get('flower_sort')
    flower_color = request.form.get('flower_color')
    flower_price = request.form.get('flower_price')
    quantity = int(request.form.get('quantity', 1))
    print(flower_price)
    try:
        print(flower_price)
        flower_price = float(flower_price)
    except ValueError:
        print(flower_price)
        print("error")
        flower_price = 1.0

    if 'cart' not in session:
        session['cart'] = []

    found = False
    for item in session['cart']:
        if (item['name'] == flower_name and
            item['sort'] == flower_sort and
            item['color'] == flower_color):
            item['quantity'] += quantity
            found = True
            break

    if not found:
        session['cart'].append({
            'name': flower_name,
            'sort': flower_sort,
            'color': flower_color,
            'price': flower_price,
            'quantity': quantity
        })

    session.modified = True
    return redirect(url_for('order_page'))

@app.route("/2weit/order", methods=['GET', 'POST'])
def order_page():
    # Fetch the cart from the session
    cart = session.get('cart', [])
    total_price = sum(item['price'] * item.get('quantity', 1) for item in cart)

    if request.method == 'POST':
        try:
            # Get form data
            name = request.form['name']
            address = request.form['address']
            email = request.form['email']
            payment_method = request.form['payment_method']
            comment = request.form.get('comment', '')

            # Get discount information from form
            discount_percent = float(request.form.get('discount_percent', 0))
            final_price = float(request.form.get('final_price', total_price))
            discount_amount = total_price - final_price
            discount_id = request.form.get('discount_id', '').strip() or None

            # Save the order to the database with all discount information
            cur.execute("""
                INSERT INTO orders (
                    customer_name, address, email, payment_method,
                    comment, total_price, discount_percent,
                    discount_amount, final_amount, discount_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                name, address, email, payment_method,
                comment, total_price, discount_percent,
                discount_amount, final_price, discount_id
            ))

            order_id = cur.lastrowid

            # Save each item in the cart to the order_items table
            for item in cart:
                cur.execute("""
                    INSERT INTO order_items (
                        order_id, flower_name, flower_sort, color, quantity, price
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                    order_id,
                    item['name'],
                    item.get('sort', ''),
                    item.get('color', ''),
                    item.get('quantity', 1),
                    item['price']
                ))

            # Commit the transaction
            cnx.commit()

            # Clear the cart from the session
            session.pop('cart', None)

            # Redirect to the order success page
            return redirect(url_for('order_success', order_id=order_id))

        except Exception as e:
            # Handle exceptions (e.g., log the error, show an error message)
            cnx.rollback()  # Rollback in case of error
            return "An error occurred while processing your order: {}".format(str(e)), 500

    # If GET request, render the order page
    return render_template('order.html', cart=cart, total_price=total_price)

@app.route('/apply_discount', methods=['POST'])
def apply_discount():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()

    # Проверяем обязательные поля
    required_fields = ["user_name", "original_amount"]
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return jsonify({
            "error": "Не заполнены обязательные поля",
            "missing_fields": missing_fields
        }), 400

    try:
        original_amount = float(data["original_amount"])
    except (ValueError, TypeError):
        return jsonify({
            "error": "original_amount должен быть числом"
        }), 400

    user_name = data["user_name"]

    try:
        cur = cnx.cursor()  # Используем ваше соединение cnx

        # Исправленный запрос - убедитесь, что таблица и поля существуют
        sql = """
        SELECT discount_percent, discount_id  # Изменил id на discount_id
        FROM discounts  # Убедитесь, что таблица называется именно так
        WHERE user_name = %s
        """
        cur.execute(sql, (user_name,))
        result = cur.fetchone()

        if not result:
            return jsonify({
                "status": "invalid",
                "message": "Скидка для данного пользователя не найдена",
                "original_amount": original_amount
            }), 404

        # Проверяем, что результат содержит оба ожидаемых значения
        if len(result) < 2:
            return jsonify({
                "error": "Некорректные данные скидки в базе"
            }), 500

        discount_percent = float(result[0])
        discount_id = result[1]

        # Проверка корректности процента скидки
        if discount_percent < 0 or discount_percent > 100:
            return jsonify({
                "error": "Некорректный размер скидки (должен быть от 0 до 100)"
            }), 400

        # Рассчитываем скидку
        discount_amount = (original_amount * discount_percent) / 100
        final_amount = original_amount - discount_amount

        return jsonify({
            "status": "success",
            "message": "Скидка применена",
            "discount_percent": discount_percent,
            "discount_amount": discount_amount,
            "final_amount": final_amount,
            "user_name": user_name,
            "discount_id": discount_id
        })

    except Exception as e:
        print(f"Ошибка в apply_discount: {str(e)}")
        return jsonify({
            "error": "Внутренняя ошибка сервера",
            "details": str(e)
        }), 500

    finally:
        if 'cur' in locals():
            cur.close()

@app.route("/order/success/<int:order_id>")
def order_success(order_id):
    return render_template('order_success.html', order_id=order_id)

@app.route("/2weit/order/clear_cart", methods=['POST'])
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('order_page'))

@app.route("/2weit/contact", methods=["GET"])
def contact_page():
    return render_template("contact.html")

@app.route("/2weit/admin", methods=["GET"])
def admin_page():
    return render_template("admin.html")

@app.route("/2weit/orders", methods=["GET"])
def orders_page():
    try:
        response = requests.get('http://127.0.0.1:5000/api/orders')
        response.raise_for_status()
        param = response.json()
        print("Ответ API:", param)

        # Создаем словарь для группировки заказов
        grouped_orders = {}

        for order in param.get('orders', []):
            try:
                order_id = order.get('order_id')
                if not order_id:
                    continue

                # Инициализируем заказ, если его еще нет
                if order_id not in grouped_orders:
                    total_price = float(order.get('total_price', 0))
                    final_amount = float(order.get('final_amount', total_price))
                    discount_percent = float(order.get('discount_percent', 0))
                    discount_amount = float(order.get('discount_amount', 0))

                    grouped_orders[order_id] = {
                        'order_info': {
                            'id': order_id,
                            'customer_name': order.get('customer_name', 'Не указано'),
                            'address': order.get('address', 'Не указан'),
                            'email': order.get('email', 'Не указан'),
                            'payment_method': order.get('payment_method', 'Не указан'),
                            'total_price': total_price,
                            'final_amount': final_amount,
                            'discount_percent': discount_percent,
                            'discount_amount': discount_amount,
                            'comment': order.get('comment', 'нет'),
                            'status': order.get('status', 'new').lower()
                        },
                        'order_items': []
                    }

                # Добавляем товары в заказ
                if order.get('flower_name') or order.get('bouquet_name'):
                    item_name = order.get('flower_name') or order.get('bouquet_name')
                    item_type = 'flower' if order.get('flower_name') else 'bouquet'

                    grouped_orders[order_id]['order_items'].append({
                        'name': item_name,
                        'type': item_type,
                        'sort': order.get('flower_sort', 'Не указан') if item_type == 'flower' else 'Букет',
                        'color': order.get('color', 'Не указан') if item_type == 'flower' else '',
                        'quantity': int(order.get('quantity', 1)),
                        'price': float(order.get('price', 0))
                    })

            except Exception as e:
                print(f"Ошибка обработки заказа {order.get('order_id')}: {str(e)}")
                continue

        # Генерация HTML
        html = ""
        statuses = {
            'new': 'Новый',
            'paid': 'Оплачен',
            'assembled': 'Собран',
            'delivery': 'Доставка',
            'completed': 'Готово'
        }

        for order_id, order_data in grouped_orders.items():
            main_order = order_data['order_info']
            items = order_data['order_items']
            current_status = main_order['status']

            # Формируем информацию о скидке
            discount_info = ""
            if main_order['discount_percent'] > 0:
                discount_info = f"""
                    <p><strong>Скидка:</strong> {main_order['discount_percent']:.0f}% (-{main_order['discount_amount']:.2f} руб.)</p>
                    <p><strong>Сумма без скидки:</strong> {main_order['total_price']:.2f} руб.</p>
                    <p><strong>Итого со скидкой:</strong> {main_order['final_amount']:.2f} руб.</p>
                """
            else:
                discount_info = f"""
                    <p><strong>Сумма:</strong> {main_order['final_amount']:.2f} руб.</p>
                """

            html_temp = f"""
            <div class="order-card {current_status}">
                <div class="order-header">
                    <h3>Заказ #{order_id}</h3>
                </div>
                <div class="order-details">
                    <p><strong>Клиент:</strong> {main_order['customer_name']}</p>
                    <p><strong>Адрес:</strong> {main_order['address']}</p>
                    <p><strong>Email:</strong> {main_order['email']}</p>
                    <p><strong>Способ оплаты:</strong> {main_order['payment_method']}</p>
                    {discount_info}
                    <p><strong>Комментарий:</strong> {main_order['comment']}</p>
                </div>
                <div class="order-items">
                    <h4>Состав заказа:</h4>"""

            for item in items:
                item_type = "Цветок" if item['sort'] else "Букет"
                html_temp += f"""
                    <div class="order-item">
                        <p>{item['name']} ({item_type}{', ' + item['sort'] if item['sort'] else ''}{', ' + item['color'] if item['color'] else ''})</p>
                        <p>{item['quantity']} шт. × {item['price']:.2f} руб. = {item['quantity'] * item['price']:.2f} руб.</p>
                    </div>"""

            html_temp += f"""
                </div>
                <div class="status-actions" data-order-id="{order_id}">
                    <p>Изменить статус:</p>
                </div>
                <div class="status-buttons" data-order-id="{order_id}">"""

            for key, value in statuses.items():
                active_class = "active" if key == current_status else ""
                html_temp += f"""
                    <button class="status-btn {key} {active_class}" data-status="{key}">{value}</button>"""

            html_temp += """
                </div>
            </div>"""
            html += html_temp

        return render_template("orders.html", param=html)

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к API: {str(e)}")
        return render_template("error.html", error="Не удалось загрузить данные заказов")
    except Exception as e:
        print(f"Неожиданная ошибка: {str(e)}")
        return render_template("error.html", error="Произошла ошибка при обработке данных")

@app.route("/api/orders/<int:order_id>/status", methods=["POST"])
def update_order_status(order_id):
    new_status = request.json.get('status')
    # Здесь логика обновления статуса в вашей БД
    # Например:
    # update_order_status_in_db(order_id, new_status)
    return jsonify({"success": True, "message": "Статус обновлен"})

@app.route("/2weit/feedback", methods=["GET"])
def feedback_page():
    response = requests.get('http://127.0.0.1:5000/reviews')
    param = response.json()
    coments = param['Reviews']
    html = ""
    for coment in coments:
        html_temp = f"""
         <div class="review" id="review-{coment['id']}">
             <h3>{coment['username']}</h3>
             <p>{coment['comment']}</p>
             <small>{coment['date'] if coment['date'] else ''}</small>
             <div class="review-actions">
                <button class="action-btn reply-btn" onclick="toggleReplyForm(this)">Ответить</button>
                <button class="action-btn delete-btn" data-id="8"{coment['id']}">Удалить</button>
             </div>
             <div class="reply-form" style="display: none;">
                <textarea placeholder="Ваш ответ..." rows="3"></textarea>
                <button class="action-btn submit-reply-btn">Отправить</button>
                <button class="action-btn cancel-reply-btn" onclick="toggleReplyForm(this)">Отмена</button>
             </div>
         </div>
         """
        html += html_temp
    return render_template("feedback.html", param=html)

@app.route('/delete-review/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    try:
        # Создаем новый курсор (лучше создавать новый для каждого запроса)
        cursor = cnx.cursor(dictionary=True)

        # Проверяем существование отзыва
        cursor.execute("SELECT id FROM Reviews WHERE id = %s", (review_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({"error": "Отзыв не найден."}), 404

        # Удаляем отзыв
        cursor.execute("DELETE FROM Reviews WHERE id = %s", (review_id,))
        cnx.commit()
        cursor.close()

        return jsonify({"message": "Отзыв успешно удален."}), 200

    except mysql.connector.Error as err:
        logging.error(f"Ошибка MySQL при удалении отзыва с ID {review_id}: {err}")
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        logging.error(f"Общая ошибка при удалении отзыва с ID {review_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/2weit/delivery", methods=["GET"])
def delivery_page():
    return render_template("delivery.html")

@app.route("/2weit/availability", methods=["GET"])
def availability_page():
    return render_template("availability.html")

@app.route("/2weit/discount", methods=["GET"])
def discount_page():
    return render_template("discount.html")


@app.route('/add_discount', methods=['POST'])
def add_discount():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Данные не предоставлены"}), 400

    required_fields = ["name", "discount_percent"]
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return jsonify({
            "error": "Не заполнены обязательные поля",
            "missing_fields": missing_fields
        }), 400

    user_name = data["name"]
    discount_percent = float(data["discount_percent"])

    try:
        cur = cnx.cursor(dictionary=True)  # <-- Важное изменение!

        sql_user = "SELECT User_ID FROM Users WHERE name = %s"
        cur.execute(sql_user, (user_name,))
        user_result = cur.fetchone()

        if not user_result:
            return jsonify({
                "error": "Пользователь не найден",
                "user_name": user_name
            }), 404

        user_id = user_result["User_ID"]  # Теперь работает

        sql_discount = """
            INSERT INTO discounts (user_name, discount_percent) 
            VALUES (%s, %s) 
            ON DUPLICATE KEY UPDATE discount_percent = %s
        """
        cur.execute(sql_discount, (user_name, discount_percent, discount_percent))
        cur._connection.commit()

        return jsonify({
            "status": "success",
            "message": "Скидка успешно добавлена/обновлена",
            "user_id": user_id,
            "user_name": user_name,
            "discount_percent": discount_percent
        })

    except Exception as e:
        return jsonify({
            "error": "Ошибка при выполнении запроса",
            "details": str(e)
        }), 500


@app.route('/flower_add', methods=['POST'])
def flower():
    data = request.json

    name = data.get("name")
    sort = data.get("sort")
    color = data.get("color")
    date = data.get("date")
    price = data.get("price")

    sql = f'INSERT INTO flowers (name, sort, color, date, price) VALUES ("{name}", "{sort}", "{color}", "{date}", "{price}")'
    print(sql)

    cur.execute(sql)
    cur._connection.commit()

    return jsonify({"status": "OK", "message": "Цветок добавлен"})


@app.route('/menu', methods=['GET'])
def menu():
    try:
        sql = 'SELECT * FROM flowers'
        cur.execute(sql)
        flowers = []
        for row in cur:
            flowers.append(row)
            print(row)

        return jsonify({
            "status": "OK",
            "count": len(flowers),
            "flowers": flowers
        })
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)})

def get_db_connection():
    return cnx  # Возвращаем уже созданное соединение, а не пытаемся его вызвать

@app.route('/api/orders', methods=['GET'])
def orders():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        sql = 'SELECT * FROM orders JOIN order_items ON orders.id = order_items.order_id;'
        cur.execute(sql)
        orders_list = []

        for row in cur:
            orders_list.append(row)
            print(row)

        cur.close()
        # cnx.close()

        return jsonify({
            "status": "OK",
            "count": len(orders_list),
            "orders": orders_list
        })

    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)})

@app.route('/flower_new_price', methods=['POST'])
def flower_new_price():
    # Проверяем, что запрос содержит JSON
    if not request.is_json:
        return jsonify({"status": "ERROR", "message": "Запрос должен быть в формате JSON"}), 400

    data = request.get_json()
    flower_name = data.get("name")
    new_price = data.get("price")

    if flower_name is None or new_price is None:
        return jsonify({"status": "ERROR", "message": "Название и цена обязательны."}), 400

    try:
        # Безопасный запрос с параметрами
        sql = "UPDATE `flowers` SET `price` = %s WHERE `name` = %s"
        print(f"Executing: {sql} with params: ({new_price}, {flower_name})")

        cur.execute(sql, (new_price, flower_name))
        cur._connection.commit()

        return jsonify({
            "status": "OK",
            "message": f"Цена цветов '{flower_name}' успешно обновлена!",
            "affected_rows": cur.rowcount
        })
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

@app.route('/flower_quantity', methods=['POST'])
def flower_quantity():
    try:
        # Сначала получаем актуальные данные о количестве цветов
        sql_get_flowers = '''
             SELECT name, COUNT(*) AS quantity, MAX(date) AS date_delivery
             FROM flowers
             GROUP BY name;
         '''
        cur.execute(sql_get_flowers)
        current_flowers = cur.fetchall()

        count = 0

        # Для каждого цветка проверяем наличие и обновляем/вставляем
        for flower in current_flowers:
            name, quantity, date_delivery = flower

            # Проверяем, существует ли уже запись с таким именем цветка
            sql_check = "SELECT 1 FROM flowers_quantity WHERE name = %s"
            cur.execute(sql_check, (name,))
            exists = cur.fetchone()

            if exists:
                # Обновляем существующую запись
                sql_update = '''
                     UPDATE flowers_quantity 
                     SET quantity = %s, date_delivery = %s
                     WHERE name = %s
                 '''
                cur.execute(sql_update, (quantity, date_delivery, name))
            else:
                # Вставляем новую запись
                sql_insert = '''
                     INSERT INTO flowers_quantity (name, quantity, date_delivery)
                     VALUES (%s, %s, %s)
                 '''
                cur.execute(sql_insert, (name, quantity, date_delivery))

            count = 1

        cur._connection.commit()

        return jsonify({
            "status": "OK",
            "count": count,
            "message": "Данные успешно обновлены!"
        })
    except Exception as e:
        cur.connection.rollback()
        return jsonify({"status": "ERROR", "message": str(e)})

@app.route('/flower_quantity_show', methods=['GET'])
def flower_quantity_show():
    try:
        sql_select = '''
             SELECT name, quantity, date_delivery
             FROM flowers_quantity;
         '''
        print(f"Executing SQL: {sql_select}")

        cur.execute(sql_select)
        flowers = cur.fetchall()

        flower_list = [{
            "name": row[0],
            "quantity": int(row[1]),
            "date_delivery": row[2].strftime('%Y-%m-%d') if row[2] else None
        } for row in flowers]

        print(f"Found {len(flower_list)} flower types")

        return jsonify({
            "status": "OK",
            "count": len(flower_list),
            "flowers": flower_list
        })

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return jsonify({
            "status": "ERROR",
            "message": f"Ошибка при получении данных: {str(e)}"
        }), 500

@app.route("/2weit/roses", methods=['POST', 'GET'])
def roses_page():
        return render_template("roses.html")

@app.route("/2weit/tulips", methods=['POST', 'GET'])
def tulips_page():
        return render_template("tulips.html")

@app.route("/2weit/lilies", methods=['POST', 'GET'])
def lilies_page():
        return render_template("lilies.html")

@app.route("/2weit/gerberas", methods=['POST', 'GET'])
def gerberas_page():
        return render_template("gerberas.html")

@app.route("/2weit/peonies", methods=['POST', 'GET'])
def peonies_page():
        return render_template("peonies.html")

@app.route("/2weit/lavender", methods=['POST', 'GET'])
def lavender_page():
        return render_template("lavender.html")

@app.route("/2weit/gypsophila", methods=['POST', 'GET'])
def gypsophila_page():
        return render_template("gypsophila.html")

if __name__ == '__main__':
    app.run(debug=True, port=5005)