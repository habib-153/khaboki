from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from services.scraper_service import ScraperService
from services.data_collection_service import dataset_builder
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
            "/scrape": "POST - Scrape food delivery platforms",
            "/dataset/export": "GET - Export dataset",
            "/dataset/stats": "GET - Get dataset statistics"
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
        "text": "location name",
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

        # # Execute the scrape
        results = scraper_service.scrape(scrape_request)

        # response_data = {
        #     "results": {
        #         "foodi": [
        #             {
        #                 "cuisine_type": "Pizza",
        #                 "delivery_fee": "69 tk",
        #                 "delivery_time": "5 - 15 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2FFoodpanda-Store-Cover2-de8c-20250125045618109.jpg&width=400",
        #                 "menu_items": [],
        #                 "name": "Domino's Pizza - ECB",
        #                 "offers": [
        #                     "Flat 20% Off"
        #                 ],
        #                 "platform": "Foodi",
        #                 "rating": "3.1(15)",
        #                 "url": "https://foodibd.com/restaurant/6243"
        #             },
        #             {
        #                 "cuisine_type": "Burger",
        #                 "delivery_fee": "37 tk",
        #                 "delivery_time": "10 - 25 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2FCover_1dbe_20240127130845460_e73f_20240521123648585.png&width=400",
        #                 "menu_items": [],
        #                 "name": "Khana's - ECB",
        #                 "offers": [
        #                     "Flat 10% Off"
        #                 ],
        #                 "platform": "Foodi",
        #                 "rating": "4.2(96)",
        #                 "url": "https://foodibd.com/restaurant/5613"
        #             },
        #             {
        #                 "cuisine_type": "Burger",
        #                 "delivery_fee": "37 tk",
        #                 "delivery_time": "5 - 20 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2FBanner-N-a91a-20241222045730811.jpg&width=400",
        #                 "menu_items": [],
        #                 "name": "MARS Restaurant",
        #                 "offers": [],
        #                 "platform": "Foodi",
        #                 "rating": "0",
        #                 "url": "https://foodibd.com/restaurant/6330"
        #             },
        #             {
        #                 "cuisine_type": "Sweets",
        #                 "delivery_fee": "37 tk",
        #                 "delivery_time": "5 - 20 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2FBanner-c961-20250423073445219.jpg&width=400",
        #                 "menu_items": [],
        #                 "name": "YARA - ECB",
        #                 "offers": [
        #                     "Flat 10% Off"
        #                 ],
        #                 "platform": "Foodi",
        #                 "rating": "4.2(4)",
        #                 "url": "https://foodibd.com/restaurant/7923"
        #             },
        #             {
        #                 "cuisine_type": "Kebab",
        #                 "delivery_fee": "37 tk",
        #                 "delivery_time": "15 - 30 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2FLIVE-KEBAB-830c-20250503050535892.jpg&width=400",
        #                 "menu_items": [],
        #                 "name": "Live Kebab - ECB",
        #                 "offers": [],
        #                 "platform": "Foodi",
        #                 "rating": "2.2(4)",
        #                 "url": "https://foodibd.com/restaurant/8050"
        #             },
        #             {
        #                 "cuisine_type": "Fast Food",
        #                 "delivery_fee": "37 tk",
        #                 "delivery_time": "15 - 30 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2FCover-8975-20240818054252929.jpg&width=400",
        #                 "menu_items": [],
        #                 "name": "Grand Bistro",
        #                 "offers": [
        #                     "Flat 10% Off"
        #                 ],
        #                 "platform": "Foodi",
        #                 "rating": "4.2(61)",
        #                 "url": "https://foodibd.com/restaurant/3896"
        #             },
        #             {
        #                 "cuisine_type": "Chinese",
        #                 "delivery_fee": "37 tk",
        #                 "delivery_time": "15 - 30 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2FCover_cee0_20240527045149876.jpg&width=400",
        #                 "menu_items": [],
        #                 "name": "Foodbees",
        #                 "offers": [],
        #                 "platform": "Foodi",
        #                 "rating": "3.1(10)",
        #                 "url": "https://foodibd.com/restaurant/2775"
        #             },
        #             {
        #                 "cuisine_type": "Bakery",
        #                 "delivery_fee": "37 tk",
        #                 "delivery_time": "5 - 20 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2Ftasty-Treat-Cover-n-3-6c18-20250129090827678.jpg&width=400",
        #                 "menu_items": [],
        #                 "name": "Tasty Treat - ECB Chattar",
        #                 "offers": [
        #                     "Flat 15% Off"
        #                 ],
        #                 "platform": "Foodi",
        #                 "rating": "4.2(18)",
        #                 "url": "https://foodibd.com/restaurant/372"
        #             },
        #             {
        #                 "cuisine_type": "Fast Food",
        #                 "delivery_fee": "37 tk",
        #                 "delivery_time": "5 - 20 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2Fcv_1984_20240325091101366.jpg&width=400",
        #                 "menu_items": [],
        #                 "name": "Munir's Kitchen",
        #                 "offers": [
        #                     "Flat 10% Off"
        #                 ],
        #                 "platform": "Foodi",
        #                 "rating": "3.0(2)",
        #                 "url": "https://foodibd.com/restaurant/1780"
        #             },
        #             {
        #                 "cuisine_type": "Fast Food",
        #                 "delivery_fee": "37 tk",
        #                 "delivery_time": "5 - 20 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2Fj1q3-listing-ec45-20250616110138414.jpg&width=400",
        #                 "menu_items": [],
        #                 "name": "The Meat Bar- ECB",
        #                 "offers": [
        #                     "Flat 10% Off"
        #                 ],
        #                 "platform": "Foodi",
        #                 "rating": "0",
        #                 "url": "https://foodibd.com/restaurant/2708"
        #             },
        #             {
        #                 "cuisine_type": "Chinese",
        #                 "delivery_fee": "37 tk",
        #                 "delivery_time": "5 - 20 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2FCV_cf4b_20240327041018288.jpg&width=400",
        #                 "menu_items": [],
        #                 "name": "Paragon Momo - ECB Chattar",
        #                 "offers": [
        #                     "Flat 10% Discount"
        #                 ],
        #                 "platform": "Foodi",
        #                 "rating": "3.8(12)",
        #                 "url": "https://foodibd.com/restaurant/1931"
        #             },
        #             {
        #                 "cuisine_type": "Sweets",
        #                 "delivery_fee": "37 tk",
        #                 "delivery_time": "5 - 20 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2FMeena-Sweets-Cover_7713_20240225103954184.jpg&width=400",
        #                 "menu_items": [],
        #                 "name": "Meena Sweets - ECB Meena Bazar",
        #                 "offers": [],
        #                 "platform": "Foodi",
        #                 "rating": "0",
        #                 "url": "https://foodibd.com/restaurant/3474"
        #             },
        #             {
        #                 "cuisine_type": "Fast Food",
        #                 "delivery_fee": "37 tk",
        #                 "delivery_time": "5 - 20 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2Fburg-sand-953a-20250512075033340.jpg&width=400",
        #                 "menu_items": [],
        #                 "name": "Sub Zone",
        #                 "offers": [],
        #                 "platform": "Foodi",
        #                 "rating": "3.7(3)",
        #                 "url": "https://foodibd.com/restaurant/8196"
        #             },
        #             {
        #                 "cuisine_type": "Fast Food",
        #                 "delivery_fee": "37 tk",
        #                 "delivery_time": "5 - 20 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2Fcv_fb0a_20240320093451225.jpg&width=400",
        #                 "menu_items": [],
        #                 "name": "Mr. Gosto",
        #                 "offers": [],
        #                 "platform": "Foodi",
        #                 "rating": "3.9(100+)",
        #                 "url": "https://foodibd.com/restaurant/1578"
        #             },
        #             {
        #                 "cuisine_type": "Fast Food",
        #                 "delivery_fee": "37 tk",
        #                 "delivery_time": "5 - 20 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2F3%20Food%20Banner%20N_80d0_20240416130109871.jpg&width=400",
        #                 "menu_items": [],
        #                 "name": "3 Food - ECB",
        #                 "offers": [],
        #                 "platform": "Foodi",
        #                 "rating": "3.9(22)",
        #                 "url": "https://foodibd.com/restaurant/817"
        #             },
        #             {
        #                 "cuisine_type": "Chinese",
        #                 "delivery_fee": "37 tk",
        #                 "delivery_time": "5 - 20 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2FCV_cf4b_20240327041018288.jpg&width=400",
        #                 "menu_items": [],
        #                 "name": "Paragon Momo - Agora ECB",
        #                 "offers": [
        #                     "Flat 10% Discount"
        #                 ],
        #                 "platform": "Foodi",
        #                 "rating": "0",
        #                 "url": "https://foodibd.com/restaurant/7891"
        #             },
        #             {
        #                 "cuisine_type": "Pizza",
        #                 "delivery_fee": "40 tk",
        #                 "delivery_time": "5 - 20 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2FCover_b945_20240708100633559.jpg&width=400",
        #                 "menu_items": [],
        #                 "name": "Lamppost (Sayem's Kitchen)",
        #                 "offers": [
        #                     "Flat 10% Off"
        #                 ],
        #                 "platform": "Foodi",
        #                 "rating": "3.6(14)",
        #                 "url": "https://foodibd.com/restaurant/3335"
        #             },
        #             {
        #                 "cuisine_type": "Burger",
        #                 "delivery_fee": "37 tk",
        #                 "delivery_time": "10 - 25 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2FKudos-Banner-8b22-20250512053811045.jpg&width=400",
        #                 "menu_items": [],
        #                 "name": "Kudos - ECB",
        #                 "offers": [
        #                     "Flat 10% Off"
        #                 ],
        #                 "platform": "Foodi",
        #                 "rating": "4.4(36)",
        #                 "url": "https://foodibd.com/restaurant/464"
        #             },
        #             {
        #                 "cuisine_type": "Burger",
        #                 "delivery_fee": "48 tk",
        #                 "delivery_time": "15 - 30 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2F581b93c8-f88f-11ec-b8fe-d2a16715da81-palace-texas-9d55-20240909045356222.jpg&width=400",
        #                 "menu_items": [],
        #                 "name": "Big Bite",
        #                 "offers": [],
        #                 "platform": "Foodi",
        #                 "rating": "4.2(16)",
        #                 "url": "https://foodibd.com/restaurant/4332"
        #             },
        #             {
        #                 "cuisine_type": "Biryani",
        #                 "delivery_fee": "37 tk",
        #                 "delivery_time": "5 - 20 min",
        #                 "image_url": "https://imrs.foodibd.com/api/v1/image-resize?imageUrl=https%3A%2F%2Fs3.ap-southeast-1.amazonaws.com%2Fcdn.foodibd.com%2Frestaurant-service%2Fc9252e6c6cd289c588c3381bc77b1dfc-1-b82d-20250129051137819.jpeg&width=400",
        #                 "menu_items": [],
        #                 "name": "Chapter - ECB",
        #                 "offers": [
        #                     "Flat 10% Off"
        #                 ],
        #                 "platform": "Foodi",
        #                 "rating": "3.0(1)",
        #                 "url": "https://foodibd.com/restaurant/6879"
        #             }
        #         ],
        #         "foodpanda": [
        #             {
        #                 "cuisine_type": "Fast Food",
        #                 "delivery_fee": "Tk31",
        #                 "delivery_time": "30-45 min",
        #                 "image_url": "https://images.deliveryhero.io/image/fd-bd/LH/cq6i-listing.jpg?width=400&height=225",
        #                 "menu_items": [],
        #                 "name": "Tasty Bites- Matikata",
        #                 "offers": [
        #                     "15% off Tk. 50"
        #                 ],
        #                 "platform": "FoodPanda",
        #                 "rating": "3.7(72)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/cq6i/tasty-bites-matikata"
        #             },
        #             {
        #                 "cuisine_type": "Middle Eastern",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "40-60 min",
        #                 "image_url": "https://images.deliveryhero.io/image/fd-bd/LH/zx18-listing.jpg?width=400&height=225",
        #                 "menu_items": [],
        #                 "name": "TOUM - Mirpur",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.9(2000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/zx18/toum-mirpur"
        #             },
        #             {
        #                 "cuisine_type": "Fast Food",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "35-55 min",
        #                 "image_url": "https://images.deliveryhero.io/image/fd-bd/LH/la6d-listing.jpg?width=400&height=225",
        #                 "menu_items": [],
        #                 "name": "Big Q - Mirpur",
        #                 "offers": [
        #                     "10% off Tk. 300"
        #                 ],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.5(9)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/la6d/big-q-mirpur"
        #             },
        #             {
        #                 "cuisine_type": "Burgers",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "45-65 min",
        #                 "image_url": "https://images.deliveryhero.io/image/fd-bd/LH/n3fm-listing.jpg?width=400&height=225",
        #                 "menu_items": [],
        #                 "name": "Burger Xpress - Mirpur",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.8(30000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/n3fm/burger-xpress-mirpur"
        #             },
        #             {
        #                 "cuisine_type": "Pizza",
        #                 "delivery_fee": "Tk51",
        #                 "delivery_time": "40-60 min",
        #                 "image_url": "https://images.deliveryhero.io/image/fd-bd/LH/zeh5-listing.jpg?width=400&height=225",
        #                 "menu_items": [],
        #                 "name": "PizzaBurg - Pallabi",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.8(5000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/zeh5/pizzaburg-pallabi"
        #             },
        #             {
        #                 "cuisine_type": "Biryani",
        #                 "delivery_fee": "Tk87",
        #                 "delivery_time": "45-65 min",
        #                 "image_url": "https://images.deliveryhero.io/image/fd-bd/LH/jzy0-listing.jpg?width=400&height=225",
        #                 "menu_items": [],
        #                 "name": "Sultan's Dine - Mirpur 12",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.8(4000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/jzy0/sultans-dine-mirpur-12"
        #             },
        #             {
        #                 "cuisine_type": "Chicken",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "40-60 min",
        #                 "image_url": "https://images.deliveryhero.io/image/fd-bd/LH/x8h4-listing.jpg?width=400&height=225",
        #                 "menu_items": [],
        #                 "name": "Chicken Buzz - Mirpur",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.7(2000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/x8h4/chicken-buzz-mirpur"
        #             },
        #             {
        #                 "cuisine_type": "Fried Chicken",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "40-60 min",
        #                 "image_url": "https://images.deliveryhero.io/image/fd-bd/LH/hcfh-listing.jpg?width=400&height=225",
        #                 "menu_items": [],
        #                 "name": "Best Fried Chicken - Mirpur 12",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.8(10000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/hcfh/best-fried-chicken-mirpur-12"
        #             },
        #             {
        #                 "cuisine_type": "Biryani",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "40-60 min",
        #                 "image_url": "https://images.deliveryhero.io/image/fd-bd/LH/t7zo-listing.jpg?width=400&height=225",
        #                 "menu_items": [],
        #                 "name": "Kacchi Bhai - Mirpur 10",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.7(30000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/t7zo/kacchi-bhai-mirpur-10"
        #             },
        #             {
        #                 "cuisine_type": "Fast Food",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "45-65 min",
        #                 "image_url": "https://images.deliveryhero.io/image/fd-bd/LH/s0hs-listing.jpg?width=400&height=225",
        #                 "menu_items": [],
        #                 "name": "Madchef - Mirpur",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.9(15000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/s0hs/madchef-mirpur"
        #             },
        #             {
        #                 "cuisine_type": "Bangladeshi",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "35-55 min",
        #                 "image_url": "https://images.deliveryhero.io/image/fd-bd/LH/jwxn-listing.jpg?width=400&height=225",
        #                 "menu_items": [],
        #                 "name": "Shiraj Chui Gosto - Mirpur 10",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.6(4000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/jwxn/shiraj-chui-gosto-mirpur-10"
        #             },
        #             {
        #                 "cuisine_type": "Fast Food",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "35-55 min",
        #                 "image_url": "https://images.deliveryhero.io/image/fd-bd/LH/u5sk-listing.jpg?width=400&height=225",
        #                 "menu_items": [],
        #                 "name": "Takeout - Mirpur",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.9(15000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/u5sk/takeout-mirpur"
        #             },
        #             {
        #                 "cuisine_type": "Fast Food",
        #                 "delivery_fee": "Tk87",
        #                 "delivery_time": "50-70 min",
        #                 "image_url": "https://images.deliveryhero.io/image/fd-bd/LH/v9ad-listing.jpg?width=400&height=225",
        #                 "menu_items": [],
        #                 "name": "Khana's Mirpur",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.7(10000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/v9ad/khanas-mirpur"
        #             },
        #             {
        #                 "cuisine_type": "Fast Food",
        #                 "delivery_fee": "Tk9",
        #                 "delivery_time": "20-35 min",
        #                 "image_url": "https://images.deliveryhero.io/image/fd-bd/LH/s6ve-listing.jpg?width=400&height=225",
        #                 "menu_items": [],
        #                 "name": "Mr. Gosto",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.4(1000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/s6ve/mr-gosto"
        #             },
        #             {
        #                 "cuisine_type": "Cafe",
        #                 "delivery_fee": "Tk9",
        #                 "delivery_time": "30-45 min",
        #                 "image_url": "https://images.deliveryhero.io/image/fd-bd/LH/jqgv-listing.jpg?width=400&height=225",
        #                 "menu_items": [],
        #                 "name": "Hungry Eyes 5 - (ECB Chattor)",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.6(100+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/jqgv/hungry-eyes-5-ecb-chattor"
        #             },
        #             {
        #                 "cuisine_type": "Pizza",
        #                 "delivery_fee": "Tk69",
        #                 "delivery_time": "15-30 min",
        #                 "image_url": "https://images.deliveryhero.io/image/fd-bd/LH/cd9p-listing.jpg?width=400&height=225",
        #                 "menu_items": [],
        #                 "name": "Domino's Pizza ECB Chattar",
        #                 "offers": [
        #                     "Up to 15% off"
        #                 ],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.8(100+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/cd9p/dominos-pizza-ecb-chattar"
        #             },
        #             {
        #                 "cuisine_type": "Burgers",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "30-45 min",
        #                 "image_url": "https://images.deliveryhero.io/image/fd-bd/LH/u25g-listing.jpg?width=400&height=225",
        #                 "menu_items": [],
        #                 "name": "Chillox - Kachukhet",
        #                 "offers": [
        #                     "10% off Tk. 50"
        #                 ],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.7(500+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/u25g/chillox-kachukhet"
        #             },
        #             {
        #                 "cuisine_type": "Rice Dishes",
        #                 "delivery_fee": "Tk9",
        #                 "delivery_time": "20-35 min",
        #                 "image_url": "https://images.deliveryhero.io/image/fd-bd/LH/lvta-listing.jpg?width=400&height=225",
        #                 "menu_items": [],
        #                 "name": "Bismillah Biryani House- Manikdi",
        #                 "offers": [
        #                     "16% off Tk. 50"
        #                 ],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.8(500+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/lvta/bismillah-biryani-house-manikdi"
        #             },
        #             {
        #                 "cuisine_type": "Biryani",
        #                 "delivery_fee": "Tk87",
        #                 "delivery_time": "35-55 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Haji Biryani House",
        #                 "offers": [
        #                     "12% off Tk. 50"
        #                 ],
        #                 "platform": "FoodPanda",
        #                 "rating": "4(5000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/n7y3/haji-biryani-house-n7y3"
        #             },
        #             {
        #                 "cuisine_type": "Snacks",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "30-45 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Dhaba Mirpur",
        #                 "offers": [
        #                     "Up to 15% off Tk. 50"
        #                 ],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.7(10000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/s8kx/dhaba-mirpur"
        #             },
        #             {
        #                 "cuisine_type": "Pizza",
        #                 "delivery_fee": "Tk87",
        #                 "delivery_time": "45-65 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Pizza Heist",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.6(5000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/r7hf/pizza-heist"
        #             },
        #             {
        #                 "cuisine_type": "Chinese",
        #                 "delivery_fee": "Tk87",
        #                 "delivery_time": "45-65 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Grand Prince Thai & Chinese Restaurant - Pallabi",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.8(4000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/wuce/grand-prince-thai-and-chinese-restaurant-pallabi"
        #             },
        #             {
        #                 "cuisine_type": "Fast Food",
        #                 "delivery_fee": "Tk9",
        #                 "delivery_time": "30-45 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Kudos- ECB",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.7(500+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/q8wz/kudos-ecb"
        #             },
        #             {
        #                 "cuisine_type": "Burgers",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "40-60 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Herfy - Mirpur",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.9(3000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/gt6t/herfy-mirpur"
        #             },
        #             {
        #                 "cuisine_type": "Biryani",
        #                 "delivery_fee": "Tk56",
        #                 "delivery_time": "25-40 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Bismillah Hanif Biryani - Mirpur 11",
        #                 "offers": [
        #                     "15% off Tk. 50"
        #                 ],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.1(100+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/wrjg/bismillah-hanif-biryani-mirpur-11"
        #             },
        #             {
        #                 "cuisine_type": "Burgers",
        #                 "delivery_fee": "Tk9",
        #                 "delivery_time": "25-40 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "3food ECB",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.7(100+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/n0vz/3food-ecb"
        #             },
        #             {
        #                 "cuisine_type": "Pizza",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "50-70 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Cheez - Mirpur",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.7(5000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/u3hn/cheez-mirpur"
        #             },
        #             {
        #                 "cuisine_type": "Biryani",
        #                 "delivery_fee": "Tk87",
        #                 "delivery_time": "30-45 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Shader Adda Biryani House",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.6(2000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/rcsh/shader-adda-biryani-house"
        #             },
        #             {
        #                 "cuisine_type": "Dessert",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "35-55 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Waffle Up - Mirpur",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.9(4000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/y95a/waffle-up-mirpur"
        #             },
        #             {
        #                 "cuisine_type": "Rice Dishes",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "40-60 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "8 Number Dokan - Mirpur",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "3.9(3000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/trq9/8-number-dokan-mirpur"
        #             },
        #             {
        #                 "cuisine_type": "Bangladeshi",
        #                 "delivery_fee": "Tk87",
        #                 "delivery_time": "55-75 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Shiraj Chui Gosto - Mirpur",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.6(5000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/d5os/shiraj-chui-gosto-mirpur"
        #             },
        #             {
        #                 "cuisine_type": "Snacks",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "35-55 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Coffee Mania",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.8(4000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/s9vk/coffee-mania"
        #             },
        #             {
        #                 "cuisine_type": "Fast Food",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "35-55 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Cornucopia",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.6(4000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/t9cm/cornucopia"
        #             },
        #             {
        #                 "cuisine_type": "Fried Chicken",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "30-45 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "KFC - Kachukhet",
        #                 "offers": [
        #                     "Up to 28% off"
        #                 ],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.8(1000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/hoyb/kfc-kachukhet"
        #             },
        #             {
        #                 "cuisine_type": "Burgers",
        #                 "delivery_fee": "Tk87",
        #                 "delivery_time": "45-65 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Cafe Twisted Burg",
        #                 "offers": [
        #                     "12% off Tk. 50"
        #                 ],
        #                 "platform": "FoodPanda",
        #                 "rating": "3.8(500+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/egaf/cafe-twisted-burg"
        #             },
        #             {
        #                 "cuisine_type": "Bangladeshi",
        #                 "delivery_fee": "Tk87",
        #                 "delivery_time": "30-45 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Rabbani Hotel And Restaurant (New Mirpur-10)",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.8(2000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/it8o/rabbani-hotel-and-restaurant-new-mirpur-10"
        #             },
        #             {
        #                 "cuisine_type": "Fast Food",
        #                 "delivery_fee": "Tk9",
        #                 "delivery_time": "30-45 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "The Meat Bar- ECB",
        #                 "offers": [
        #                     "11% off Tk. 50"
        #                 ],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.1(100+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/j1q3/the-meat-bar-ecb"
        #             },
        #             {
        #                 "cuisine_type": "Kebab",
        #                 "delivery_fee": "Tk73",
        #                 "delivery_time": "25-40 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Lahori Kabab",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.7(500+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/qcrl/lahori-kabab"
        #             },
        #             {
        #                 "cuisine_type": "Pizza",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "50-70 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Street Oven - Mirpur DOHS",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.3(5000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/t7vx/street-oven-mirpur-dohs"
        #             },
        #             {
        #                 "cuisine_type": "Burgers",
        #                 "delivery_fee": "Tk87",
        #                 "delivery_time": "55-75 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Burger Lab - Mirpur",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.9(5000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/u8xi/burger-lab-mirpur"
        #             },
        #             {
        #                 "cuisine_type": "Chinese",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "30-45 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Celebrate Cafe & Restaurant",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.8(2000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/s6xj/celebrate-cafe-and-restaurant"
        #             },
        #             {
        #                 "cuisine_type": "Dessert",
        #                 "delivery_fee": "Tk9",
        #                 "delivery_time": "20-35 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Tasty Treat - ECB Chattor",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.5(500+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/jcf7/tasty-treat-ecb-chattor"
        #             },
        #             {
        #                 "cuisine_type": "Rice Dishes",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "35-55 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Abesh Hotel & Biryani House - Mirpur-12",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.7(2000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/rveh/abesh-hotel-and-biryani-house-mirpur-12"
        #             },
        #             {
        #                 "cuisine_type": "Fast Food",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "40-60 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Chunk - Mirpur",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.3(500+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/ccfw/chunk-mirpur"
        #             },
        #             {
        #                 "cuisine_type": "Fast Food",
        #                 "delivery_fee": "Tk73",
        #                 "delivery_time": "35-50 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Sub Hub",
        #                 "offers": [
        #                     "15% off Tk. 50"
        #                 ],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.5(3000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/s0jw/sub-hub"
        #             },
        #             {
        #                 "cuisine_type": "Bangladeshi",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "35-55 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Rabbani Hotel And Restaurant - Mirpur 11",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.6(5000+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/b6et/rabbani-hotel-and-restaurant-mirpur-11-b6et"
        #             },
        #             {
        #                 "cuisine_type": "Kebab",
        #                 "delivery_fee": "Tk9",
        #                 "delivery_time": "20-35 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Amish Proteen - ECB Chattar",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.7(500+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/zqkx/amish-proteen-ecb-chattar"
        #             },
        #             {
        #                 "cuisine_type": "Bangladeshi",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "40-60 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Fries & Rice - Mirpur",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "3.9(100+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/kxie/fries-and-rice-mirpur"
        #             },
        #             {
        #                 "cuisine_type": "Dumpling",
        #                 "delivery_fee": "Tk9",
        #                 "delivery_time": "20-35 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Paragon Momo - Meenabazar ECB Chattar",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "4.9(100+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/b0wc/paragon-momo-meenabazar-ecb-chattar"
        #             },
        #             {
        #                 "cuisine_type": "Pizza",
        #                 "delivery_fee": "Tk78",
        #                 "delivery_time": "50-70 min",
        #                 "image_url": "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg",
        #                 "menu_items": [],
        #                 "name": "Diggger - Mirpur-11",
        #                 "offers": [],
        #                 "platform": "FoodPanda",
        #                 "rating": "3.6(100+)",
        #                 "url": "https://www.foodpanda.com.bd/restaurant/zxqw/diggger-mirpur-11"
        #             }
        #         ]
        #     },
        #     "success": True,
        #     # "re": results
        # }

        response_data = {
            "success": True,
            "results": results
        }

        # Add to dataset in background (non-blocking)
        # try:
        #     lat = float(data.get('lat'))
        #     lng = float(data.get('lng'))
        #     dataset_builder.add_scraped_data(response_data, lat, lng)
        #     print(f"[DATASET] Queued data for processing: {lat}, {lng}")
        # except Exception as dataset_error:
        #     print(f"[DATASET] Error queuing data: {dataset_error}")

        return jsonify(response_data)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/dataset/export', methods=['GET'])
def export_dataset():
    """Export the dataset"""
    try:
        format_type = request.args.get('format', 'json')
        file_path = dataset_builder.export_dataset(format_type)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/dataset/stats', methods=['GET'])
def dataset_stats():
    """Get dataset statistics"""
    try:
        print("[DEBUG] dataset_stats endpoint called")
        stats = dataset_builder.get_stats()
        print(f"[DEBUG] Stats result: {stats}")
        return jsonify(stats)
    except Exception as e:
        print(f"[ERROR] Error in dataset_stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)