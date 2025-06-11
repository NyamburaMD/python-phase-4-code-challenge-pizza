#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

def validate_restaurant_pizza_payload(data):
    errors = []

    price = data.get("price")
    pizza_id = data.get("pizza_id")
    restaurant_id = data.get("restaurant_id")

    pizza = db.session.get(Pizza, pizza_id)
    restaurant = db.session.get(Restaurant, restaurant_id)

    if pizza is None:
        errors.append("Pizza not found")
    if restaurant is None:
        errors.append("Restaurant not found")
    if price is None or not isinstance(price, (int, float)) or price <= 0:
        errors.append("Invalid price")

    return errors, price, pizza, restaurant_id, pizza_id


class RestaurantListResource(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        data = [r.to_dict(only=("id", "name", "address")) for r in restaurants]
        return make_response(jsonify(data), 200)
    
class RestaurantResource(Resource):
    def get(self, id):
        restaurant = db.session.get(Restaurant, id)
        if not restaurant:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)
        
        data = restaurant.to_dict()
        data["restaurant_pizzas"] = [
            rp.to_dict(exclude=("-pizza.restaurant_pizzas", "-restaurant.restaurant_pizzas"))
            for rp in restaurant.restaurant_pizzas
        ]
        return make_response(jsonify(data), 200)
    def delete(self, id):
        restaurant = db.session.get(Restaurant, id)
        if not restaurant:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)
        
        db.session.delete(restaurant)
        db.session.commit()
        return "", 204
    
class PizzaListResource(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        data = [p.to_dict(only=("id", "name", "ingredients")) for p in pizzas]
        return make_response(jsonify(data), 200)


class RestaurantPizzaCreateResource(Resource):
    def post(self):
        data = request.get_json()
        errors, price, pizza, restaurant_id, pizza_id = validate_restaurant_pizza_payload(data)

        if errors:
            return jsonify({"errors": errors}), 400
        
        new_rp = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
        db.session.add(new_rp)
        db.session.commit()

        result = new_rp.to_dict(exclude=("-pizza.restaurant_pizzas", "-restaurant.restaurant_pizzas"))
        result["pizza"] = pizza.to_dict(only=("id", "name", "ingredients"))
        result["restaurant"] = db.session.get(Restaurant, restaurant_id).to_dict(only=("id", "name", "address"))

        return jsonify(result), 201
    

#routes
api.add_resource(RestaurantListResource, "/restaurants")
api.add_resource(RestaurantResource, "/restaurants/<int:id>")
api.add_resource(PizzaListResource, "/pizzas")
api.add_resource(RestaurantPizzaCreateResource, "/restaurant_pizzas")
    
if __name__ == "__main__":
    app.run(port=5555, debug=True)
    