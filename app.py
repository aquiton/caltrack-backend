import time
from requests_oauthlib import OAuth1
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from supabase import create_client, Client
import os
import base64
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("FATSECRET_CLIENT_ID")
CLIENT_SECRET = os.getenv("FATSECRET_CLIENT_SECRET")
TOKEN_URL = "https://oauth.fatsecret.com/connect/token"
API_URL = "https://platform.fatsecret.com/rest/server.api"

from requests_oauthlib import OAuth1

CONSUMER_KEY = os.getenv("FATSECRET_CLIENT_ID")
CONSUMER_SECRET = os.getenv("FATSECRET_CLIENT_SECRET")

def get_food_by_barcode(barcode):
    auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET)
    response = requests.get(
        "https://platform.fatsecret.com/rest/server.api",
        auth=auth,
        params={
            "method": "food.find_id_for_barcode",
            "barcode": barcode,
            "format": "json"
        }
    )
    response.raise_for_status()
    return response.json()

def get_food(food_id):
    auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET)
    response = requests.get(
        "https://platform.fatsecret.com/rest/server.api",
        auth=auth,
        params={
            "method": "food.get.v4",
            "food_id": food_id,
            "format": "json"
        }
    )
    response.raise_for_status()
    return response.json()


app = Flask(__name__)
CORS(app)

# Load from environment or hardcode (for local dev)
SUPABASE_URL = os.environ.get("SUPABASE_URL") or "https://YOUR_SUPABASE_URL.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or "YOUR_SUPABASE_ANON_KEY"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Default route
@app.route("/")
def default():
    return jsonify({"message": "Hello from caltrack backend!"})
# Test route
@app.route("/api/hello")
def hello():
    res = get_food_by_barcode('0889392001549')
    foodres = get_food(res.get('food_id').get('value'))
    print(foodres)
    return jsonify({"message": "Hello from Flask + Supabase!"})

# Add a meal
@app.route("/api/meals", methods=["POST"])
def add_meal():
    data = request.json
    meal = {
        "name": data.get("name"),
        "calories": data.get("calories"),
        "user_id": data.get("user_id", "anonymous")
    }
    response = supabase.table("meals").insert(meal).execute()
    return jsonify(response.data)

# Get meals
@app.route("/api/meals", methods=["GET"])
def get_meals():
    response = supabase.table("meals").select("*").execute()
    print("Response Data: ", response.data[0])
    return jsonify(response.data[0])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
