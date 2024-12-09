
import requests
from flask import Flask, Blueprint, request, jsonify

flight_blueprint = Blueprint('flight', __name__)

# OpenSky API 配置信息
OPENSKY_API_URL = "https://opensky-network.org/api/flights"
USERNAME = "bozhang3"  # 替换为你的用户名
PASSWORD = "Zz20001028"  # 替换为你的密码


@flight_blueprint.route('/departure', methods=['GET'])
def get_flights_departing():
    """
    获取指定机场的出发航班信息
    """
    airport = request.args.get('airport')  # 机场 IATA 代码
    begin = request.args.get('begin')  # 开始时间 (UNIX 时间戳)
    end = request.args.get('end')  # 结束时间 (UNIX 时间戳)

    if not airport or not begin or not end:
        return jsonify({"error": "Please provide airport, begin, and end parameters"}), 400

    try:
        url = f"{OPENSKY_API_URL}/departure"
        params = {
            "airport": airport,
            "begin": begin,
            "end": end
        }

        response = requests.get(url, auth=(USERNAME, PASSWORD), params=params)

        if response.status_code == 200:
            data = response.json()
            flights = []
            for flight in data:
                flights.append({
                    "icao24": flight.get("icao24"),
                    "callsign": flight.get("callsign"),
                    "departure_time": flight.get("firstSeen"),
                    "arrival_airport": flight.get("estArrivalAirport"),
                    "departure_airport": flight.get("estDepartureAirport"),
                    "arrival_time": flight.get("lastSeen"),
                })

            return jsonify(flights)
        else:
            return jsonify({"error": f"Failed to retrieve data. Status code: {response.status_code}"}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flight_blueprint.route('/arrival', methods=['GET'])
def get_flights_arriving():
    """
    获取指定机场的到达航班信息
    """
    airport = request.args.get('airport')  # 机场 IATA 代码
    begin = request.args.get('begin')  # 开始时间 (UNIX 时间戳)
    end = request.args.get('end')  # 结束时间 (UNIX 时间戳)

    if not airport or not begin or not end:
        return jsonify({"error": "Please provide airport, begin, and end parameters"}), 400

    try:
        url = f"{OPENSKY_API_URL}/arrival"
        params = {
            "airport": airport,
            "begin": begin,
            "end": end
        }

        response = requests.get(url, auth=(USERNAME, PASSWORD), params=params)

        if response.status_code == 200:
            data = response.json()
            flights = []
            for flight in data:
                flights.append({
                    "icao24": flight.get("icao24"),
                    "callsign": flight.get("callsign"),
                    "departure_time": flight.get("firstSeen"),
                    "arrival_airport": flight.get("estArrivalAirport"),
                    "departure_airport": flight.get("estDepartureAirport"),
                    "arrival_time": flight.get("lastSeen"),
                })

            return jsonify(flights)
        else:
            return jsonify({"error": f"Failed to retrieve data. Status code: {response.status_code}"}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 主 Flask 应用
app = Flask(__name__)
app.register_blueprint(flight_blueprint, url_prefix='/flights')

if __name__ == "__main__":
    app.run(debug=True)
