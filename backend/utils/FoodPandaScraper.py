import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from .BaseScraper import BaseScraper  
from models.Restaurant import Restaurant

class FoodPandaScraper(BaseScraper):
    def __init__(self):
        self.base_url = "https://www.foodpanda.com.bd/restaurants/new"

    def scrape(self, lat, lng, text, filters=None):
        """Scrape FoodPanda for restaurants near the given coordinates"""
        url = f"{self.base_url}?lng={lng}&lat={lat}&vertical=restaurants"
        print(f"[DEBUG] Starting to scrape URL: {url}")

        try:
            options = webdriver.ChromeOptions()
            # options.add_argument("--headless")  
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--user-agent=Mozilla/5.0...")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            print("[DEBUG] Starting Chrome browser...")
            driver = webdriver.Chrome(options=options)
            
            print(f"[DEBUG] Loading URL: {url}")
            driver.get(url)
            
            # Wait for the main container to load
            print("[DEBUG] Waiting for restaurant list to load...")
            wait = WebDriverWait(driver, 20)
            vendor_list = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "vendor-list-revamp"))
            )
            
            # Let the dynamic content load fully
            time.sleep(5)
            
            # Save screenshot for debugging
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug")
            os.makedirs(debug_dir, exist_ok=True)
            screenshot_path = os.path.join(debug_dir, "foodpanda_screenshot.png")
            driver.save_screenshot(screenshot_path)
            print(f"[DEBUG] Screenshot saved to {screenshot_path}")

            # Get page source after content is loaded
            page_source = driver.page_source
            driver.quit()

            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Try multiple selector patterns to find restaurant elements
            restaurant_elements = []
            selectors = [
                'ul.vendor-list-revamp > li',
                'li.vendor-tile-new-1',
                'div[data-testid="vendor-tile-new"]',
                'div[class*="vendor-tile"]'
            ]
            
            for selector in selectors:
                restaurant_elements = soup.select(selector)
                if restaurant_elements:
                    print(f"[DEBUG] Found {len(restaurant_elements)} restaurants using selector: {selector}")
                    break
                    
            if not restaurant_elements:
                print("[DEBUG] No restaurant elements found with any selector")
                return []

            restaurants = []
            for idx, restaurant_elem in enumerate(restaurant_elements):
                try:
                    # Link and URL
                    link = restaurant_elem.find('a', {'data-testid': lambda x: x and x.startswith('vendor-tile')}) or \
                        restaurant_elem.find('a', href=True)
                    restaurant_url = link.get('href') if link else None
                    if restaurant_url and not restaurant_url.startswith('http'):
                        restaurant_url = f"https://www.foodpanda.com.bd{restaurant_url}"

                    # Name
                    name_elem = restaurant_elem.select_one('[class*="vendor-name"], [class*="name"]') or \
                            restaurant_elem.find('h2')
                    name = name_elem.text.strip() if name_elem else "Unknown Restaurant"

                    offers = []
                    try:
                        offer_selectors = [
                            # Primary offer tags (like "10% off Tk. 300")
                            'span[class*="bds-c-tag__label"]:contains("off")',
                            'div[class*="revamped-primary-tag"]',
                            'span[data-testid="DISCOUNT"]',
                            'div[id*="revamped-primary-tag"]',
                            # Secondary offer tags
                            'span[class*="promoted-tag"]',
                            'div[class*="bds-c-tag"][class*="sponsored"]',
                            # Generic offer containers
                            '[class*="offer"]',
                            '[class*="discount"]',
                            '[class*="promo"]'
                        ]

                        for selector in offer_selectors:
                            offer_elements = restaurant_elem.select(selector)
                            for offer_elem in offer_elements:
                                offer_text = offer_elem.get_text(strip=True)

                                # Filter valid offers
                                if (offer_text and
                                    len(offer_text) > 2 and
                                    any(keyword in offer_text.lower() for keyword in ['off', '%', 'tk', 'free', 'discount', 'buy', 'get', 'deal']) and
                                        offer_text not in offers):
                                    offers.append(offer_text)
                                    print(f"[DEBUG] Found offer: {offer_text}")
                        
                        data_offers = restaurant_elem.find_all(
                            attrs={"data-testid": lambda x: x and "tag" in x.lower()})
                        for data_offer in data_offers:
                            offer_text = data_offer.get_text(strip=True)
                            if (offer_text and
                                any(keyword in offer_text.lower() for keyword in ['off', '%', 'tk', 'free', 'discount']) and
                                    offer_text not in offers):
                                offers.append(offer_text)
                    except Exception as e:
                        print(f"[DEBUG] Error extracting offers: {str(e)}")

                    # Rating and review count
                    try:
                        import re
                        # Get the rating
                        rating_elem = restaurant_elem.select_one('[class*="bds-c-rating__label-primary"]')
                        rating = rating_elem.text.strip() if rating_elem else "0"
                        
                        # Get the number of reviews
                        reviews_count = "0"

                        reviews_elem = restaurant_elem.select_one(
                            '[class*="bds-c-rating__label-secondary"]')
                        if reviews_elem and reviews_elem.text:
                            reviews_text = reviews_elem.text.strip()
                            print(f"[DEBUG] Found reviews element text: '{reviews_text}'")

                            # Extract number from parentheses like "(500+)" or "(50)"
                            reviews_match = re.search(r'\((\d+\+?)\)', reviews_text)
                            if reviews_match:
                                reviews_count = reviews_match.group(1)
                                print(f"[DEBUG] Extracted reviews count: {reviews_count}")
                            
                        # Format the rating with reviews count
                        if rating and rating != "0":
                            if reviews_count and reviews_count != "0":
                                final_rating = f"{rating}({reviews_count})"
                            else:
                                final_rating = rating
                        else:
                            final_rating = "No rating"

                        print(f"[DEBUG] Final rating: {final_rating}")
                    except Exception as e:
                        print(f"[DEBUG] Error extracting rating: {str(e)}")
                        rating = "No rating"


                    # Additional details
                    cuisine_type = "Not specified"
                    delivery_time = "Unknown"
                    delivery_fee = "Unknown"

                    try:
                            vendor_info_elements = restaurant_elem.find_all(
                                "div", class_=lambda x: x and "vendor-info-row" in x)

                            if not vendor_info_elements:
                                vendor_info_elements = restaurant_elem.find_all(
                                    "div", class_="vendor-info-row")

                            print(
                                f"[DEBUG] Found {len(vendor_info_elements)} vendor-info-row elements")

                            import re
                            for info_elem in vendor_info_elements:
                                # Get all child elements to process individually
                                child_elements = info_elem.find_all(
                                    ['span', 'div'], recursive=True)

                                for child in child_elements:
                                    child_text = child.get_text(strip=True)

                                    # Skip empty or very short text
                                    if not child_text or len(child_text) < 2:
                                        continue

                                    print(
                                        f"[DEBUG] Processing child text: '{child_text}'")

                                    if any(keyword in child_text.lower() for keyword in ['min']) and delivery_time == "Unknown":
                                        time_match = re.search(
                                            r'(\d+(?:-\d+)?\s*min)', child_text, re.IGNORECASE)
                                        if time_match:
                                            delivery_time = time_match.group(1)
                                            print(
                                                f"[DEBUG] Extracted delivery time: {delivery_time}")

                                    elif any(keyword in child_text for keyword in ['Tk', '৳']) and delivery_fee == "Unknown":
                                        fee_match = re.search(
                                            r'((?:Tk|৳)\s*\d+)', child_text)
                                        if fee_match:
                                            delivery_fee = fee_match.group(1)
                                            print(
                                                f"[DEBUG] Extracted delivery fee: {delivery_fee}")

                                    elif any(keyword in child_text for keyword in ['Cuisines', 'cuisine']) and cuisine_type == "Not specified":
                                        # Extract cuisine type from text
                                        if 'Cuisines' in child_text or 'cuisine' in child_text:
                                            # Remove the keyword part and strip whitespace
                                            cuisine_type = child_text.replace(
                                                'Cuisines', '').replace('cuisine', '').strip()
                                            print(
                                                f"[DEBUG] Extracted cuisine type: {cuisine_type}")


                            print(
                                f"[DEBUG] Final extracted - Time: '{delivery_time}', Fee: '{delivery_fee}', Cuisine: '{cuisine_type}'")

                    except Exception as e:
                            print(
                                f"[DEBUG] Error extracting vendor info: {str(e)}")
                            import traceback
                            traceback.print_exc()

                    # Image
                    try:
                        # First try to find the specific revamped image element
                        img_elem = restaurant_elem.select_one('img[data-testid="vendor-tile-revamped-image-actual"]')
                        
                        # If not found, try the image inside the vendor-image-container
                        if not img_elem:
                            container = restaurant_elem.select_one('div[class*="vendor-image-container"]')
                            if container:
                                img_elem = container.find('img')
                        
                        # If still not found, try any image
                        if not img_elem:
                            img_elem = restaurant_elem.find('img')
                            
                        # Get the source URL
                        image_url = img_elem.get('src') if img_elem else "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg"
                        
                        # Sometimes src might be empty but data-src has the URL
                        if not image_url or image_url == "":
                            image_url = img_elem.get('data-src') if img_elem else "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg"
                            
                        print(f"[DEBUG] Found image URL: {image_url}")
                    except Exception as e:
                        print(f"[DEBUG] Error extracting image: {str(e)}")
                        image_url = "https://micro-assets.foodora.com/img/logo-placeholder-fp.svg"

                    restaurant = Restaurant(
                        name=name,
                        cuisine_type=cuisine_type,
                        rating=final_rating,
                        delivery_time=delivery_time,
                        delivery_fee=delivery_fee,
                        platform="FoodPanda",
                        image_url=image_url,
                        url=restaurant_url,
                        offers=offers
                    )
                    
                    restaurants.append(restaurant)
                    
                except Exception as e:
                    print(f"[DEBUG] Error extracting restaurant #{idx+1} data: {str(e)}")

            print(f"[DEBUG] Successfully extracted {len(restaurants)} restaurants")
            return restaurants

        except Exception as e:
            print(f"[DEBUG] Error scraping FoodPanda: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []