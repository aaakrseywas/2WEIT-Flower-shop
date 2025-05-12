import datetime
import sqlite3
from contextlib import closing

import mysql
from flask import Flask, render_template, request, jsonify, url_for, redirect, session
import requests
from mysql.connector import Error

from db import cur, cnx

app = Flask(__name__)
app.secret_key = '2weit-flower'

REGISTRATION_API_URL = "http://127.0.0.1:5000/registration"

def get_db_connection():
    conn = sqlite3.connect('reviews.db')
    conn.row_factory = sqlite3.Row
    return conn

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

@app.route("/2weit/login", methods=["GET"])
def login_page():
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

        response = requests.post(
            "http://127.0.0.1:5000/login",
            json={"email": email, "password": password}
        )

        if response.status_code == 200:
            return jsonify({
                "success": True,
                "message": "Авторизация прошла успешно!",
                "redirect": "/2weit",
                "token": response.json().get("token")
            })
        else:
            error_message = response.json().get("message", "Неверный email или пароль")
            return jsonify({"success": False, "message": error_message}), response.status_code

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

        if not username or not comment:
            missing_fields = []
            if not username: missing_fields.append("username")
            if not comment: missing_fields.append("comment")

            return jsonify({
                "success": False,
                "message": "Все поля обязательны для заполнения",
                "missing_fields": missing_fields
            }), 400

        sql = "INSERT INTO Reviews (username, comment) VALUES (%s, %s)"
        cur.execute(sql, (username, comment))
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
    response = requests.get('http://127.0.0.1:5000/menu')
    param = response.json()
    flowers = param['flowers']
    html = ""
    for flower in flowers:
        html_temp = f"""
            <div class="flower">
                <h3>{flower[1]}</h3>  
                <p>Сорт: {flower[2]}</p>  
                <p>Цвет: {flower[3]}</p>  
               <p> Цена: {flower[5]} за штуку.</p>  
                <button class="add-to-cart" data-name={flower[1]}
                data-sort={flower[2]}
                data-color={flower[3]}
                data-price={flower[5]}>
                Добавить в корзину</button>
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

    session['cart'].append({
        'name': flower_name,
        'sort': flower_sort,
        'color': flower_color,
        'price': flower_price
    })

    session.modified = True
    return redirect(url_for('order_page'))

@app.route("/2weit/order", methods=['GET', 'POST'])
def order_page():
    cart = session.get('cart', [])
    total_price = sum(item['price'] * item.get('quantity', 1) for item in cart)

    if request.method == 'POST':
        try:
            name = request.form['name']
            address = request.form['address']
            email = request.form['email']
            payment_method = request.form['payment_method']
            comment = request.form.get('comment', '')
            discount_percent = float(request.form.get('discount_percent', 0))
            final_amount = total_price

            # Проверяем соединение с MySQL
            if not cnx.is_connected():
                cnx.reconnect()

            # Создаем заказ
            cur.execute("""
                 INSERT INTO orders (
                     customer_name, comment, address, email, 
                     payment_method, total_price, final_amount
                 ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                 """, (name, comment, address, email, payment_method, total_price, final_amount))

            order_id = cur.lastrowid

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

            cnx.commit()
            session.pop('cart', None)
            return redirect(url_for('order_success', order_id=order_id))

        except Exception as e:
            print(f"Ошибка при сохранении заказа: {e}")
            return render_template('order.html',
                                   cart=cart,
                                   total_price=total_price,
                                   error="Ошибка при оформлении заказа. Пожалуйста, попробуйте еще раз.")

    return render_template('order.html', cart=cart, total_price=total_price)

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

if __name__ == '__main__':
    app.run(debug=True, port=5005)