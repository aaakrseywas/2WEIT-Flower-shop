import requests
from flask import Flask, request, jsonify
from db import cur, cnx
import jwt
import bcrypt

from datetime import datetime, timedelta, timezone

app = Flask(__name__)
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response

@app.route('/')
def index():
    return jsonify({"status": "OK"})

@app.route('/registration', methods=["POST"])
def registration():
    data = request.json
    if not data:
        return jsonify({"error": "Данные не предоставлены"}), 400

    required_fields = ["name", "username", "email", "phone", "password"]
    missing_fields = [field for field in required_fields if field not in data or not data[field]]

    if missing_fields:
        return jsonify({
            "error": "Не заполнены обязательные поля",
            "missing_fields": missing_fields
        }), 400

    name = data.get("name")
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    phone = data.get("phone")

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    sql = f'INSERT INTO Users (name, username, email, phone, password) VALUES ("{name}", "{username}", "{email}", "{phone}", "{hashed_password}")'
    print(sql)
    cur.execute(sql)
    cur._connection.commit()

    return jsonify({
        "status": "success",
        "message": "User registered successfully"
    }), 201

def generate_token(username, secret_key='2weiT', expires_in=3600):
    payload = {
        'user_name': username,
        'exp': datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    }
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token

@app.route('/login', methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Данные не предоставлены"}), 400

    required_fields = ["email", "password"]
    missing_fields = [field for field in required_fields if field not in data or not data[field]]

    if missing_fields:
        return jsonify({
            "error": "Не заполнены обязательные поля",
            "missing_fields": missing_fields
        }), 400

    email = data.get("email")
    password = data.get("password")

    sql = f'SELECT * FROM Users WHERE email = "{email}"'
    print(sql)
    cur.execute(sql)
    user = cur.fetchone()
    print(user)

    if user:
            if bcrypt.checkpw(password.encode('utf-8'), user[4].encode('utf-8')):
                token = generate_token(user[2])
                users_id = user[0]

            insert_sql = f'INSERT INTO User_token (users_id, token) VALUES ("{users_id}", "{token}")'
            print(insert_sql)
            try:
                cur.execute(insert_sql)
                cur._connection.commit()
                print("Токен успешно сохранен.")
            except Exception as e:
                print(f"Ошибка при вставке токена: {e}")
                return jsonify({
                    "status": "error",
                    "message": "Не удалось сохранить токен"
                }), 500

            return jsonify({
                "status": "success",
                "message": "Login successful",
                "token": token
            }), 200
    else:
        return jsonify({
            "status": "error",
            "message": "Invalid credentials"
        }), 401


@app.route('/flower_add', methods=['POST'])
def flower():
    data = request.get_json()

    name = data.get("name")
    sort = data.get("sort")
    color = data.get("color")
    date = data.get("date")
    price = data.get("price")

    sql = f'INSERT INTO flowers (name, sort, color, date, price) VALUES ("{name}", "{sort}", "{color}", "{date}", "{price}")'
    print(sql)

    cur.execute(sql)
    cur._connection.commit()

    return jsonify({"status": "OK", "message": "Flower added successfully!"})


@app.route('/api/menu', methods=['GET'])
def menu():
    try:
        sql = '''
        SELECT f.id, f.name, f.sort, f.color, f.price, fq.quantity 
        FROM flowers f 
        JOIN flowers_quantity fq ON f.name = fq.name
        '''
        cur.execute(sql)

        flowers = []
        for row in cur:
            flower = {
                'id': row[0],
                'name': row[1],
                'sort': row[2],
                'color': row[3],
                'price': row[4],
                'quantity': row[5]
            }
            flowers.append(flower)

        return jsonify({
            "status": "OK",
            "count": len(flowers),
            "flowers": flowers
        })
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500


def get_db_connection():
    return cnx


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
    data = request.json
    flower_name = data.get("name")
    new_price = data.get("price")

    if flower_name is None or new_price is None:
        return jsonify({"status": "ERROR", "message": "Название и цена обязательны."}), 400

    try:
        sql = 'UPDATE flowers SET price = %s WHERE name = %s'
        cur.execute(sql, (new_price, flower_name))
        cur._connection.commit()

        return jsonify({
            "status": "OK",
            "message": f"Цена всех цветов '{flower_name}' обновлена на {new_price}"
        })
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)})


