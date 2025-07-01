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
import re
from .BaseScraper import BaseScraper
from models.Restaurant import Restaurant


class FoodiScraper(BaseScraper):
    def __init__(self):
        self.base_url = "https://foodibd.com"

    def scrape(self, lat, lng, text, filters=None):
        """
        Scrape restaurants from foodi.bd using Selenium
        """
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1200,980")
        # chrome_options.add_argument("headless")  

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

            location_text = text
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
                modal_location_input.send_keys(location_text)
                print("[DEBUG] Set location in modal input")
                time.sleep(3)  # Wait for dropdown suggestions to appear

                
                # Wait for and select from dropdown suggestions
                print("[DEBUG] Looking for location dropdown suggestions...")
                print("[DEBUG] Looking for location dropdown suggestions...")
                suggestion_selected = False

                try:
                    import re
                    location_parts = location_text.split(',')

                    # Get all location parts and clean them
                    all_location_parts = []
                    for part in location_parts:
                        clean_part = part.strip()
                        if clean_part:
                            all_location_parts.append(clean_part)
                            # Also add cleaned version (remove common words)
                            cleaned = re.sub(
                                r'\b(road|rd|street)\b', '', clean_part, flags=re.IGNORECASE).strip()
                            if cleaned and cleaned != clean_part:
                                all_location_parts.append(cleaned)

                    print(
                        f"[DEBUG] All location parts to search: {all_location_parts}")

                    # Wait for suggestions to appear
                    time.sleep(5)

                    # Build dynamic selectors based on all location parts
                    suggestion_selectors = [
                        # Standard autocomplete dropdowns
                        "//div[contains(@class, 'p-autocomplete-items')]//li",
                        "//div[contains(@class, 'p-autocomplete-panel')]//li",
                        "//ul[contains(@class, 'p-autocomplete-items')]//li",

                        # Generic list items that might contain locations
                        "//li[contains(text(), 'ঢাকা') or contains(text(), 'Dhaka')]",
                        "//div[contains(text(), 'ঢাকা') or contains(text(), 'Dhaka')]",
                        f"//*[contains(text(), {text}) or contains(text(), '{location_text}')]",
                    ]

                    # Add dynamic selectors for each location part
                    for part in all_location_parts:
                        if len(part) > 2:  # Only add meaningful parts
                            # Escape single quotes in the part for XPath
                            escaped_part = part.replace("'", "\\'")
                            suggestion_selectors.append(
                                f"//*[contains(text(), '{escaped_part}')]")

                    for selector in suggestion_selectors:
                        try:
                            print(f"[DEBUG] Trying selector: {selector}")
                            suggestions = WebDriverWait(driver, 3).until(
                                EC.presence_of_all_elements_located(
                                    (By.XPATH, selector))
                            )

                            if suggestions:
                                print(
                                    f"[DEBUG] Found {len(suggestions)} suggestions with selector: {selector}")

                                # Log all suggestions for debugging
                                for i, suggestion in enumerate(suggestions[:10]):
                                    try:
                                        suggestion_text = suggestion.text.strip()
                                        print(
                                            f"[DEBUG] Suggestion {i+1}: '{suggestion_text}'")
                                    except:
                                        print(
                                            f"[DEBUG] Suggestion {i+1}: Could not get text")

                                # Enhanced matching logic using all location parts
                                for i, suggestion in enumerate(suggestions[:10]):
                                    try:
                                        suggestion_text = suggestion.text.strip()
                                        suggestion_lower = suggestion_text.lower()

                                        # Check how many of our location parts match this suggestion
                                        part_matches = 0
                                        matched_parts = []

                                        for part in all_location_parts:
                                            part_lower = part.lower()
                                            if part_lower in suggestion_lower:
                                                part_matches += 1
                                                matched_parts.append(part)
                                                print(
                                                    f"[DEBUG] Matched part: '{part}' in suggestion")

                                        # Check for location indicators
                                        location_indicators = [
                                            'ঢাকা', 'dhaka', 'bangladesh', 'বাংলাদেশ', {text},
                                            '১২১২', '1212'
                                        ]

                                        indicator_matches = sum(1 for indicator in location_indicators
                                                                if indicator in suggestion_lower)

                                        # Enhanced matching criteria
                                        is_good_match = False

                                        # Priority matching logic:
                                        if part_matches >= 2:
                                            # If 2 or more parts of our address match
                                            is_good_match = True
                                            print(
                                                f"[DEBUG] Good match - {part_matches} parts matched: {matched_parts}")
                                        elif part_matches >= 1 and indicator_matches >= 1:
                                            # If at least 1 part matches and has location indicators
                                            is_good_match = True
                                            print(
                                                f"[DEBUG] Good match - 1 part + indicators: {matched_parts}")
                                        elif indicator_matches >= 2:
                                            # If multiple location indicators match
                                            is_good_match = True
                                            print(
                                                f"[DEBUG] Good match - multiple indicators")
                                        elif (('ঢাকা' in suggestion_lower or 'dhaka' in suggestion_lower) and
                                              len(suggestion_text) > 15):
                                            # Fallback for long Dhaka addresses
                                            is_good_match = True
                                            print(
                                                f"[DEBUG] Good match - long Dhaka address")
                                        elif ('bangladesh' in suggestion_lower or 'বাংলাদেশ' in suggestion_lower):
                                            # Any Bangladesh address
                                            is_good_match = True
                                            print(
                                                f"[DEBUG] Good match - Bangladesh address")

                                        if is_good_match:
                                            print(
                                                f"[DEBUG] Selecting good match: {suggestion_text}")
                                            print(
                                                f"[DEBUG] Match details - Parts: {part_matches}, Indicators: {indicator_matches}")
                                            try:
                                                driver.execute_script(
                                                    "arguments[0].scrollIntoView(true);", suggestion)
                                                time.sleep(1)
                                                driver.execute_script(
                                                    "arguments[0].click();", suggestion)
                                                suggestion_selected = True
                                                time.sleep(3)
                                                break
                                            except Exception as click_error:
                                                print(
                                                    f"[DEBUG] JavaScript click failed: {click_error}")
                                                try:
                                                    suggestion.click()
                                                    suggestion_selected = True
                                                    time.sleep(3)
                                                    break
                                                except Exception as regular_click_error:
                                                    print(
                                                        f"[DEBUG] Regular click also failed: {regular_click_error}")

                                    except Exception as suggestion_error:
                                        print(
                                            f"[DEBUG] Error processing suggestion {i+1}: {suggestion_error}")
                                        continue

                                # Enhanced fallback - try suggestions with any location part match
                                if not suggestion_selected and suggestions:
                                    print(
                                        "[DEBUG] Trying fallback with any part match...")
                                    for suggestion in suggestions[:5]:
                                        try:
                                            suggestion_text = suggestion.text.strip()
                                            suggestion_lower = suggestion_text.lower()

                                            # Check if any of our location parts are in this suggestion
                                            has_part_match = any(part.lower() in suggestion_lower
                                                                 for part in all_location_parts
                                                                 if len(part) > 3)

                                            if has_part_match and len(suggestion_text) > 10:
                                                print(
                                                    f"[DEBUG] Fallback match: {suggestion_text}")
                                                driver.execute_script(
                                                    "arguments[0].click();", suggestion)
                                                suggestion_selected = True
                                                time.sleep(3)
                                                break
                                        except Exception as fallback_error:
                                            print(
                                                f"[DEBUG] Fallback click failed: {fallback_error}")
                                            continue

                                if suggestion_selected:
                                    break

                        except TimeoutException:
                            print(
                                f"[DEBUG] No suggestions found with selector: {selector}")
                            continue
                        except Exception as selector_error:
                            print(
                                f"[DEBUG] Error with selector {selector}: {selector_error}")
                            continue

                    # Final fallback: try to find any clickable suggestion with location parts
                    if not suggestion_selected:
                        print("[DEBUG] Trying final broader suggestion search...")
                        try:
                            # Build XPath for all our location parts
                            xpath_conditions = []
                            xpath_conditions.append("contains(text(), 'ঢাকা')")
                            xpath_conditions.append(
                                "contains(text(), 'Dhaka')")

                            for part in all_location_parts:
                                if len(part) > 3:  # Only meaningful parts
                                    escaped_part = part.replace("'", "\\'")
                                    xpath_conditions.append(
                                        f"contains(text(), '{escaped_part}')")

                            xpath_query = f"//*[{' or '.join(xpath_conditions)}]"
                            print(f"[DEBUG] Final XPath query: {xpath_query}")

                            all_elements = driver.find_elements(
                                By.XPATH, xpath_query)
                            print(
                                f"[DEBUG] Found {len(all_elements)} elements in final search")

                            for element in all_elements[:5]:
                                try:
                                    element_text = element.text.strip()
                                    if (len(element_text) > 10 and
                                            len(element_text) < 200):

                                        # Check if this element contains any of our location parts
                                        element_lower = element_text.lower()
                                        matching_parts = [part for part in all_location_parts
                                                          if part.lower() in element_lower and len(part) > 3]

                                        if matching_parts:
                                            print(
                                                f"[DEBUG] Final attempt - trying element with parts {matching_parts}: {element_text}")
                                            driver.execute_script(
                                                "arguments[0].click();", element)
                                            suggestion_selected = True
                                            time.sleep(3)
                                            break
                                except Exception as broad_error:
                                    print(
                                        f"[DEBUG] Final attempt failed: {broad_error}")
                                    continue

                        except Exception as broad_search_error:
                            print(
                                f"[DEBUG] Final search failed: {broad_search_error}")

                    if suggestion_selected:
                        print(
                            "[DEBUG] Successfully selected a location suggestion!")
                    else:
                        print("[DEBUG] Could not select any location suggestion")

                except Exception as e:
                    print(
                        f"[DEBUG] Error in suggestion selection process: {e}")


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
                "//div[contains(@class, 'col-12') and contains(@class, 'sm:col-6') and contains(@class, 'md:col-6') and contains(@class, 'lg:col-4')]//a[contains(@href, '/restaurant/')]",
                "//div[contains(@class, 'restaurant-item-card')]//a[contains(@href, '/restaurant/')]",
                "//div[contains(@class, 'grid')]//a[contains(@href, '/restaurant/')]",
            ]

            for xpath in restaurant_xpaths:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    print(
                        f"[DEBUG] Found {len(elements)} restaurant links using XPath: {xpath}")
                    restaurant_elements = elements
                    break

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
                    try:
                        rating = "No rating"
                        reviews_count = ""
                        try:
                            rating_containers = element.find_elements(
                                By.XPATH, 
                                ".//div[@class='flex align-items-center column-gap-1' or contains(@class, 'flex align-items-center column-gap-1')]"
                            )
                            
                            if rating_containers:
                                rating_div = rating_containers[0]
                                
                                rating_spans = rating_div.find_elements(By.TAG_NAME, "span")
                                
                                if len(rating_spans) >= 1:
                                    # First span should be the rating value (4.2)
                                    rating = rating_spans[0].text.strip()
                                    print(f"[DEBUG] Found rating in first span: {rating}")
                                
                                if len(rating_spans) >= 2:
                                    # Second span should be the reviews count in parentheses
                                    reviews_text = rating_spans[1].text.strip()
                                    print(f"[DEBUG] Found reviews text: {reviews_text}")
                                    
                                    # Extract the number from parentheses
                                    if '(' in reviews_text and ')' in reviews_text:
                                        reviews_count = reviews_text.strip('()')
                                        print(f"[DEBUG] Extracted review count: {reviews_count}")
                                    else:
                                        # Direct number extraction if no parentheses
                                        digit_match = re.search(r'\d+', reviews_text)
                                        if digit_match:
                                            reviews_count = digit_match.group(0)
                                
                                # Debug the found spans
                                print(f"[DEBUG] Found {len(rating_spans)} spans in rating container")
                                for i, span in enumerate(rating_spans):
                                    print(f"[DEBUG] Span {i+1} text: '{span.text}'")
                        
                        except Exception as precise_error:
                            print(f"[DEBUG] Error in precise rating extraction: {precise_error}")
                            
                            # Fall back to direct XPath for the specific elements we see in screenshots
                            try:
                                # Try direct XPath for rating (first span with font-semibold)
                                rating_elem = element.find_element(By.XPATH, ".//span[contains(@class, 'font-semibold')]")
                                if rating_elem:
                                    rating = rating_elem.text.strip()
                                    
                                # Direct XPath for reviews count (span following font-semibold span)
                                reviews_elem = element.find_element(By.XPATH, ".//span[contains(@class, 'font-semibold')]/following-sibling::span[1]")
                                if reviews_elem:
                                    reviews_text = reviews_elem.text.strip()
                                    if '(' in reviews_text and ')' in reviews_text:
                                        reviews_count = reviews_text.strip('()')
                            
                            except Exception as xpath_error:
                                print(f"[DEBUG] Error in direct XPath approach: {xpath_error}")
                        
                        # Format the final rating
                        if rating and rating != "No rating":
                            if reviews_count:
                                final_rating = f"{rating}({reviews_count})"
                            else:
                                final_rating = rating
                        else:
                            final_rating = "No rating"
                            
                        print(f"[DEBUG] Enhanced final rating: {final_rating}")
                        
                    except Exception as general_error:
                        print(f"[DEBUG] General error in enhanced rating extraction: {general_error}")
                        final_rating = "No rating"

                    delivery_time = "Unknown"
                    try:
                        time_xpaths = [
                            ".//div[1]/div[3]/div/span",
                            ".//div/div[1]/div[3]/div/span",
                            ".//div[contains(@class, 'div-3')]//span",
                            ".//*[contains(text(), 'min')]",
                            ".//span[contains(text(), 'min')]",
                            ".//div[contains(text(), 'min')]//span",
                            ".//span[contains(text(), '-') and contains(text(), 'min')]",
                            ".//span[text()[contains(., 'min')]]"
                        ]
                        
                        for xpath in time_xpaths:
                            try:
                                time_elements = element.find_elements(By.XPATH, xpath)
                                for time_elem in time_elements:
                                    time_text = time_elem.text.strip()
                                    print(f"[DEBUG] Found time element text: '{time_text}'")
                                    
                                    if time_text and 'min' in time_text.lower():
                                        time_match = re.search(r'(\d+(?:\s*-\s*\d+)?\s*min)', time_text, re.IGNORECASE)
                                        if time_match:
                                            delivery_time = time_match.group(1)
                                            print(f"[DEBUG] Extracted delivery time: {delivery_time}")
                                            break
                                        else:
                                            delivery_time = time_text
                                            print(f"[DEBUG] Used full time text: {delivery_time}")
                                            break
                                
                                if delivery_time != "Unknown":
                                    break
                                    
                            except Exception as xpath_error:
                                print(f"[DEBUG] Error with time xpath {xpath}: {xpath_error}")
                                continue
                        
                        if delivery_time == "Unknown":
                            try:
                                all_spans = element.find_elements(By.XPATH, ".//span")
                                for span in all_spans:
                                    span_text = span.text.strip()
                                    if (span_text and 
                                        'min' in span_text.lower() and 
                                        len(span_text) < 20 and  
                                        not any(exclude in span_text.lower() for exclude in ['rating', 'review', 'cuisine', 'restaurant'])):
                                        
                                        import re
                                        time_match = re.search(r'(\d+(?:\s*-\s*\d+)?\s*min)', span_text, re.IGNORECASE)
                                        if time_match:
                                            delivery_time = time_match.group(1)
                                            print(f"[DEBUG] Found delivery time via general search: {delivery_time}")
                                            break
                                            
                            except Exception as general_error:
                                print(f"[DEBUG] Error in general time search: {general_error}")
                        
                        # Final fallback using regex on entire element text
                        if delivery_time == "Unknown":
                            try:
                                element_text = element.text
                                import re
                                time_patterns = [
                                    r'(\d+\s*-\s*\d+\s*min)', 
                                    r'(\d+\s*min)',           
                                ]
                                
                                for pattern in time_patterns:
                                    time_match = re.search(pattern, element_text, re.IGNORECASE)
                                    if time_match:
                                        delivery_time = time_match.group(1)
                                        print(f"[DEBUG] Found delivery time via regex fallback: {delivery_time}")
                                        break
                                        
                            except Exception as regex_error:
                                print(f"[DEBUG] Error in regex time extraction: {regex_error}")
                        
                    except Exception as e:
                        print(f"[DEBUG] Error extracting delivery time: {e}")

                    delivery_fee = "Unknown"
                    try:
                        # Look for delivery fee
                        fee_elem = element.find_element(
                            By.XPATH, ".//*[contains(text(), '৳') or contains(text(), 'tk')]")
                        fee_text = fee_elem.text.strip()
                        if '৳' in fee_text or 'tk' in fee_text:
                            fee_match = re.search(r'(?:৳|tk)\s*(\d+)', fee_text)
                            if fee_match:
                                delivery_fee = f"৳{fee_match.group(1)}"
                            else:
                                delivery_fee = fee_text
                    except:
                        pass

                    # Extract cuisine type from text content if possible
                    try:
                        cuisine_type = "Not specified"
                        try:
                            cuisine_xpath = ".//span[contains(@class, 'text-16') and contains(@class, 'fd-text-gray-700')]"
                            cuisine_elem = element.find_element(By.XPATH, cuisine_xpath)
                            if cuisine_elem:
                                cuisine_text = cuisine_elem.text.strip()
                                print(f"[DEBUG] Raw cuisine text: '{cuisine_text}'")

                                if cuisine_text and len(cuisine_text) > 1:
                                    # Method 1: Split by newline - the format is often "৳৳\nSweets"
                                    cuisine_parts = cuisine_text.strip().split('\n')
                                    if len(cuisine_parts) > 1:
                                        # Get the second part which is usually the cuisine type
                                        cuisine_type = cuisine_parts[-1].strip()
                                        print(
                                            f"[DEBUG] Found cuisine type after newline: {cuisine_type}")
                                    else:
                                        # Method 2: Remove price indicators (৳) from the text
                                        clean_text = re.sub(r'[৳₹$€£¥]+', '', cuisine_text).strip()

                                        # If we have text after removing price symbols, use that
                                        if clean_text:
                                            cuisine_type = clean_text
                                            print(
                                                f"[DEBUG] Found cuisine type after removing price symbols: {cuisine_type}")
                                        else:
                                            cuisine_type = cuisine_text.strip()
                        except Exception as e:
                            print(f"[DEBUG] Error getting cuisine from specific XPath: {e}")
                    except:
                        pass

                    offers = []
                    try:
                        offer_xpaths = [
                            ".//div[contains(@class, 'div-1')]//div[contains(@class, 'div-2')]//span",
                            # Alternative patterns based on your XPath structure
                            ".//div/div[1]/div[2]/div/div[2]/span",
                            ".//div/div[1]/div[2]//span",
                            # Generic offer patterns for Foodi
                            ".//*[contains(text(), 'Off') or contains(text(), 'off')]",
                            ".//*[contains(text(), 'Flat') and contains(text(), '%')]",
                            ".//*[contains(text(), 'Get') and contains(text(), 'Off')]",
                            ".//*[contains(text(), 'Free') and contains(text(), 'delivery')]",
                            ".//*[contains(text(), 'Buy') and contains(text(), 'Get')]",
                            ".//span[contains(text(), '%')]",
                            ".//span[contains(text(), 'discount')]",
                            ".//span[contains(text(), 'promo')]"
                        ]

                        for xpath in offer_xpaths:
                            try:
                                offer_elements = element.find_elements(
                                    By.XPATH, xpath)
                                for offer_elem in offer_elements:
                                    offer_text = offer_elem.text.strip()

                                    if (offer_text and
                                        len(offer_text) > 2 and
                                        len(offer_text) < 100 and
                                        any(keyword in offer_text.lower() for keyword in ['off', '%', 'free', 'discount', 'buy', 'get', 'flat', 'promo']) and
                                        not any(exclude in offer_text.lower() for exclude in ['min', 'delivery time', 'rating', 'review']) and
                                            offer_text not in offers):

                                        offers.append(offer_text)
                                        print(
                                            f"[DEBUG] Found Foodi offer: {offer_text}")
                            except:
                                continue
                        try:
                            card_text = element.text
                            import re

                            percent_offers = re.findall(
                                r'(?:Flat\s+)?(\d+%\s+[Oo]ff)', card_text, re.IGNORECASE)
                            for offer in percent_offers:
                                formatted_offer = f"Flat {offer}" if not offer.lower(
                                ).startswith('flat') else offer
                                if formatted_offer not in offers:
                                    offers.append(formatted_offer)

                            buy_get_offers = re.findall(
                                r'(Buy\s+\d+\s+Get\s+\d+[^.]*)', card_text, re.IGNORECASE)
                            for offer in buy_get_offers:
                                if offer.strip() not in offers:
                                    offers.append(offer.strip())

                            if re.search(r'free\s+delivery', card_text, re.IGNORECASE) and "Free delivery" not in offers:
                                offers.append("Free delivery")
                        except Exception as regex_error:
                            print(f"[DEBUG] Regex extraction error: {regex_error}")
                    except Exception as e:
                        print(f"[DEBUG] Error extracting Foodi offers: {e}")
                    

                    restaurant = Restaurant(
                        name=name,
                        cuisine_type=cuisine_type,
                        rating=final_rating,
                        delivery_time=delivery_time,
                        delivery_fee=delivery_fee,
                        platform="Foodi",
                        image_url=image_url,
                        url=url,
                        offers=offers
                    )

                    restaurants.append(restaurant)
                    print(
                        f"[DEBUG] Successfully extracted: {name} | {rating} | {delivery_fee} | {url}")

                except Exception as e:
                    print(f"[DEBUG] Error extracting restaurant {i+1}: {e}")
                    continue

            if len(restaurants) < 5:
                print("[DEBUG] Got very few restaurants, trying alternative extraction...")

                h6_elements = driver.find_elements(
                    By.XPATH, "//h6[string-length(text()) > 5]")

                for i, h6_elem in enumerate(h6_elements[:15]):
                    try:
                        name = h6_elem.text.strip()

                        if name.lower() in ['filters', 'sort by'] or 'price range' in name.lower() or 'delivery time' in name.lower():
                            continue

                        print(f"[DEBUG] Alternative extraction {i+1}: {name}")

                        try:
                            card_container = h6_elem.find_element(
                                By.XPATH, "./ancestor::div[contains(@class, 'col')]")

                            url = "https://foodibd.com"
                            try:
                                link_elem = card_container.find_element(
                                    By.XPATH, ".//a[@href]")
                                href = link_elem.get_attribute("href")
                                if href and href.startswith("http"):
                                    url = href
                            except:
                                pass

                            image_url = "https://via.placeholder.com/300x200?text=No+Image"
                            try:
                                img_elem = card_container.find_element(By.XPATH, ".//img")
                                src = img_elem.get_attribute("src")
                                if src and "http" in src and "delivery-icon" not in src:
                                    image_url = src
                            except:
                                pass

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

        return ""
