from flask import Flask, request, jsonify
from flask_cors import CORS
from services.scraper_service import ScraperService
from models.ScrapeRequest import ScrapeRequest

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": [
    "https://habib-153.github.io",
    "http://localhost:3000"
]}})
scraper_service = ScraperService()


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "online",
        "message": "Khabo ki? Web Scraper API is running",
        "endpoints": {
            "/scrape": "POST - Scrape food delivery platforms"
        }
    })


@app.route('/scrape', methods=['POST'])
def scrape():
    """
    Endpoint to scrape food delivery platforms based on location
    
    Expected POST data:
    {
        "lat": 23.82257,
        "lng": 90.39329,
        "filters": {
            "cuisine": "...",
            "price_range": "...",
            "dietary": "...",
            ...
        }
    }
    """
    if not request.json:
        return jsonify({"error": "Invalid request format"}), 400

    try:
        # Parse the request data
        print("Received request data:", request.json)
        data = request.json
        if 'lat' not in data or 'lng' not in data:
            return jsonify({"error": "Missing required location parameters (lat, lng)"}), 400

        # Create scrape request object
        scrape_request = ScrapeRequest.from_dict(data)

        # Execute the scrape
        results = scraper_service.scrape(scrape_request)

        return jsonify({
            "success": True,
            "results": results
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True)