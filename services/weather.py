from flask import Blueprint, request, jsonify
import requests
from datetime import datetime

weather_blueprint = Blueprint('weather', __name__)

# OpenWeatherMap API 配置信息
API_KEY = '8e135125a72740c9b107923cb85d2f9d'  # 替换为你的 API Key
BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'

@weather_blueprint.route('/', methods=['GET'])
def get_weather():
    city = request.args.get('city')
    date_str = request.args.get('date')  # 假设日期是通过 'date' 参数传递的，例如 'C'

    if not city:
        return jsonify({"error": "Please provide a city name"}), 400

    # 验证和解析日期
    if date_str:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            # 在这里，你可以进一步使用日期进行天气数据的预测，具体取决于 API 的功能
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # 使用 OpenWeatherMap API 获取天气信息
    params = {
        'q': city,
        'appid': API_KEY,
        'units': 'metric'
    }
    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        weather_description = data['weather'][0]['description']
        temperature = data['main']['temp']
        result = {
            "city": city,
            "temperature": temperature,
            "weather": weather_description,
            "date": date_str if date_str else "current"
        }
        return jsonify(result)
    else:
        return jsonify({'error': 'Failed to retrieve weather data'}), response.status_code
