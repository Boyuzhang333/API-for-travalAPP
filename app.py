from flask import Flask
from services.weather import weather_blueprint
#from services.trains import train_blueprint
#from services.flight import flight_blueprint
#from services.hotel import hotel_blueprint
#from services.restaurants import restaurant_blueprint

app = Flask(__name__)

# 注册不同的蓝图
app.register_blueprint(weather_blueprint, url_prefix='/weather')
#app.register_blueprint(train_blueprint, url_prefix='/trains')
#app.register_blueprint(flight_blueprint, url_prefix='/flights')
#app.register_blueprint(hotel_blueprint, url_prefix='/hotels')
#app.register_blueprint(restaurant_blueprint, url_prefix='/restaurants')

if __name__ == '__main__':
    app.run(debug=True)
