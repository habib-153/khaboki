from utils.FoodPandaScraper import FoodPandaScraper
from utils.FoodiScraper import FoodiScraper
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

class ScraperService:
    def __init__(self):
        self.scrapers = {
            "foodpanda": FoodPandaScraper(),
            "foodi": FoodiScraper(),
        }
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def _scrape_platform_async(self, platform_name, scraper, scrape_request):
        print(f"Starting async scrape for {platform_name}...")
        start_time = time.time()

        try:
            # Run the blocking scraper in a thread pool
            loop = asyncio.get_event_loop()
            platform_results = await loop.run_in_executor(
                self.executor,
                scraper.scrape,
                scrape_request.lat,
                scrape_request.lng,
                scrape_request.text,
                scrape_request.filters
            )

            # Convert to dict for JSON serialization
            result = [restaurant.to_dict() for restaurant in platform_results]

            end_time = time.time()
            print(
                f"✅ {platform_name} completed in {end_time - start_time:.2f}s - Found {len(result)} restaurants")

            return platform_name, result

        except Exception as e:
            end_time = time.time()
            print(
                f"❌ {platform_name} failed in {end_time - start_time:.2f}s - Error: {e}")
            return platform_name, {"error": str(e)}

    async def scrape_async(self, scrape_request):
        """
        Async method to scrape data from all platforms concurrently
        """
        print(f"🚀 Starting async parallel scrape for: {scrape_request}")
        start_time = time.time()

        # Create tasks for all platforms
        tasks = [
            self._scrape_platform_async(platform, scraper, scrape_request)
            for platform, scraper in self.scrapers.items()
        ]

        # Wait for all tasks to complete
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        results = {}
        for result in results_list:
            if isinstance(result, Exception):
                print(f"Exception occurred: {result}")
                continue
            platform_name, platform_result = result
            results[platform_name] = platform_result

        total_time = time.time() - start_time
        total_restaurants = sum(len(result) if isinstance(
            result, list) else 0 for result in results.values())
        print(
            f"🎉 All platforms completed in {total_time:.2f}s - Total restaurants: {total_restaurants}")

        return results

    def scrape(self, scrape_request):
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, create a new task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, self.scrape_async(scrape_request))
                    return future.result()
            else:
                return asyncio.run(self.scrape_async(scrape_request))
        except RuntimeError:
            # No event loop exists, create one
            return asyncio.run(self.scrape_async(scrape_request))