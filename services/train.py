import os
import requests
from flask import Blueprint, jsonify, request
from datetime import datetime
from dotenv import load_dotenv  # 从 python-dotenv 导入加载函数

# 加载 .env 文件中的环境变量
load_dotenv()

train_blueprint = Blueprint('train', __name__)

# 使用 SNCF API 获取站点 ID
def get_station_id(city_name):
    api_key = os.getenv("SNCF_API_KEY")  # 从环境变量中获取 API 密钥
    if not api_key:
        return None  # 如果环境变量未定义，返回 None    
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
    # 获取出发地、目的地和出发日期参数
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date = request.args.get('date')

    if not origin or not destination or not date:
        return jsonify({"error": "Origin, destination, and date are required"}), 400

    try:
        datetime.strptime(date, '%Y-%m-%d %H:%M')
    except ValueError:
        return jsonify({"error": "Invalid date format. Use 'YYYY-MM-DD HH:MM'"}), 400

    # 获取出发地和目的地的站点 ID
    origin_id = get_station_id(origin)
    destination_id = get_station_id(destination)

    if not origin_id or not destination_id:
        return jsonify({"error": f"Invalid origin or destination: '{origin}' or '{destination}'"}), 404

    # SNCF API 的 URL
    formatted_date = datetime.strptime(date, '%Y-%m-%d %H:%M').strftime('%Y%m%dT%H%M%S')
    api_url = f"https://api.sncf.com/v1/coverage/sncf/journeys?from={origin_id}&to={destination_id}&datetime={formatted_date}"

    # 发送 GET 请求到 SNCF API
    response = requests.get(api_url, auth=("ce77f0e6-6291-4b03-8125-ebe88852aeaa", ''))

    # 处理响应
    if response.status_code == 200:
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

            # 根据行程时间生成合理价格和座位类型
            hours = duration // 3600
            base_price = hours * 20  # 每小时约 20 欧元的基础价格
            if (duration % 3600) // 60 > 0:  # 如果有额外的分钟数，增加小幅费用
                base_price += 10

            if hours <= 3:
                price_second_class = base_price
                seat_class = "Second Class"
            else:
                price_second_class = base_price
                price_first_class = base_price + 30  # 一等座比二等座贵 30 欧元
                seat_class = "First Class or Second Class"

            # 添加到列表
            journeys.append({
                "origin": from_station,
                "destination": to_station,
                "departure": departure_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "arrival": arrival_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "duration": duration_str,
                "price_second_class": f"{price_second_class} EUR",
                "price_first_class": f"{price_first_class} EUR" if hours > 3 else "Not available",
                "seat_class": seat_class
            })

        return jsonify(journeys)

    else:
        return jsonify({'error': f'Failed to retrieve data. Status code: {response.status_code}'}), response.status_code
#http://127.0.0.1:5000/train/?origin=Paris&destination=Nice&date=2024-12-08%2007:00