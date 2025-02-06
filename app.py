import os
import threading
import requests
import time

from flask import Flask, jsonify
from services.weather import weather_blueprint
from services.train import train_blueprint
from services.restaurant import restaurant_blueprint
from services.hotel import hotel_blueprint
from services.flight import flight_blueprint
from services.attraction import places_blueprint
app = Flask(__name__)

# 注册不同的蓝图
app.register_blueprint(weather_blueprint, url_prefix='/weather')
app.register_blueprint(train_blueprint, url_prefix='/train')
app.register_blueprint(restaurant_blueprint, url_prefix='/restaurants')
app.register_blueprint(hotel_blueprint, url_prefix='/hotel')
app.register_blueprint(flight_blueprint, url_prefix='/flight')
app.register_blueprint(places_blueprint, url_prefix='/attraction')


PING_URL = "https://api-for-travalapp.onrender.com" 

def auto_ping():
    while True:
        try:
            response = requests.get(PING_URL)
            print(f"Auto-ping réussi : {response.status_code}")
        except Exception as e:
            print(f"Erreur d'auto-ping : {e}")
        time.sleep(30)  # Ping toutes les 30 secondes

threading.Thread(target=auto_ping, daemon=True).start()
# 默认根目录内容   
@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Travel App API! Use specific endpoints such as /weather to get information."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # 使用 PORT 环境变量
    app.run(host='0.0.0.0', debug=True, port=port)
