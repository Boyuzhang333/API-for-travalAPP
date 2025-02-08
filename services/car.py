import requests
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta

# 创建 car 蓝图
car_blueprint = Blueprint('car', __name__)

# OpenRouteService API Key
ORS_API_KEY = "5b3ce3597851110001cf6248c4c60872b9ea4f27af6e5e8c79aebbf1"

def fetch_city_coordinates(city):
    """通过 OpenRouteService API 获取城市的经纬度"""
    try:
        geocode_url = f"https://api.openrouteservice.org/geocode/search?api_key={ORS_API_KEY}&text={city}, France"
        response = requests.get(geocode_url)
        response.raise_for_status()  # 确保返回状态为 200
        data = response.json()
        return data['features'][0]['geometry']['coordinates'] if 'features' in data and data['features'] else None
    except Exception as e:
        print(f"Error fetching coordinates for {city}: {str(e)}")
        return None

def get_car_route(origin, destination, date):
    """
    使用 OpenRouteService API 获取两个城市之间的驾车距离和时间，并返回带时间和日期的结果。
    """
    try:
        headers = {
            'Authorization': ORS_API_KEY,
            'Content-Type': 'application/json'
        }

        # 获取城市坐标
        origin_coords = fetch_city_coordinates(origin)
        dest_coords = fetch_city_coordinates(destination)

        if not origin_coords or not dest_coords:
            return {"error": f"Could not fetch coordinates for '{origin}' or '{destination}'"}

        # 构建路线请求
        directions_url = "https://api.openrouteservice.org/v2/directions/driving-car"
        body = {"coordinates": [origin_coords, dest_coords], "format": "json"}
        response = requests.post(directions_url, json=body, headers=headers)
        response.raise_for_status()  # 确保返回状态为 200

        route_data = response.json()

        # 提取距离和时间
        distance_km = route_data['routes'][0]['summary']['distance'] / 1000  # 转换为公里
        duration_seconds = route_data['routes'][0]['summary']['duration']  # 总秒数

        # 计算出发和到达时间
        departure_time = datetime.strptime(date, "%Y-%m-%d") + timedelta(hours=9)  # 假设早上 9 点出发
        arrival_time = departure_time + timedelta(seconds=duration_seconds)

        # 转换时间格式
        duration_str = f"{int(duration_seconds // 3600)}h {int((duration_seconds % 3600) // 60)}m"

        # 计算成本
        cost = distance_km * 0.2

        return {
            "from": origin,
            "to": destination,
            "date": date,
            "time": f"{departure_time.strftime('%H:%M')}-{arrival_time.strftime('%H:%M')}",
            "duration": duration_str,
            "type": "car",
            "price": f"{cost:.0f}",
            "distance": f"{distance_km:.1f}km",
        }
    except requests.exceptions.RequestException as e:
        print(f"API Request error: {str(e)}")
        return {"error": "Failed to fetch route data"}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {"error": "An unexpected error occurred"}

@car_blueprint.route('/get_route', methods=['GET'])
def get_route():
    """
    API 端点：获取汽车路线信息
    参数：
    - origin: 出发城市
    - destination: 到达城市
    - date: 出发日期（格式：YYYY-MM-DD）
    """
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date = request.args.get('date')

    # 验证必需参数
    if not origin or not destination:
        return jsonify({"error": "Origin and destination are required"}), 400

    # 验证日期格式
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # 获取汽车路线
    car_route = get_car_route(origin, destination, date)
    return jsonify(car_route) if car_route else jsonify({"error": "Could not retrieve car route"}), 500
