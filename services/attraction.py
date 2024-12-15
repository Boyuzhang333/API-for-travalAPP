from flask import Blueprint, request, jsonify
import requests
import hashlib
import os
import hashlib
from dotenv import load_dotenv  # 从 python-dotenv 导入加载函数


# 创建 Flask 蓝图
places_blueprint = Blueprint('places', __name__)

# 配置信息
FOURSQUARE_API_KEY = os.getenv('FOURSQUARE_API_KEY')  # 从环境变量读取 API Key
if not FOURSQUARE_API_KEY:
    raise EnvironmentError("FOURSQUARE_API_KEY is not set. Please set it in the environment variables.")

SEARCH_URL = 'https://api.foursquare.com/v3/places/search'
DETAIL_URL = 'https://api.foursquare.com/v3/places'
PHOTO_URL = 'https://api.foursquare.com/v3/places/{fsq_id}/photos'
NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'

# 城市名转经纬度函数
def convert_city_to_lat_lng(city_name):
    params = {
        'q': city_name,
        'format': 'json',
        'addressdetails': 1,
        'limit': 1
    }
    headers = {'User-Agent': 'MyTravelApp/1.0 (myemail@example.com)'}
    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data:
            return f"{data[0]['lat']},{data[0]['lon']}"
        return None
    except requests.exceptions.RequestException as e:
        print("Nominatim API Error:", e)
        return None

# 生成评分和价格
def generate_rating_and_price(fsq_id):
    hash_value = int(hashlib.md5(fsq_id.encode()).hexdigest(), 16)
    rating = 3.0 + (hash_value % 2000) / 1000.0  # 结果范围是 [3.0, 5.0]
    price = 10 + (hash_value % 41)  # 结果范围是 [10, 50]
    return round(rating, 1), price

# 获取照片信息
def fetch_photos(fsq_id):
    headers = {'Authorization': FOURSQUARE_API_KEY}
    try:
        response = requests.get(PHOTO_URL.format(fsq_id=fsq_id), headers=headers)
        response.raise_for_status()
        photos = response.json()
        return [
            f"{photo['prefix']}original{photo['suffix']}" for photo in photos
        ] if photos else ["No photo available"]
    except requests.exceptions.RequestException as e:
        print("Photo API Error:", e)
        return ["No photo available"]

@places_blueprint.route('/', methods=['GET'])
def get_attractions():
    city_name = request.args.get('city')
    radius = request.args.get('radius', 1000)
    limit = request.args.get('limit', 10)
    query = request.args.get('query')  # 景点名称关键字
    categories = request.args.get('categories')

    if not city_name:
        return jsonify({"error": "Please provide a city name"}), 400

    location = convert_city_to_lat_lng(city_name)
    if not location:
        return jsonify({"error": f"Failed to retrieve location for city: {city_name}"}), 500

    headers = {'Authorization': FOURSQUARE_API_KEY}
    params = {
        'll': location,
        'radius': radius,
        'limit': limit,
        'categories': '16023,16032,16001,16021,16019',  # 景点相关分类 ID
    }

    # 如果用户提供了景点名称，则添加到请求参数
    if query:
        params['query'] = query
        
    if categories:
        params['categories'] = categories

    try:
        response = requests.get(SEARCH_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        attractions = []
        for place in data.get("results", []):
            fsq_id = place.get("fsq_id")
            rating, price = generate_rating_and_price(fsq_id)

            photos = fetch_photos(fsq_id)

            attraction_details = {
                "name": place.get("name", "No name available"),
                "location": place.get("location", {}).get("formatted_address", "No address available"),
                "distance": place.get("distance", "Unknown"),
                "rating": rating,
                "price": f"€{price}",
                "categories": [cat["name"] for cat in place.get("categories", [])],
                "photos": photos
            }
            attractions.append(attraction_details)

        return jsonify(attractions)

    except requests.exceptions.RequestException as e:
        print("FourSquare API Error:", e)
        return jsonify({"error": str(e)}), 500
