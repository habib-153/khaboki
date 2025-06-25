from utils.FoodPandaScraper import FoodPandaScraper
from utils.FoodiScraper import FoodiScraper

class ScraperService:
    def __init__(self):
        # Initialize the scrapers
        print("Initializing scrapers...")
        self.scrapers = {
            "foodpanda": FoodPandaScraper(),
            "foodi": FoodiScraper(),
        }

    def scrape(self, scrape_request):
        """
        Main method to scrape data from all configured delivery platforms
        
        Args:
            scrape_request (ScrapeRequest): The scrape request containing location and filters
            
        Returns:
            dict: Combined results from all scrapers
        """
        print(f"Received scrape request: {scrape_request}")

        results = {}

        # Scrape from each platform
        for platform, scraper in self.scrapers.items():
            print(f"Scraping from {platform}...")
            try:
                platform_results = scraper.scrape(
                    scrape_request.lat,
                    scrape_request.lng,
                    scrape_request.text,
                    scrape_request.filters
                )

                # Convert to dict for JSON serialization
                results[platform] = [restaurant.to_dict()
                                     for restaurant in platform_results]
                print(
                    f"Found {len(results[platform])} restaurants on {platform}")

            except Exception as e:
                print(f"Error scraping {platform}: {e}")
                results[platform] = {"error": str(e)}

        return results