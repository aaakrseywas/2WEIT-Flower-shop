import datetime
import sqlite3
import mysql
from flask import Flask, render_template, request, jsonify, url_for, redirect
import requests

app = Flask(__name__)


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

@app.route("/2weit/feedback", methods=['POST', 'GET'])
def feedback_user():
        response = requests.get(REVIEWS_API_URL)
        print(response)
        try:
            response = requests.get(REVIEWS_API_URL)
            print(response)
            if response.status_code == 200:
                reviews_data = response.json()
                return jsonify({
                    "success": True,
                    "message": "Отзывы успешно получены",
                    "reviews": reviews_data.get("Reviews", []),
                    "count": reviews_data.get("count", 0)
                })
            else:
                error_message = response.json().get("message", "Ошибка при получении отзывов")
                return jsonify({"success": False, "message": error_message}), response.status_code

        except Exception as e:
            return jsonify({"success": False, "message": f"Ошибка сервера: {str(e)}"}), 500



if __name__ == '__main__':
    app.run(debug=True, port=5005)