@app.route('/flower_quantity', methods=['POST'])
def flower_quantity():
    try:
        sql_get_flowers = '''
            SELECT name, COUNT(*) AS quantity, MAX(date) AS date_delivery
            FROM flowers
            GROUP BY name;
        '''
        cur.execute(sql_get_flowers)
        current_flowers = cur.fetchall()

        count = 0

        for name, quantity, date_delivery in current_flowers:
            sql_check = "SELECT 1 FROM flowers_quantity WHERE name = %s"
            cur.execute(sql_check, (name,))
            exists = cur.fetchone()

            if exists:
                #
                sql_update = '''
                    UPDATE flowers_quantity 
                    SET quantity = %s, date_delivery = %s
                    WHERE name = %s
                '''
                cur.execute(sql_update, (quantity, date_delivery, name))
            else:
                sql_insert = '''
                    INSERT INTO flowers_quantity (name, quantity, date_delivery)
                    VALUES (%s, %s, %s)
                '''
                cur.execute(sql_insert, (name, quantity, date_delivery))

            count += 1

        cur.connection.commit()

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
        sql_select = f'''
            SELECT flowers.name, SUM(flowers_quantity.quantity) AS quantity
            FROM flowers 
            JOIN flowers_quantity ON flowers.name = flowers_quantity.name
            GROUP BY flowers.name;
         '''
        cur.execute(sql_select)
        flowers = cur.fetchall()

        flower_list = [{"name": row[0], "quantity": row[1]} for row in flowers]

        return jsonify({
            "status": "OK",
            "flowers": flower_list
        })
    except Exception as e:
        cur._connection.rollback()
        return jsonify({"status": "ERROR", "message": str(e)})

@app.route('/reviews_add', methods=['POST'])
def reviews_add():
    data = request.get_json()
    print(data)
    if not data:
        return jsonify({"error": "Данные не предоставлены"}), 400

    required_fields = ["username", "comment", "email"]
    missing_fields = [field for field in required_fields if field not in data or not data[field]]

    if missing_fields:
        return jsonify({
            "error": "Не заполнены обязательные поля",
            "missing_fields": missing_fields
        }), 400

    username = data.get('username')
    comment = data.get('comment')
    email = data.get('email')

    sql = f'INSERT INTO Reviews (username, comment, email) VALUES ("{username}","{comment}", "{email}")'
    print(sql)
    cur.execute(sql)
    cur._connection.commit()

    return jsonify({
        "status": "success",
        "message": "review saved successfully"
    }), 201

@app.route('/reviews', methods=['POST', 'GET'])
def reviews():
    try:
        sql = 'SELECT * FROM Reviews'
        cur.execute(sql)
        reviews = []
        for row in cur:
            reviews.append({
                "id": row[0],
                "username": row[1],
                "comment": row[2],
                "date": row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] else None
            })

        return jsonify({
            "status": "OK",
            "count": len(reviews),
            "Reviews": reviews
        })
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500


@app.route('/apply_discount', methods=['POST'])
def apply_discount():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Данные не предоставлены"}), 400

    required_fields = ["user_id", "order_id", "original_amount"]
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return jsonify({
            "error": "Не заполнены обязательные поля",
            "missing_fields": missing_fields
        }), 400

    user_id = data["user_id"]
    order_id = data["order_id"]
    original_amount = float(data["original_amount"])

    try:
            sql = "SELECT discount_percent FROM discounts WHERE user_id = %s"
            cur.execute(sql, (user_id,))
            result = cur.fetchone()

            if not result:
                return jsonify({
                    "status": "no_discount",
                    "message": "Пользователь не найден или скидка не назначена",
                    "original_amount": original_amount
                })

            discount_percent = float(result[0])

            if discount_percent < 0 or discount_percent > 100:
                return jsonify({
                    "error": "Некорректный размер скидки",
                    "discount_percent": discount_percent
                }), 400

            discount_amount = (original_amount * discount_percent) / 100
            final_amount = original_amount - discount_amount

            sql_insert = """
                 INSERT INTO orders 
                 (order_id, user_id, original_amount, discount_percent, final_amount) 
                 VALUES (%s, %s, %s, %s, %s)
             """
            cur.execute(sql_insert, (order_id, user_id, original_amount,
                                     discount_percent, final_amount))
            cur._connection.commit()

            return jsonify({
                "status": "success",
                "message": "Скидка применена",
                "discount_percent": discount_percent,
                "discount_amount": discount_amount,
                "final_amount": final_amount
            })

    except Exception as e:
        cur._connection.rollback()
        return jsonify({
            "error": "Ошибка при обработке запроса",
            "details": str(e)
        }), 500


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

    name = data["name"]
    discount_percent = float(data["discount_percent"])

    try:
        sql_user = f"SELECT User_ID FROM Users WHERE name = '{name}'"
        cur.execute(sql_user)
        user_result = cur.fetchone()

        if not user_result:
            return jsonify({"error": "Пользователь не найден"}), 404

        user_id = user_result[0]

        sql_discount = f"""
            INSERT INTO discounts (user_id, discount_percent) 
            VALUES ('{user_id}', '{discount_percent}') 
            ON DUPLICATE KEY UPDATE discount_percent = '{discount_percent}'
        """
        cur.execute(sql_discount)
        cur._connection.commit()

        return jsonify({
            "status": "success",
            "message": "Скидка добавлена или обновлена",
            "user_id": user_id,
            "discount_percent": discount_percent
        })

    except Exception as e:
        return jsonify({
            "error": "Ошибка при выполнении запроса",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')





