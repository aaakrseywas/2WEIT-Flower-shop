from flask import Flask, request, jsonify
from db import cur
import jwt
import bcrypt

from datetime import datetime, timedelta, timezone

app = Flask(__name__)

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

            insert_sql = f'INSERT INTO User_token (users_id, token) VALUES ({users_id}, "{token}")'
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

    return jsonify({"status": "OK", "message": "Flower added successfully!"})

@app.route('/flower_all', methods=['GET'])
def flower_all():
    try:
        sql='SELECT * FROM flowers'
        cur.execute(sql)
        flowers=[]
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


@app.route('/flower_new_price', methods=['POST'])
def flower_new_price():
    data = request.json
    flower_id = data.get("id")
    new_price = data.get("price")

    if flower_id is None or new_price is None:
        return jsonify({"status": "ERROR", "message": "ID и цена обязательны."}), 400

    try:
        sql = f'UPDATE `flowers` SET `price` = "{new_price}" WHERE `id` = {flower_id}'
        print(sql)

        print(f"flower_id: {flower_id}, new_price: {new_price}")
        cur.execute(sql)
        cur._connection.commit()

        return jsonify({"status": "OK", "message": "Цена успешно обновлена!"})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)})

@app.route('/flower_quantity', methods=['POST'])
def flower_quantity():
    try:
        sql_insert = f'''
            INSERT INTO flowers_quantity (flower_ID, quantity, date_delivery)
            SELECT id, COUNT(*) AS quantity, MAX(date) AS date_delivery
            FROM flowers
            GROUP BY id;
        '''
        cur.execute(sql_insert)
        cur._connection.commit()

        count = cur.rowcount

        return jsonify({
            "status": "OK",
            "count": count,
            "message": "Data inserted successfully!"
        })
    except Exception as e:
        cur.connection.rollback()
        return jsonify({"status": "ERROR", "message": str(e)})

@app.route('/flower_quantity_show', methods=['POST'])
def flower_quantity_show():
    try:
        sql_select = f'''
            SELECT name, COUNT(*) AS quantity
            FROM flowers 
            JOIN flowers_quantity ON id = flower_ID
            GROUP BY name;
        '''
        cur.execute(sql_select)
        flowers = cur.fetchall()

        flower_list = [{"name": row[0], "quantity": row[1]} for row in flowers]

        return jsonify({
            "status": "OK",
            "flowers": flower_list
        })
    except Exception as e:
        cur.connection.rollback()
        return jsonify({"status": "ERROR", "message": str(e)})


@app.route('/reviews', methods=['POST'])
def reviews():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Данные не предоставлены"}), 400

    required_fields = ["username", "comment"]
    missing_fields = [field for field in required_fields if field not in data or not data[field]]

    if missing_fields:
        return jsonify({
            "error": "Не заполнены обязательные поля",
            "missing_fields": missing_fields
        }), 400

    username = data.get('username')
    comment = data.get('comment')

    sql = f'INSERT INTO Reviews (username, comment) VALUES ("{username}", "{comment}")'
    print(sql)
    cur.execute(sql)
    cur._connection.commit()



    return jsonify({
        "status": "success",
        "message": "review saved successfully"
    }), 201


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
    app.run(debug=True)





