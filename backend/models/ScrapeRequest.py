class ScrapeRequest:
    def __init__(self, lat, lng, text, filters=None):
        self.lat = lat
        self.lng = lng
        self.text = text
        self.filters = filters or {}

    @classmethod
    def from_dict(cls, data):
        return cls(
            lat=data.get('lat'),
            lng=data.get('lng'),
            text=data.get('text', ''),
            filters=data.get('filters', {})
        )
