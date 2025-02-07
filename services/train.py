import os
import requests
import math
from flask import Blueprint, jsonify, request
from datetime import datetime
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

train_blueprint = Blueprint('train', __name__)

# SNCF API 相关配置
SNCF_API_KEY = os.getenv("SNCF_API_KEY")
SNCF_BASE_URL = "https://api.sncf.com/v1/coverage/sncf"

# Open-Meteo API (用于获取城市经纬度)
OPEN_METEO_URL = "https://geocoding-api.open-meteo.com/v1/search"

# 获取城市的经纬度
def get_city_coordinates(city_name):
    url = f"{OPEN_METEO_URL}?name={city_name}&count=1"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if "results" in data and len(data["results"]) > 0:
                city_info = data["results"][0]
                return city_info["latitude"], city_info["longitude"]
    except Exception as e:
        print(f"Error fetching city coordinates: {e}")
    return None, None  # 查询失败返回空值

# Haversine 公式计算两地之间的直线距离
def haversine(lat1, lon1, lat2, lon2):
    if None in [lat1, lon1, lat2, lon2]:
        return "Unknown"
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # 地球半径（单位：公里）
    return round(c * r, 1)  # 取整到最近的 0.1 公里

# 获取 SNCF 站点 ID
def get_station_id(city_name):
    if not SNCF_API_KEY:
        return None  # 如果 API Key 为空，返回 None
    url = f"{SNCF_BASE_URL}/places?q={city_name}"
    response = requests.get(url, auth=(SNCF_API_KEY, ""))
    if response.status_code == 200:
        data = response.json()
        for place in data.get("places", []):
            if place.get("embedded_type") == "stop_area":
                return place["id"]
    return None

def calculate_train_price(distance):
    """
    计算合理的火车票价:
    - 125km → 30 EUR
    - 600km → 80 EUR
    - 价格不会过高或过低
    """
    if distance == "Unknown":
        return "Unknown"

    try:
        distance = float(distance)
    except ValueError:
        return "Unknown"

    # 计算票价
    price = 0.105 * distance + 16.875

    # 票价限制
    price = max(20, min(price, 150))  # 最低 20 欧，最高 150 欧
    return round(price,0)  # 保留 2 位小数

def fetch_train_data(origin_id, destination_id, date):
    """调用 SNCF API 获取列车数据"""
    api_url = f"{SNCF_BASE_URL}/journeys?from={origin_id}&to={destination_id}&datetime={date}&count=40"
    print(f"API URL: {api_url}")
    response = requests.get(api_url, auth=(SNCF_API_KEY, ""))
    return response

@train_blueprint.route('/', methods=['GET'])
def get_train_schedule():
    print("Train schedule endpoint hit")

    # 获取用户输入的参数
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date = request.args.get('date')

    if not origin or not destination:
        return jsonify({"error": "Origin and destination are required"}), 400

    # 获取城市的经纬度
    origin_lat, origin_lon = get_city_coordinates(origin)
    destination_lat, destination_lon = get_city_coordinates(destination)

    if origin_lat is None or destination_lat is None:
        return jsonify({"error": f"Could not find coordinates for '{origin}' or '{destination}'"}), 404

    # 计算两地之间的直线距离
    distance = haversine(origin_lat, origin_lon, destination_lat, destination_lon)

    # 获取 SNCF 站点 ID
    origin_id = get_station_id(origin)
    destination_id = get_station_id(destination)

    print(f"Origin ID: {origin_id}, Destination ID: {destination_id}")

    if not origin_id or not destination_id:
        return jsonify({"error": f"Invalid origin or destination: '{origin}' or '{destination}'"}), 404

    # 处理 `date` 为空的情况，默认查询当天 06:00 和 14:00 两个时间段
    if not date:
        today = datetime.now().strftime("%Y-%m-%d")
        morning_date = f"{today} 06:00"
        afternoon_date = f"{today} 14:00"

        # 查询早上 06:00 之后的班次
        morning_response = fetch_train_data(origin_id, destination_id, datetime.strptime(morning_date, "%Y-%m-%d %H:%M").strftime("%Y%m%dT%H%M%S"))
        afternoon_response = fetch_train_data(origin_id, destination_id, datetime.strptime(afternoon_date, "%Y-%m-%d %H:%M").strftime("%Y%m%dT%H%M%S"))

        responses = [morning_response, afternoon_response]
    else:
        formatted_date = datetime.strptime(date, "%Y-%m-%d %H:%M").strftime("%Y%m%dT%H%M%S")
        responses = [fetch_train_data(origin_id, destination_id, formatted_date)]

    journeys = []

    # 解析 API 返回的列车信息
    for response in responses:
        if response.status_code == 200:
            print("SNCF API request successful")
            data = response.json()
            for journey in data.get("journeys", []):
                # 获取出发时间、到达时间和时长
                departure_time = journey["departure_date_time"]
                arrival_time = journey["arrival_date_time"]
                duration = journey["duration"]

                # 转换时间格式
                departure_dt = datetime.strptime(departure_time, "%Y%m%dT%H%M%S")
                arrival_dt = datetime.strptime(arrival_time, "%Y%m%dT%H%M%S")
                duration_str = f"{duration // 3600}h{(duration % 3600) // 60}min"

                # 计算票价（基于距离）
                price_range = f"{calculate_train_price(distance)}"

                # 统一返回格式
                journeys.append({
                    "from": origin,  # 返回城市名
                    "to": destination,  # 返回城市名
                    "date": departure_dt.strftime("%d %b"),  # 格式化日期
                    "time": f"{departure_dt.strftime('%H:%M')}-{arrival_dt.strftime('%H:%M')}",
                    "duration": duration_str,
                    "type": "train",
                    "price": price_range,
                    "distance": str(distance)
                })

    if not journeys:
        return jsonify({"error": "No trains available"}), 404

    return jsonify(journeys)
