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

    def scrape(self, lat, lng, filters=None):
        """Scrape FoodPanda for restaurants near the given coordinates"""
        url = f"{self.base_url}?lng={lng}&lat={lat}&vertical=restaurants"
        print(f"[DEBUG] Starting to scrape URL: {url}")

        try:
            options = webdriver.ChromeOptions()
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

                    # Rating and review count
                    try:
                        # Get the rating
                        rating_elem = restaurant_elem.select_one('[class*="bds-c-rating__label-primary"]')
                        rating = rating_elem.text.strip() if rating_elem else "0"
                        
                        # Get the number of reviews
                        reviews_elem = restaurant_elem.select_one('[class*="bds-c-rating__label-secondary"]')
                        if reviews_elem and reviews_elem.text:
                            # Extract just the number from inside the parentheses, like (12)
                            import re
                            reviews_match = re.search(r'\((\d+)\)', reviews_elem.text)
                            reviews_count = reviews_match.group(1) if reviews_match else "0"
                        else:
                            reviews_count = "0"
                            
                        # Format the rating with reviews count
                        if rating != "0" and reviews_count != "0":
                            rating = f"{rating}({reviews_count})"
                        elif rating != "0":
                            rating = f"{rating}(0)"
                        else:
                            rating = "No rating"
                            
                        print(f"[DEBUG] Extracted rating: {rating}")
                    except Exception as e:
                        print(f"[DEBUG] Error extracting rating: {str(e)}")
                        rating = "No rating"

                    # Additional details
                    info_spans = restaurant_elem.find_all(['span', 'div'], class_=['info', 'details'])
                    cuisine_type = "Not specified"
                    delivery_time = "Unknown"
                    delivery_fee = "Unknown"

                    for span in info_spans:
                        text = span.text.strip()
                        if any(cuisine in text.lower() for cuisine in ['cuisine', 'food type']):
                            cuisine_type = text
                        elif any(time in text.lower() for time in ['min', 'delivery time']):
                            delivery_time = text
                        elif any(fee in text.lower() for fee in ['tk', 'fee', 'delivery']):
                            delivery_fee = text

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
                        rating=rating,
                        delivery_time=delivery_time,
                        delivery_fee=delivery_fee,
                        platform="FoodPanda",
                        image_url=image_url,
                        url=restaurant_url
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