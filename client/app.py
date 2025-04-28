from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# API endpoint for registration
REGISTRATION_API_URL = "http://127.0.0.1:5000/registration"


@app.route("/2weit/registration")
def registration_page():
    return render_template("registration.html")


@app.route("/2weit/register", methods=["POST"])
def register_user():
    try:
        # Get form data
        user_data = {
            "name": request.form.get("name"),
            "username": request.form.get("username"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone"),
            "password": request.form.get("password")
        }

        # Validate all fields are present
        if not all(user_data.values()):
            return jsonify({"success": False, "message": "All fields are required"}), 400

        # Send data to registration API
        response = requests.post(REGISTRATION_API_URL, json=user_data)

        if response.status_code == 201:
            return jsonify({"success": True, "message": "Registration successful"})
        else:
            return jsonify({"success": False, "message": "Registration failed"}), 400

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/2weit")
def main_page():
    return render_template("main.html")

if __name__ == '__main__':
    app.run(debug=True, port=5005)