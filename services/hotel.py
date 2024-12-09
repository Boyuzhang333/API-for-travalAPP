import os
from flask import Blueprint, request, jsonify
import requests
import hashlib
from dotenv import load_dotenv  # 从 python-dotenv 导入加载函数


hotel_blueprint = Blueprint('hotel', __name__)

FOURSQUARE_API_KEY = os.getenv('FOURSQUARE_API_KEY')  # 从环境变量读取 API Key
if not FOURSQUARE_API_KEY:
    raise EnvironmentError("FOURSQUARE_API_KEY is not set. Please set it in the environment variables.")
SEARCH_URL = 'https://api.foursquare.com/v3/places/search'
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
    price = 80 + (hash_value % 90)  # 结果范围是 [15, 50]
    return round(rating, 1), price

# 获取照片信息
def fetch_photos(fsq_id):
    headers = {'Authorization': FOURSQUARE_API_KEY}
    try:
        response = requests.get(PHOTO_URL.format(fsq_id=fsq_id), headers=headers)
        response.raise_for_status()
        photos = response.json()
        # 返回所有照片的完整 URL
        return [
            f"{photo['prefix']}original{photo['suffix']}" for photo in photos
        ] if photos else ["No photo available"]
    except requests.exceptions.RequestException as e:
        print("Photo API Error:", e)
        return ["No photo available"]

@hotel_blueprint.route('/', methods=['GET'])
def get_hotels():
    city_name = request.args.get('city')
    radius = request.args.get('radius', 1000)
    limit = request.args.get('limit', 5)

    if not city_name:
        return jsonify({"error": "Please provide a city name"}), 400

    location = convert_city_to_lat_lng(city_name)
    if not location:
        return jsonify({"error": f"Failed to retrieve location for city: {city_name}"}), 500

    headers = {'Authorization': FOURSQUARE_API_KEY}
    params = {
        'll': location,
        'radius': radius,
        'categories': '19014',  # 酒店分类 ID
        'limit': limit
    }

    try:
        response = requests.get(SEARCH_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        hotels = []
        for place in data.get("results", []):
            fsq_id = place.get("fsq_id")
            rating, price = generate_rating_and_price(fsq_id)

            # 获取照片
            photos = fetch_photos(fsq_id)

            hotel_details = {
                "name": place.get("name", "No name available"),
                "location": place.get("location", {}).get("address", "No address available"),
                "distance": place.get("distance", "Unknown"),
                "rating": rating,
                "price": f"{price}€",
                "categories": [cat["name"] for cat in place.get("categories", [])],
                "photos": photos
            }
            hotels.append(hotel_details)

        return jsonify(hotels)

    except requests.exceptions.RequestException as e:
        print("FourSquare API Error:", e)
        return jsonify({"error": str(e)}), 500

# http://127.0.0.1:5000/hotel/?city=Nice&radius=1000&limit=5
