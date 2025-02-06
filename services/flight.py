import requests
import math
from datetime import datetime, timedelta
from flask import Flask, Blueprint, request, jsonify

app = Flask(__name__)
flight_blueprint = Blueprint('flight', __name__)

# 开源机场数据库（OpenFlights 托管的 airports.dat 数据）
OPENFLIGHTS_AIRPORTS_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"

# Haversine 公式计算两地之间的直线距离
def haversine(lat1, lon1, lat2, lon2):
    """
    计算两点之间的直线距离（单位：公里）
    """
    if None in [lat1, lon1, lat2, lon2]:  # 如果有一个空值，则无法计算
        return None

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # 地球半径（单位：公里）
    return round(c * r, 1)  # 取整到最近的 0.1 公里

# 获取机场名称和经纬度
def get_airport_info(city):
    """
    通过城市名称查询机场名称和经纬度（使用 OpenFlights 的数据）
    """
    try:
        response = requests.get(OPENFLIGHTS_AIRPORTS_URL)
        if response.status_code == 200:
            airports = response.text.split("\n")
            for airport in airports:
                fields = airport.split(",")
                if len(fields) > 6:
                    airport_name = fields[1].replace('"', '')  # 机场名称
                    city_name = fields[2].replace('"', '')  # 城市名称
                    lat, lon = fields[6], fields[7]  # 经纬度
                    if city.lower() == city_name.lower():
                        return airport_name, float(lat), float(lon)
        return "No Airport Found", None, None
    except Exception:
        return "No Airport Found", None, None

# 生成固定值的航班时间 & 价格
def generate_flight_time_and_price(distance):
    """
    通过距离生成固定的出发时间、飞行时间和票价
    """
    if distance is None:
        return None, None, None, "Unknown"

    # 固定出发时间（通过哈希计算小时数）
    start_hour = (hash(int(distance)) % 12) + 6  # 确保出发时间在 06:00 - 18:00
    departure_time = datetime.now().replace(hour=start_hour, minute=0, second=0)

    # 计算飞行时间（假设飞机时速 800km/h）
    duration_minutes = max(60, int(distance / 800 * 60))  # 至少 1 小时
    arrival_time = departure_time + timedelta(minutes=duration_minutes)
    duration_str = f"{duration_minutes // 60}h{duration_minutes % 60}min"

    # 计算票价（基础票价 50 欧元，每公里 0.2 欧元）
    base_price = 50
    rate_per_km = 0.2
    price = base_price + distance * rate_per_km

    return departure_time, arrival_time, duration_str, round(price, 2)

# 生成假航班数据
def generate_fake_flight(departure_city, arrival_city, date):
    departure_airport, departure_lat, departure_lon = get_airport_info(departure_city)
    arrival_airport, arrival_lat, arrival_lon = get_airport_info(arrival_city)

    # 如果任何一个城市没有机场，返回标识
    if departure_airport == "No Airport Found" or arrival_airport == "No Airport Found":
        return {
            "error": "One or both cities do not have an airport",
            "departure_city": departure_city,
            "arrival_city": arrival_city,
            "departure_airport": departure_airport,
            "arrival_airport": arrival_airport
        }

    # 计算真实的飞行距离
    distance = haversine(departure_lat, departure_lon, arrival_lat, arrival_lon)

    # 解析用户输入的日期（格式：YYYY-MM-DD）
    try:
        flight_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}

    # 生成固定出发时间、到达时间、飞行时长和价格
    departure_time, arrival_time, duration_str, price = generate_flight_time_and_price(distance)

    return {
        "from": departure_airport,
        "to": arrival_airport,
        "date": flight_date.strftime("%d %b"),  # 格式化日期，例如 "08 Dec"
        "time": f"{departure_time.strftime('%H:%M')}-{arrival_time.strftime('%H:%M')}",
        "duration": duration_str,
        "type": "plane",
        "price": f"{price}",
        "distance": str(distance) if distance else "Unknown"  # 计算出的真实距离
    }

@flight_blueprint.route('/search', methods=['GET'])
def search_flights():
    """
    获取模拟航班数据
    """
    departure_city = request.args.get('departure_city')  # 出发城市
    arrival_city = request.args.get('arrival_city')  # 到达城市
    date = request.args.get('date')  # 用户输入的日期（YYYY-MM-DD）

    if not departure_city or not arrival_city or not date:
        return jsonify({"error": "Please provide departure_city, arrival_city, and date"}), 400

    fake_flights = [generate_fake_flight(departure_city, arrival_city, date)]

    return jsonify(fake_flights)

app.register_blueprint(flight_blueprint, url_prefix='/flights')

if __name__ == "__main__":
    app.run(debug=True)
