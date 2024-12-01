import requests
from flask import Flask, Blueprint, jsonify, request
from datetime import datetime
import random
train_blueprint = Blueprint('train', __name__)

# 使用 SNCF API 获取站点 ID
def get_station_id(city_name):
    api_key = "ce77f0e6-6291-4b03-8125-ebe88852aeaa"
    url = f"https://api.sncf.com/v1/coverage/sncf/places?q={city_name}"
    
    response = requests.get(url, auth=(api_key, ''))
    if response.status_code == 200:
        data = response.json()
        for place in data.get('places', []):
            if place.get('embedded_type') == 'stop_area':
                return place['id']
    return None

@train_blueprint.route('/', methods=['GET'])
def get_train_schedule():
    print("Train schedule endpoint hit")  # 添加这一行用于调试

    # 获取出发地、目的地和出发日期参数
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date = request.args.get('date')

    if not origin or not destination or not date:
        print("Missing required parameters: origin, destination, or date")  # 调试信息
        return jsonify({"error": "Origin, destination, and date are required"}), 400

    try:
        datetime.strptime(date, '%Y-%m-%d %H:%M')
    except ValueError:
        print("Invalid date format")  # 调试信息
        return jsonify({"error": "Invalid date format. Use 'YYYY-MM-DD HH:MM'"}), 400

    # 获取出发地和目的地的站点 ID
    origin_id = get_station_id(origin)
    destination_id = get_station_id(destination)
    print(f"Origin ID: {origin_id}, Destination ID: {destination_id}")

    if not origin_id or not destination_id:
        print(f"Invalid origin or destination: '{origin}' or '{destination}'")  # 调试信息
        return jsonify({"error": f"Invalid origin or destination: '{origin}' or '{destination}'"}), 404

    # SNCF API 的 URL
    formatted_date = datetime.strptime(date, '%Y-%m-%d %H:%M').strftime('%Y%m%dT%H%M%S')
    api_url = f"https://api.sncf.com/v1/coverage/sncf/journeys?from={origin_id}&to={destination_id}&datetime={formatted_date}"

    print(f"API URL: {api_url}")  # 调试信息

    # 发送 GET 请求到 SNCF API
    response = requests.get(api_url, auth=("ce77f0e6-6291-4b03-8125-ebe88852aeaa", ''))

    # 处理响应
    if response.status_code == 200:
        print("SNCF API request successful")  # 调试信息
        data = response.json()

        # 获取列车行程数据
        journeys = []
        for journey in data.get('journeys', []):
            # 获取出发地、目的地、出发和到达时间
            departure = journey['departure_date_time']
            arrival = journey['arrival_date_time']
            duration = journey['duration']

            # 获取出发站点和到达站点的名称
            from_station = journey.get('from', {}).get('name', origin)
            to_station = journey.get('to', {}).get('name', destination)

            # 转换时间格式
            departure_dt = datetime.strptime(departure, "%Y%m%dT%H%M%S")
            arrival_dt = datetime.strptime(arrival, "%Y%m%dT%H%M%S")
            duration_str = f"{duration // 3600}h {(duration % 3600) // 60}m"

            # 根据行程时间生成随机价格和座位类型
            hours = duration // 3600
            if hours <= 2:
                price = random.randint(20, 40)
                seat_class = "Second Class"
            elif hours <= 4:
                price = random.randint(40, 70)
                seat_class = "Second Class"
            else:
                price = random.randint(70, 120)
                seat_class = "First Class"

            # 添加到列表
            journeys.append({
                "origin": from_station,
                "destination": to_station,
                "departure": departure_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "arrival": arrival_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "duration": duration_str,
                "price": f"{price} EUR",
                "seat_class": seat_class
            })

        return jsonify(journeys)

    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")  # 调试信息
        return jsonify({'error': f'Failed to retrieve data. Status code: {response.status_code}'}), response.status_code
#http://127.0.0.1:5000/train/?origin=Paris&destination=Nice&date=2024-12-08%2007:00