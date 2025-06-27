class Restaurant:
    def __init__(self, name, cuisine_type, rating, delivery_time, delivery_fee, platform, offers=[], image_url=None, url=None):
        self.name = name
        self.cuisine_type = cuisine_type
        self.rating = rating
        self.delivery_time = delivery_time
        self.delivery_fee = delivery_fee
        self.platform = platform
        self.image_url = image_url
        self.url = url
        self.offers = offers
        self.menu_items = []

    def to_dict(self):
        return {
            "name": self.name,
            "cuisine_type": self.cuisine_type,
            "rating": self.rating,
            "delivery_time": self.delivery_time,
            "delivery_fee": self.delivery_fee,
            "platform": self.platform,
            "image_url": self.image_url,
            "url": self.url,
            "offers": self.offers,
            "menu_items": [item.to_dict() for item in self.menu_items]
        }
