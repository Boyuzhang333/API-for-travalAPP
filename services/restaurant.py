import os
from flask import Flask, Blueprint, request, jsonify
import requests
import hashlib
from dotenv import load_dotenv  # 从 python-dotenv 导入加载函数

# 创建 Flask 应用
app = Flask(__name__)

# 配置信息
FOURSQUARE_API_KEY = os.getenv('FOURSQUARE_API_KEY')  # 从环境变量读取 API Key
if not FOURSQUARE_API_KEY:
    raise EnvironmentError("FOURSQUARE_API_KEY is not set. Please set it in the environment variables.")
SEARCH_URL = 'https://api.foursquare.com/v3/places/search'
DETAIL_URL = 'https://api.foursquare.com/v3/places'
PHOTO_URL = 'https://api.foursquare.com/v3/places/{fsq_id}/photos'
NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'

# 创建蓝图
restaurant_blueprint = Blueprint('restaurant', __name__)

def generate_rating_and_price(fsq_id):
    """
    根据 fsq_id 生成稳定的评分和价格，并符合实际。
    """
    # 使用哈希函数将 fsq_id 转换为整数
    hash_value = int(hashlib.md5(fsq_id.encode()).hexdigest(), 16)
    
    # 生成评分（3.0 到 5.0 之间的浮点数）
    rating = 3.0 + (hash_value % 2000) / 1000.0  # 结果范围是 [3.0, 5.0]
    
    # 生成价格（10 到 50 的整数，表示欧元）
    price = 10 + (hash_value % 41)  # 结果范围是 [10, 50]
    
    return round(rating, 1), price


# 城市名转经纬度函数
def convert_city_to_lat_lng(city_name):
    """
    使用 Nominatim API 将城市名称转换为经纬度
    """
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

@restaurant_blueprint.route('/', methods=['GET'])
def get_restaurants_with_details():
    """
    搜索餐厅并返回详细信息
    """
    city_name = request.args.get('city')
    radius = request.args.get('radius', 1000)
    limit = request.args.get('limit', 5)

    if not city_name:
        return jsonify({"error": "Please provide a city name"}), 400

    # 将城市名转换为经纬度
    location = convert_city_to_lat_lng(city_name)
    if not location:
        return jsonify({"error": f"Failed to retrieve location for city: {city_name}"}), 500

    headers = {'Authorization': FOURSQUARE_API_KEY}
    params = {
        'll': location,
        'radius': radius,
        'categories': '13065',
        'limit': limit
    }

    try:
        # 搜索餐厅
        search_response = requests.get(SEARCH_URL, headers=headers, params=params)
        search_response.raise_for_status()
        search_data = search_response.json()

        restaurants = []
        for place in search_data.get("results", []):
            fsq_id = place.get("fsq_id")

            # 获取详细信息
            detail_response = requests.get(f"{DETAIL_URL}/{fsq_id}", headers=headers)
            detail_response.raise_for_status()
            detail_data = detail_response.json()

            # 获取图片信息
            photo_response = requests.get(PHOTO_URL.replace("{fsq_id}", fsq_id), headers=headers)
            photo_response.raise_for_status()
            photos = photo_response.json()

            # 整合数据
            # 使用 fsq_id 生成评分和价格
            generated_rating, generated_price = generate_rating_and_price(fsq_id)

            # 整合数据
            restaurant_details = {
                "name": detail_data.get("name", "No name available"),
                "categories": [cat["name"] for cat in detail_data.get("categories", [])],
                "rating": generated_rating,
                "price": f"{generated_price}€",
                "location": detail_data.get("location", {}).get("formatted_address", "No address available"),
                "phone": detail_data.get("tel", "No phone available"),
                "website": detail_data.get("website", "No website available"),
                "photos": [
                    f"{photo['prefix']}original{photo['suffix']}" for photo in photos
                ] if photos else ["No photo available"]
            }

            restaurants.append(restaurant_details)

        return jsonify(restaurants)

    except requests.exceptions.RequestException as e:
        print("FourSquare API Error:", e)
        return jsonify({"error": str(e)}), 500

# 注册蓝图
app.register_blueprint(restaurant_blueprint, url_prefix='/restaurants')

if __name__ == '__main__':
    app.run(debug=True)
#http://127.0.0.1:5000/restaurants/?city=New%20York&radius=1000&limit=3