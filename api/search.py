import os
import sys

# Dynamically add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from flask import Flask, request, jsonify, Blueprint, g
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError
from model.search import SearchHistory, db
from api.jwt_authorize import token_required
from model.user import User

# Initialize Flask app
app = Flask(__name__)

# Apply CORS settings to the app
CORS(app, supports_credentials=True, origins=["http://127.0.0.1:4887"])

# Define the Blueprint
search_api = Blueprint("search_api", __name__, url_prefix="/api/search")

# Items data
items = [
    {"name": "Teddy Bear", "link": "holiday/toys", "tags": {"all": 1, "teddy": 0, "bear": 0, "toys": 0}},
    {"name": "Lego Set", "link": "holiday/toys", "tags": {"all": 1, "lego": 0, "set": 0, "toys": 0}},
    {"name": "Remote Control Car", "link": "holiday/toys", "tags": {"all": 1, "remote": 0, "control": 0, "car": 0, "toys": 0}},
    {"name": "Holiday Candles", "link": "holiday/home-decor", "tags": {"all": 1, "holiday": 0, "candles": 0, "home-decor": 0}},
    # Additional items omitted for brevity...
]

@search_api.route("", methods=["GET", "OPTIONS"])
@token_required()
def search_items():
    """
    Search for items based on a query string, and log the search in the database for the authenticated user.
    """
    if request.method == "OPTIONS":
        return _cors_preflight_response()

    query = request.args.get("q", "").lower()
    current_user = g.current_user  # Get authenticated user
    user_id = current_user.uid

    if not query:
        return jsonify([])

    # Search logic
    results = [
        item for item in items if query in item["name"].lower() or any(query in tag for tag in item["tags"])
    ]

    # Save search query to the database
    try:
        associated_tags = [item["tags"] for item in results]
        search_entry = SearchHistory(user=user_id, query=query, tags=associated_tags)
        db.session.add(search_entry)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to log search query: {str(e)}"}), 500

    return jsonify(results), 200


@search_api.route("/increment_tag", methods=["POST", "OPTIONS"])
@token_required()
def increment_tag():
    """
    Increment the tags for a specific item for the authenticated user.
    """
    if request.method == "OPTIONS":
        return _cors_preflight_response()

    data = request.get_json()
    if not data or "name" not in data:
        return jsonify({"error": "Invalid data"}), 400

    current_user = g.current_user  # Get authenticated user
    item_name = data["name"]

    # Find the item in the catalog
    item = next((item for item in items if item["name"].lower() == item_name.lower()), None)
    if item:
        # Increment tags for the item
        for tag in item["tags"]:
            item["tags"][tag] += 1

        # Log the tag update in the user's history
        try:
            search_entry = SearchHistory(user=current_user.uid, query=item_name, tags=item["tags"])
            db.session.add(search_entry)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to log tag increment: {str(e)}"}), 500

        return jsonify({"message": f"Tags for '{item_name}' updated successfully!", "tags": item["tags"]}), 200

    return jsonify({"error": "Item not found!"}), 404


def _cors_preflight_response():
    """
    Helper function to return a 200 OK response for CORS preflight requests.
    """
    response = jsonify({"message": "CORS preflight check passed!"})
    response.status_code = 200
    response.headers.add("Access-Control-Allow-Origin", "http://127.0.0.1:4887")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    return response


@app.after_request
def add_cors_headers(response):
    """
    Ensures all responses include the necessary CORS headers.
    """
    response.headers.add("Access-Control-Allow-Origin", "http://127.0.0.1:4887")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    return response


# Register the Blueprint
app.register_blueprint(search_api)

# Run the app
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8887)
