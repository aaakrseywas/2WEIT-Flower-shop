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
def flower_update_price():
    data = request.json
    flower_id = data.get("id")
    new_price = data.get("price")

    if flower_id is None or new_price is None:
        return jsonify({"status": "ERROR", "message": "ID и цена обязательны."}), 400

    try:
        sql = f'UPDATE flowers SET price = "{new_price}" WHERE id = {flower_id}'

        print(f"flower_id: {flower_id}, new_price: {new_price}")
        cur.execute(sql, (new_price, flower_id))
        cur.connection.commit()

        return jsonify({"status": "OK", "message": "Цена успешно обновлена!"})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)})


if __name__ == '__main__':
    app.run(debug=True)


if __name__ == '__main__':
    app.run(debug=True)
