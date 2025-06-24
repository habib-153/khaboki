class ScrapeRequest:
    def __init__(self, lat, lng, filters=None):
        self.lat = lat
        self.lng = lng
        self.filters = filters or {}

    @classmethod
    def from_dict(cls, data):
        return cls(
            lat=data.get('lat'),
            lng=data.get('lng'),
            filters=data.get('filters', {})
        )
