from flask import Flask, request, jsonify
from db import cur
app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"status": "OK"})

@app.route('/registration',methods=["POST"])
def registration():
    data=request.json
    if not data:
        return jsonify({"error": "Данные не предоставлены"}), 400

    required_fields = ["name", "username", "email", "phone"]
    for field in required_fields:
        missing_fields = [field for field in required_fields if field not in data or not data[field]]

        if missing_fields:
            return jsonify({
                "error": "Не заполнены обязательные поля",
                "missing_fields": missing_fields
            }), 400

    name=data.get("name")
    username=data.get("username")
    email=data.get("email")
    phone=data.get("phone")
    sql=f'INSERT INTO Users (name,username,email,phone) VALUES ("{name}", "{username}", "{email}", "{phone}")'
    print(sql)
    cur.execute(sql)
    cur._connection.commit()
    return jsonify({
        "status": "success",
        "message": "User registered successfully"
    }), 201

if __name__ == '__main__':
    app.run(debug=True)