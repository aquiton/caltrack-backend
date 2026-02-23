import time

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

_token_cache = {
    "access_token": None,
    "expires_at": 0
}

def get_access_token():
    """Returns a valid access token, fetching a new one if expired."""
    now = time.time()

    if _token_cache["access_token"] and now < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    # Encode credentials
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()

    response = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={"grant_type": "client_credentials", "scope": "basic"}
    )

    response.raise_for_status()
    token_data = response.json()

    # Cache token with a small buffer before expiry
    _token_cache["access_token"] = token_data["access_token"]
    _token_cache["expires_at"] = now + token_data["expires_in"] - 60

    return _token_cache["access_token"]

def get_food(food_id):
    """Get details for a specific food item."""
    token = get_access_token()

    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {token}"},
        params={
            "method": "food.get.v4",
            "food_id": food_id,
            "format": "json"
        }
    )

    response.raise_for_status()
    return response.json()

def get_food_by_barcode(barcode):
    """Look up a food item by its barcode (EAN-13 or UPC)."""
    token = get_access_token()

    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {token}"},
        params={
            "method": "food.find_id_for_barcode",
            "barcode": barcode,
            "format": "json"
        }
    )

    response.raise_for_status()
    result = response.json()

    # The barcode lookup returns a food_id, so we fetch the full details
    food_id = result.get("food_id", {}).get("value")
    if not food_id:
        return {"error": "No food found for this barcode"}

    return get_food(food_id)

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
