from abc import ABC, abstractmethod


class BaseScraper(ABC):
    @abstractmethod
    def scrape(self, lat, lng, filters=None):
        """
        Scrape the website based on location coordinates and optional filters
        
        Args:
            lat (float): Latitude coordinate
            lng (float): Longitude coordinate
            filters (dict, optional): Additional filtering parameters
            
        Returns:
            list: List of Restaurant objects
        """
        pass
