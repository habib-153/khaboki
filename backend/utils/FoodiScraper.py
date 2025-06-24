from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests

from .BaseScraper import BaseScraper
from models.Restaurant import Restaurant


class FoodiScraper(BaseScraper):
    def __init__(self):
        self.base_url = "https://foodibd.com"

    def scrape(self, lat, lng, filters=None):
        """
        Scrape restaurants from foodi.bd using Selenium
        """
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1600,980")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            # Start with homepage to set location first
            print("[DEBUG] Opening foodi.bd homepage...")
            driver.get("https://foodibd.com")

            # Wait for page to load
            wait = WebDriverWait(driver, 20)
            time.sleep(3)

            # Find the location input field on homepage
            print("[DEBUG] Looking for location input field...")
            location_input = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input.p-inputtext"))
            )

            # Clear the existing value and set new location
            location_input.clear()
            time.sleep(1)

            # Use a simple, recognizable Dhaka location
            location_text = "124/1, Matikata, Dhaka Cantonment, Dhaka, Bangladesh"
            print(f"[DEBUG] Setting location: {location_text}")
            location_input.send_keys(location_text)
            time.sleep(2)

            # Find and click the "Find Food" button
            print("[DEBUG] Looking for Find Food button...")
            find_food_button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Find Food')]"))
            )

            print("[DEBUG] Clicking Find Food button...")
            find_food_button.click()

            # Now handle the modal that opens
            print("[DEBUG] Waiting for modal to appear...")
            time.sleep(3)

            # Look for the modal and handle it
            try:
                # Wait for modal to be visible
                modal = wait.until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, "[role='dialog']"))
                )
                print("[DEBUG] Modal found and visible")

                # Find the location input in the modal
                print("[DEBUG] Looking for location input in modal...")
                modal_location_input = wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "[role='dialog'] input"))
                )

                # Clear the modal input and set our location
                modal_location_input.clear()
                time.sleep(1)
                modal_location_input.send_keys("Matikata")
                print("[DEBUG] Set location in modal input")
                time.sleep(3)  # Wait for dropdown suggestions to appear

                # Wait for and select from dropdown suggestions
                print("[DEBUG] Looking for location dropdown suggestions...")
                suggestion_selected = False

                try:
                    # Try different selectors for suggestions
                    suggestion_selectors = [
                        "//div[contains(@class, 'p-autocomplete-items')]//li",
                        "//div[contains(text(), 'Matikata')]",
                        "//li[contains(text(), 'Matikata')]",
                        "//*[contains(text(), 'Matikata') and contains(text(), 'Bangladesh')]",
                        "//*[contains(text(), 'Matikata') and contains(text(), 'Dhaka')]"
                    ]

                    for selector in suggestion_selectors:
                        try:
                            suggestions = WebDriverWait(driver, 5).until(
                                EC.presence_of_all_elements_located((By.XPATH, selector))
                            )

                            if suggestions:
                                print(
                                    f"[DEBUG] Found {len(suggestions)} suggestions with selector: {selector}")

                                # Try to find the best suggestion
                                for i, suggestion in enumerate(suggestions[:5]):
                                    suggestion_text = suggestion.text.strip()
                                    print(f"[DEBUG] Suggestion {i+1}: '{suggestion_text}'")

                                    # Select suggestion that contains both "Matikata" and "Dhaka"
                                    if ("matikata" in suggestion_text.lower() and
                                        "dhaka" in suggestion_text.lower() and
                                            len(suggestion_text) > 10):

                                        print(
                                            f"[DEBUG] Selecting suggestion: {suggestion_text}")
                                        # Use JavaScript click to ensure it works
                                        driver.execute_script(
                                            "arguments[0].click();", suggestion)
                                        suggestion_selected = True
                                        time.sleep(2)
                                        break

                                # If we found suggestions but no perfect match, select the first one
                                if not suggestion_selected and suggestions:
                                    print(
                                        f"[DEBUG] No perfect match, selecting first suggestion: {suggestions[0].text}")
                                    driver.execute_script(
                                        "arguments[0].click();", suggestions[0])
                                    suggestion_selected = True
                                    time.sleep(2)

                                if suggestion_selected:
                                    break

                        except TimeoutException:
                            continue

                except Exception as e:
                    print(f"[DEBUG] Error finding suggestions: {e}")

                # If no suggestion was selected, try manual approach
                if not suggestion_selected:
                    print("[DEBUG] No suggestions found or selected. Trying manual approach...")

                    # Look for any clickable elements that might be suggestions
                    try:
                        all_suggestions = driver.find_elements(
                            By.XPATH, "//*[contains(text(), 'Matikata')]")
                        print(
                            f"[DEBUG] Found {len(all_suggestions)} elements containing 'Matikata'")

                        for suggestion in all_suggestions:
                            suggestion_text = suggestion.text.strip()
                            print(f"[DEBUG] Checking element: '{suggestion_text}'")

                            # Check if this looks like a location suggestion
                            if (len(suggestion_text) > 10 and
                                "matikata" in suggestion_text.lower() and
                                    ("dhaka" in suggestion_text.lower() or "bangladesh" in suggestion_text.lower())):

                                try:
                                    # Try to click it
                                    driver.execute_script(
                                        "arguments[0].click();", suggestion)
                                    print(
                                        f"[DEBUG] Successfully clicked suggestion: {suggestion_text}")
                                    suggestion_selected = True
                                    time.sleep(2)
                                    break
                                except Exception as click_error:
                                    print(
                                        f"[DEBUG] Could not click suggestion: {click_error}")

                    except Exception as manual_error:
                        print(
                            f"[DEBUG] Manual suggestion selection failed: {manual_error}")

                # Only proceed if a suggestion was selected
                if suggestion_selected:
                    print("[DEBUG] Location suggestion selected, proceeding to submit...")

                    # Now click the "Submit Location" button
                    print("[DEBUG] Looking for Submit Location button in modal...")
                    submit_button = wait.until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//button[contains(text(), 'Submit Location')]"))
                    )

                    print("[DEBUG] Clicking Submit Location button...")
                    submit_button.click()

                    # Wait for modal to close and navigation to happen
                    print("[DEBUG] Waiting for modal to close and navigation...")
                    time.sleep(8)

                    # Wait for modal to disappear (fixed timeout parameter)
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.invisibility_of_element_located(
                                (By.CSS_SELECTOR, "[role='dialog']"))
                        )
                        print("[DEBUG] Modal closed successfully")
                    except TimeoutException:
                        print("[DEBUG] Modal may still be visible or took longer to close")
                else:
                    print("[DEBUG] No suggestion was selected. Modal will likely stay open or close without navigation.")
                    # Try to close modal by clicking X button
                    try:
                        close_button = driver.find_element(
                            By.XPATH, "//button[@aria-label='Close'] | //*[contains(@class, 'close')]")
                        close_button.click()
                        print("[DEBUG] Closed modal manually")
                        time.sleep(2)
                    except:
                        print("[DEBUG] Could not find close button")


            except TimeoutException:
                print("[DEBUG] Could not find or interact with modal")

            # Wait additional time for navigation
            time.sleep(5)

            # Check current URL after modal interaction
            current_url = driver.current_url
            print(f"[DEBUG] Current URL after modal interaction: {current_url}")

            # Check if we navigated to restaurants page
            if "restaurants" in current_url or "delivery" in current_url or current_url != "https://foodibd.com/":
                print("[DEBUG] Successfully navigated from homepage!")
            else:
                print("[DEBUG] Still on homepage, trying direct navigation...")
                # If still on homepage, try direct navigation
                driver.get("https://foodibd.com/restaurants?type=delivery")
                time.sleep(5)
                current_url = driver.current_url
                print(f"[DEBUG] URL after direct navigation: {current_url}")


            print("[DEBUG] Looking for restaurant content...")
            time.sleep(5)


            restaurant_elements = []

            # Target only actual restaurant cards, not filter elements
            restaurant_xpaths = [
                # Target restaurant cards specifically (exclude filters)
                "//div[contains(@class, 'col-12') and contains(@class, 'sm:col-6') and contains(@class, 'md:col-6') and contains(@class, 'lg:col-4')]//a[contains(@href, '/restaurant/')]",
                # Alternative: restaurant item cards
                "//div[contains(@class, 'restaurant-item-card')]//a[contains(@href, '/restaurant/')]",
                # Direct restaurant links in grid
                "//div[contains(@class, 'grid')]//a[contains(@href, '/restaurant/')]",
            ]

            for xpath in restaurant_xpaths:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    print(
                        f"[DEBUG] Found {len(elements)} restaurant links using XPath: {xpath}")
                    restaurant_elements = elements
                    break

            # If no restaurant links found, try getting restaurant cards directly
            if not restaurant_elements:
                print("[DEBUG] No restaurant links found, trying restaurant card containers...")
                # Target the actual restaurant card containers
                card_xpath = "//div[contains(@class, 'col-12') and contains(@class, 'sm:col-6') and contains(@class, 'md:col-6') and contains(@class, 'lg:col-4')]//div[contains(@class, 'restaurant-item-card')]"
                restaurant_elements = driver.find_elements(By.XPATH, card_xpath)
                print(f"[DEBUG] Found {len(restaurant_elements)} restaurant cards")

            # Extract restaurant data with better parsing
            restaurants = []

            for i, element in enumerate(restaurant_elements[:20]):
                try:
                    print(f"[DEBUG] Processing restaurant {i+1}...")

                    # Extract restaurant name - look for h6 within the card
                    name = "Unknown Restaurant"
                    try:
                        # Look for h6 tag within this specific restaurant card
                        name_elem = element.find_element(By.XPATH, ".//h6")
                        if name_elem and name_elem.text.strip():
                            name = name_elem.text.strip()
                            print(f"[DEBUG] Found name: {name}")

                        # Skip if this is a filter element
                        if name.lower() in ['filters', 'sort by', 'price range', 'delivery time'] or 'filter' in name.lower():
                            print(f"[DEBUG] Skipping filter element: {name}")
                            continue

                    except:
                        print("[DEBUG] Could not find restaurant name")
                        continue

                    # Extract restaurant URL - look for the main link
                    url = "https://foodibd.com"
                    try:
                        if element.tag_name == 'a':
                            # Element itself is a link
                            href = element.get_attribute("href")
                            if href and href.startswith("http"):
                                url = href
                        else:
                            # Look for link within element
                            link_elem = element.find_element(By.XPATH, ".//a[@href]")
                            href = link_elem.get_attribute("href")
                            if href and href.startswith("http"):
                                url = href
                    except:
                        pass

                    # Extract image URL - look for img within the card
                    image_url = "https://via.placeholder.com/300x200?text=No+Image"
                    try:
                        img_elem = element.find_element(By.XPATH, ".//img")
                        src = img_elem.get_attribute("src")
                        if src and "http" in src and "delivery-icon" not in src:
                            image_url = src
                    except:
                        pass

                    # Extract rating - look for rating elements
                    rating = "No rating"
                    try:
                        # Look for rating in various possible structures
                        rating_selectors = [
                            ".//div[contains(@class, 'p-rating')]//span",
                            ".//span[contains(text(), '.') and string-length(text()) < 5]",
                            ".//*[contains(@class, 'rating')]",
                            ".//div[contains(@class, 'flex')]//span[contains(text(), '.')]"
                        ]

                        for rating_selector in rating_selectors:
                            try:
                                rating_elem = element.find_element(
                                    By.XPATH, rating_selector)
                                rating_text = rating_elem.text.strip()
                                if rating_text and ('.' in rating_text or '★' in rating_text):
                                    # Check if it looks like a rating (number with decimal)
                                    import re
                                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                                    if rating_match:
                                        rating_num = float(rating_match.group(1))
                                        if 0 <= rating_num <= 5:  # Valid rating range
                                            rating = f"{rating_num} ★"
                                            break
                            except:
                                continue
                    except:
                        pass

                    # Extract delivery time - look for min text
                    delivery_time = "Unknown"
                    try:
                        # Look for delivery time in various structures
                        time_elem = element.find_element(
                            By.XPATH, ".//*[contains(text(), 'min')]")
                        time_text = time_elem.text.strip()
                        if 'min' in time_text.lower():
                            # Extract just the time part
                            import re
                            time_match = re.search(
                                r'(\d+)\s*min', time_text, re.IGNORECASE)
                            if time_match:
                                delivery_time = f"{time_match.group(1)} min"
                            else:
                                delivery_time = time_text
                    except:
                        pass

                    # Extract delivery fee - look for currency symbols
                    delivery_fee = "Unknown"
                    try:
                        # Look for delivery fee
                        fee_elem = element.find_element(
                            By.XPATH, ".//*[contains(text(), '৳') or contains(text(), 'tk')]")
                        fee_text = fee_elem.text.strip()
                        if '৳' in fee_text or 'tk' in fee_text:
                            # Extract fee amount
                            import re
                            fee_match = re.search(r'(?:৳|tk)\s*(\d+)', fee_text)
                            if fee_match:
                                delivery_fee = f"৳{fee_match.group(1)}"
                            else:
                                delivery_fee = fee_text
                    except:
                        pass

                    # Extract cuisine type from text content if possible
                    cuisine_type = "Not specified"
                    try:
                        element_text = element.text.lower()
                        cuisines = ['pizza', 'burger', 'chinese', 'indian', 'bengali',
                                    'thai', 'italian', 'fast food', 'cafe', 'restaurant']
                        for cuisine in cuisines:
                            if cuisine in element_text:
                                cuisine_type = cuisine.title()
                                break
                    except:
                        pass

                    # Create restaurant object
                    restaurant = Restaurant(
                        name=name,
                        cuisine_type=cuisine_type,
                        rating=rating,
                        delivery_time=delivery_time,
                        delivery_fee=delivery_fee,
                        platform="Foodi",
                        image_url=image_url,
                        url=url
                    )

                    restaurants.append(restaurant)
                    print(
                        f"[DEBUG] Successfully extracted: {name} | {rating} | {delivery_fee} | {url}")

                except Exception as e:
                    print(f"[DEBUG] Error extracting restaurant {i+1}: {e}")
                    continue

            # If we got very few restaurants, try alternative extraction
            if len(restaurants) < 5:
                print("[DEBUG] Got very few restaurants, trying alternative extraction...")

                # Look for all h6 elements that contain restaurant names
                h6_elements = driver.find_elements(
                    By.XPATH, "//h6[string-length(text()) > 5]")

                for i, h6_elem in enumerate(h6_elements[:15]):
                    try:
                        name = h6_elem.text.strip()

                        # Skip filter elements
                        if name.lower() in ['filters', 'sort by'] or 'price range' in name.lower() or 'delivery time' in name.lower():
                            continue

                        print(f"[DEBUG] Alternative extraction {i+1}: {name}")

                        # Try to get parent container for additional info
                        try:
                            # Go up to restaurant card container
                            card_container = h6_elem.find_element(
                                By.XPATH, "./ancestor::div[contains(@class, 'col')]")

                            # Extract URL from card
                            url = "https://foodibd.com"
                            try:
                                link_elem = card_container.find_element(
                                    By.XPATH, ".//a[@href]")
                                href = link_elem.get_attribute("href")
                                if href and href.startswith("http"):
                                    url = href
                            except:
                                pass

                            # Extract image
                            image_url = "https://via.placeholder.com/300x200?text=No+Image"
                            try:
                                img_elem = card_container.find_element(By.XPATH, ".//img")
                                src = img_elem.get_attribute("src")
                                if src and "http" in src and "delivery-icon" not in src:
                                    image_url = src
                            except:
                                pass

                            # Create restaurant
                            restaurant = Restaurant(
                                name=name,
                                cuisine_type="Not specified",
                                rating="No rating",
                                delivery_time="Unknown",
                                delivery_fee="Unknown",
                                platform="Foodi",
                                image_url=image_url,
                                url=url
                            )

                            # Check if we already have this restaurant
                            if not any(r.name == name for r in restaurants):
                                restaurants.append(restaurant)
                                print(
                                    f"[DEBUG] Added alternative restaurant: {name} | {url}")

                        except Exception as container_error:
                            print(
                                f"[DEBUG] Could not get container for {name}: {container_error}")

                    except Exception as h6_error:
                        print(f"[DEBUG] Error processing h6 element {i+1}: {h6_error}")
                        continue

            print(
                f"[DEBUG] Successfully extracted {len(restaurants)} restaurants from foodi")
            return restaurants

        except Exception as e:
            print(f"[DEBUG] Error in foodi scraping: {e}")
            import traceback
            print(traceback.format_exc())
            return []

        finally:
            driver.quit()

            # Look for restaurant cards using more specific XPaths
        #     restaurant_elements = []

        #     # Try to find restaurant cards using XPath patterns
        #     restaurant_xpaths = [
        #         # Based on your provided XPath structure
        #         "//div[contains(@class, 'col')]//a[contains(@href, '/restaurant/')]",
        #         # Divs containing h6 (restaurant names)
        #         "//div[contains(@class, 'col')]//div[.//h6]",
        #         # Following the structure you mentioned
        #         "//*[@id='__next']//div[contains(@class, 'col')]//a//div",
        #         "//a[contains(@href, '/restaurant/')]//div",  # Restaurant links
        #         "//h6[parent::div]/..",  # Parent divs of h6 elements (restaurant names)
        #     ]

        #     for xpath in restaurant_xpaths:
        #         elements = driver.find_elements(By.XPATH, xpath)
        #         if elements:
        #             print(f"[DEBUG] Found {len(elements)} elements using XPath: {xpath}")
        #             # Filter elements that contain meaningful content
        #             filtered_elements = []
        #             for elem in elements:
        #                 try:
        #                     elem_text = elem.text.strip()
        #                     # Check if element has substantial content and looks like a restaurant card
        #                     if (len(elem_text) > 20 and
        #                         any(keyword in elem_text.lower() for keyword in ['min', 'tk', '৳', 'delivery']) and
        #                             not any(exclude in elem_text.lower() for exclude in ['temporarily unavailable', 'business account', 'signup'])):
        #                         filtered_elements.append(elem)
        #                 except:
        #                     continue

        #             if filtered_elements:
        #                 restaurant_elements = filtered_elements
        #                 print(
        #                     f"[DEBUG] Using {len(filtered_elements)} filtered restaurant elements")
        #                 break

        #     # If no specific restaurant cards found, try direct name extraction
        #     if not restaurant_elements:
        #         print("[DEBUG] No restaurant cards found, trying direct name extraction...")

        #         name_elements = driver.find_elements(
        #             By.XPATH, "//h6[contains(@class, '') or not(@class)]")

        #         if name_elements:
        #             print(
        #                 f"[DEBUG] Found {len(name_elements)} h6 elements (potential restaurant names)")
        #             # Get parent containers of these names
        #             restaurant_elements = []
        #             for name_elem in name_elements:
        #                 try:
        #                     # Get the restaurant card container (go up a few levels)
        #                     card_container = name_elem.find_element(
        #                         By.XPATH, "./ancestor::div[contains(@class, 'col') or contains(@class, 'card')]")
        #                     if card_container and card_container not in restaurant_elements:
        #                         restaurant_elements.append(card_container)
        #                 except:
        #                     continue

        #             print(
        #                 f"[DEBUG] Found {len(restaurant_elements)} restaurant containers from names")

        #     # Extract restaurant data with better parsing
        #     restaurants = []

        #     for i, element in enumerate(restaurant_elements[:20]):
        #         try:
        #             print(f"[DEBUG] Processing restaurant {i+1}...")

        #             name = "Unknown Restaurant"
        #             try:
        #                 name_selectors = [
        #                     "//*[@id='__next']/div[1]/main/section[2]/form/div/div/div[2]/div[2]/div[2]/div/div/div[1]/div[1]/div/a/div/div[2]/h6",
        #                 ]

        #                 for selector in name_selectors:
        #                     name_elem = element.find_element(By.XPATH, selector)
        #                     if name_elem and name_elem.text.strip():
        #                         name = name_elem.text.strip()
        #                         print(f"[DEBUG] Found name: {name}")
        #                         break
        #             except:
        #                 element_text = element.text.strip()
        #                 lines = element_text.split('\n')
        #                 for line in lines:
        #                     line = line.strip()
        #                     if (line and len(line) > 3 and len(line) < 80 and
        #                             not any(skip in line.lower() for skip in ['temporarily unavailable', 'open at', 'closed', 'delivery', 'min', 'tk', '৳'])):
        #                         name = line
        #                         break

        #             # Skip if name is still generic
        #             if name in ["Unknown Restaurant", "Temporarily unavailable"]:
        #                 continue

        #             # Extract rating
        #             rating = "No rating"
        #             try:
        #                 rating_elem = element.find_element(
        #                     By.XPATH, "//*[@id='__next']/div[1]/main/section[2]/form/div/div/div[2]/div[2]/div[2]/div/div/div[1]/div[1]/div/a/div/div[2]/div/div[1]/div[2]/span[1]")
        #                 if rating_elem:
        #                     rating_text = rating_elem.text.strip()
        #                     if rating_text and ('★' in rating_text or '.' in rating_text):
        #                         rating = rating_text
        #             except:
        #                 # Try regex on full text
        #                 import re
        #                 element_text = element.text
        #                 rating_match = re.search(
        #                     r'(\d+\.?\d*)\s*(?:★|star)', element_text, re.IGNORECASE)
        #                 if rating_match:
        #                     rating = f"{rating_match.group(1)} ★"

        #             # Extract delivery time
        #             delivery_time = "Unknown"
        #             try:
        #                 time_elem = element.find_element(
        #                     By.XPATH, ".//*[contains(text(), 'min')]")
        #                 if time_elem:
        #                     time_text = time_elem.text.strip()
        #                     if 'min' in time_text.lower():
        #                         delivery_time = time_text
        #             except:
        #                 # Try regex
        #                 import re
        #                 element_text = element.text
        #                 time_match = re.search(r'(\d+)\s*min', element_text, re.IGNORECASE)
        #                 if time_match:
        #                     delivery_time = f"{time_match.group(1)} min"

        #             # Extract delivery fee
        #             delivery_fee = "Unknown"
        #             try:
        #                 fee_elem = element.find_element(
        #                     By.XPATH, ".//*[contains(text(), 'Tk') or contains(text(), '৳')]")
        #                 if fee_elem:
        #                     fee_text = fee_elem.text.strip()
        #                     if '৳' in fee_text or 'Tk' in fee_text:
        #                         delivery_fee = fee_text
        #             except:
        #                 # Try regex
        #                 import re
        #                 element_text = element.text
        #                 fee_match = re.search(r'(?:Tk|৳)\s*(\d+)', element_text)
        #                 if fee_match:
        #                     delivery_fee = f"৳{fee_match.group(1)}"

        #             # Extract image URL
        #             image_url = "https://via.placeholder.com/300x200?text=No+Image"
        #             try:
        #                 img_elem = element.find_element(
        #                     By.XPATH, "//*[@id='__next']/div[1]/main/section[2]/form/div/div/div[2]/div[2]/div[2]/div/div/div[1]/div[1]/div/a/div/div[1]/div[1]/img")
        #                 src = img_elem.get_attribute("src")
        #                 if src and "http" in src:
        #                     image_url = src
        #             except:
        #                 pass

        #             # Extract restaurant URL
        #             url = "https://foodibd.com"
        #             try:
        #                 link_elem = element.find_element(
        #                     By.XPATH, "//*[@id='__next']/div[1]/main/section[2]/form/div/div/div[2]/div[2]/div[2]/div/div/div[1]/div[1]/div/a")
        #                 href = link_elem.get_attribute("href")
        #                 if href and href.startswith("http"):
        #                     url = href
        #                 else:
        #                     url = f'https://foodibd.com{href}'
        #             except:
        #                 pass

        #             # Create restaurant object
        #             restaurant = Restaurant(
        #                 name=name,
        #                 cuisine_type="Not specified",
        #                 rating=rating,
        #                 delivery_time=delivery_time,
        #                 delivery_fee=delivery_fee,
        #                 platform="Foodi",
        #                 image_url=image_url,
        #                 url=url
        #             )

        #             restaurants.append(restaurant)
        #             print(
        #                 f"[DEBUG] Successfully extracted: {name} | {rating} | {delivery_time}")

        #         except Exception as e:
        #             print(f"[DEBUG] Error extracting restaurant {i+1}: {e}")
        #             continue

        #     # If still no restaurants found, try alternative approach with direct XPath
        #     if not restaurants:
        #         print("[DEBUG] No restaurants extracted, trying direct XPath approach...")

        #         try:
        #             # Use the exact XPath pattern you provided
        #             direct_name_elements = driver.find_elements(
        #                 By.XPATH, "//*[@id='__next']//h6")

        #             print(f"[DEBUG] Found {len(direct_name_elements)} h6 elements")

        #             for i, name_elem in enumerate(direct_name_elements[:20]):
        #                 try:
        #                     name = name_elem.text.strip()
        #                     if name and len(name) > 3 and "temporarily unavailable" not in name.lower():
        #                         print(f"[DEBUG] Direct extraction {i+1}: {name}")

        #                         # Try to get the parent container for additional info
        #                         try:
        #                             parent_container = name_elem.find_element(
        #                                 By.XPATH, "./ancestor::div[3]")
        #                             container_text = parent_container.text

        #                             # Extract additional info from container
        #                             delivery_time = "Unknown"
        #                             rating = "No rating"

        #                             import re
        #                             time_match = re.search(
        #                                 r'(\d+)\s*min', container_text, re.IGNORECASE)
        #                             if time_match:
        #                                 delivery_time = f"{time_match.group(1)} min"

        #                             rating_match = re.search(
        #                                 r'(\d+\.?\d*)\s*(?:★|star)', container_text, re.IGNORECASE)
        #                             if rating_match:
        #                                 rating = f"{rating_match.group(1)} ★"

        #                         except:
        #                             container_text = name
        #                             delivery_time = "Unknown"
        #                             rating = "No rating"

        #                         restaurant = Restaurant(
        #                             name=name,
        #                             cuisine_type="Not specified",
        #                             rating=rating,
        #                             delivery_time=delivery_time,
        #                             delivery_fee="Unknown",
        #                             platform="Foodi",
        #                             image_url="https://via.placeholder.com/300x200?text=No+Image",
        #                             url="https://foodibd.com"
        #                         )

        #                         restaurants.append(restaurant)

        #                 except Exception as e:
        #                     print(f"[DEBUG] Error in direct extraction {i+1}: {e}")
        #                     continue

        #         except Exception as e:
        #             print(f"[DEBUG] Error in direct XPath approach: {e}")

        #     print(
        #         f"[DEBUG] Successfully extracted {len(restaurants)} restaurants from foodi")

        #     # Keep browser open for debugging
        #     print("[DEBUG] Keeping browser open for 10 seconds...")
        #     time.sleep(10)

        #     return restaurants

        # except Exception as e:
        #     print(f"[DEBUG] Error in foodi scraping: {e}")
        #     import traceback
        #     print(traceback.format_exc())
        #     return []

        # finally:
        #     driver.quit()

    def reverse_geocode_address(self, lat, lng):
        """
        Convert coordinates to address using OpenStreetMap Nominatim API
        """
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&zoom=18&addressdetails=1"
            response = requests.get(url, headers={'User-Agent': 'KhaboKi App'})
            data = response.json()

            if 'display_name' in data:
                return data['display_name']

        except Exception as e:
            print(f"[DEBUG] Geocoding error: {e}")

        return "Dhanmondi, Dhaka"
