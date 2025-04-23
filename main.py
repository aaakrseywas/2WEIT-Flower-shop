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
        with connection.cursor() as cur:
            sql = 'SELECT * FROM flowers'
            cur.execute(sql)
            result = cur.fetchall()

            flowers = []
            for row in result:
                flowers.append({
                    'id': row[0],
                    'name': row[1],
                    'sort': row[2],
                    'color': row[3],
                    'date': row[4].strftime('%Y-%m-%d'),
                    'price': row[5]
                })
            return jsonify({"status": "OK", "flowers": flowers})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)})


if __name__ == '__main__':
    app.run(debug=True)
