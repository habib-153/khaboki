import json
import os
from datetime import datetime
from typing import List, Dict, Any
import sqlite3
import threading
from queue import Queue


class DatasetBuilder:
    def __init__(self, db_path="dataset/restaurants.db"):
        self.db_path = db_path
        self.data_queue = Queue()
        self.processing_thread = None
        self.setup_database()

    def setup_database(self):
        """Initialize SQLite database for dataset with location-aware delivery info"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # Drop old table if exists and create new improved structure
            conn.execute('DROP TABLE IF EXISTS restaurants')

            conn.execute('''
                CREATE TABLE restaurants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    cuisine_type TEXT,
                    image_url TEXT,
                    url TEXT,
                    platform TEXT NOT NULL,
                    rating TEXT,
                    restaurant_lat REAL,
                    restaurant_lng REAL,
                    delivery_time TEXT,
                    delivery_fee TEXT,
                    service_area_lat REAL,
                    service_area_lng REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, platform, service_area_lat, service_area_lng)
                )
            ''')

            # Create indexes for better performance
            conn.execute(
                'CREATE INDEX IF NOT EXISTS idx_platform ON restaurants(platform)')
            conn.execute(
                'CREATE INDEX IF NOT EXISTS idx_service_area ON restaurants(service_area_lat, service_area_lng)')
            conn.execute(
                'CREATE INDEX IF NOT EXISTS idx_restaurant_location ON restaurants(restaurant_lat, restaurant_lng)')
            conn.execute(
                'CREATE INDEX IF NOT EXISTS idx_name ON restaurants(name)')
            conn.execute(
                'CREATE INDEX IF NOT EXISTS idx_cuisine ON restaurants(cuisine_type)')

            print("[DATASET] Database initialized with improved structure")

    def add_scraped_data(self, data: Dict[str, Any], lat: float, lng: float):
        """Add scraped data to processing queue (non-blocking)"""
        self.data_queue.put({
            'data': data,
            'lat': lat,
            'lng': lng,
            'timestamp': datetime.now()
        })

        if not self.processing_thread or not self.processing_thread.is_alive():
            self.processing_thread = threading.Thread(
                target=self._process_queue)
            self.processing_thread.daemon = True
            self.processing_thread.start()

    def _process_queue(self):
        """Process queued data in background"""
        while not self.data_queue.empty():
            try:
                item = self.data_queue.get_nowait()
                self._process_restaurants(
                    item['data'], item['lat'], item['lng'])
            except Exception as e:
                print(f"[DATASET] Error processing item: {e}")

    def _process_restaurants(self, data: Dict[str, Any], lat: float, lng: float):
        """Process and clean restaurant data"""
        if not data.get('success') or not data.get('results'):
            print("[DATASET] No valid data to process")
            return

        restaurants_to_add = []

        for platform, restaurants in data['results'].items():
            if not restaurants:
                continue

            print(
                f"[DATASET] Processing {len(restaurants)} restaurants from {platform}")

            for restaurant in restaurants:
                cleaned_restaurant = self._clean_restaurant_data(
                    restaurant, platform, lat, lng)
                if cleaned_restaurant:
                    restaurants_to_add.append(cleaned_restaurant)

        if restaurants_to_add:
            self._batch_insert_restaurants(restaurants_to_add)
            print(
                f"[DATASET] Successfully processed {len(restaurants_to_add)} restaurants")
        else:
            print("[DATASET] No valid restaurants to add after cleaning")

    def _clean_restaurant_data(self, restaurant: Dict[str, Any], platform: str, lat: float, lng: float) -> Dict[str, Any]:
        """Clean and validate restaurant data with improved structure"""
        name = restaurant.get('name', '').strip()

        # Skip unknown restaurants
        if not name or name == "Unknown Restaurant" or "unknown" in name.lower():
            return None

        # Skip if no valid URL
        url = restaurant.get('url', '').strip()
        if not url or url.lower() in ['null', 'none', '']:
            return None

        # Clean cuisine type
        cuisine_type = restaurant.get('cuisine_type', '').strip()
        if not cuisine_type or cuisine_type.lower() in ['not specified', 'unknown', '']:
            cuisine_type = 'Various'
        else:
            cuisine_type = cuisine_type.title()

        # Clean image URL
        image_url = restaurant.get('image_url', '').strip()
        if 'placeholder' in image_url.lower() or not image_url:
            image_url = ''

        # Clean rating
        rating = restaurant.get('rating', '').strip()
        if rating.lower() in ['no rating', '0', 'unknown']:
            rating = ''

        # Clean delivery info
        delivery_time = restaurant.get('delivery_time', '').strip()
        delivery_fee = restaurant.get('delivery_fee', '').strip()

        if delivery_time.lower() in ['unknown', 'not specified', '']:
            delivery_time = ''
        if delivery_fee.lower() in ['unknown', 'not specified', '']:
            delivery_fee = ''

        cleaned = {
            'name': name,
            'cuisine_type': cuisine_type,
            'image_url': image_url,
            'url': url,
            'platform': platform.lower(),
            'rating': rating,
            # Restaurant's location (same as service area for now)
            'restaurant_lat': round(lat, 6),
            'restaurant_lng': round(lng, 6),
            'delivery_time': delivery_time,
            'delivery_fee': delivery_fee,
            # Area where this delivery info applies
            'service_area_lat': round(lat, 4),
            'service_area_lng': round(lng, 4)
        }

        return cleaned

    def _batch_insert_restaurants(self, restaurants: List[Dict[str, Any]]):
        """Insert restaurants into database with smart conflict resolution"""
        with sqlite3.connect(self.db_path) as conn:
            inserted_count = 0
            updated_count = 0

            for restaurant in restaurants:
                try:
                    # Check if restaurant already exists for this service area
                    existing = conn.execute('''
                        SELECT id, rating, delivery_time, delivery_fee 
                        FROM restaurants 
                        WHERE name = ? AND platform = ? AND service_area_lat = ? AND service_area_lng = ?
                    ''', (
                        restaurant['name'],
                        restaurant['platform'],
                        restaurant['service_area_lat'],
                        restaurant['service_area_lng']
                    )).fetchone()

                    if existing:
                        # Update existing record if we have better data
                        should_update = False
                        update_fields = []
                        update_values = []

                        # Update if we have better rating info
                        if restaurant['rating'] and not existing[1]:
                            update_fields.append('rating = ?')
                            update_values.append(restaurant['rating'])
                            should_update = True

                        # Update if we have better delivery info
                        if restaurant['delivery_time'] and not existing[2]:
                            update_fields.append('delivery_time = ?')
                            update_values.append(restaurant['delivery_time'])
                            should_update = True

                        if restaurant['delivery_fee'] and not existing[3]:
                            update_fields.append('delivery_fee = ?')
                            update_values.append(restaurant['delivery_fee'])
                            should_update = True

                        # Always update image_url and url if available
                        if restaurant['image_url']:
                            update_fields.append('image_url = ?')
                            update_values.append(restaurant['image_url'])
                            should_update = True

                        if should_update:
                            update_fields.append(
                                'updated_at = CURRENT_TIMESTAMP')
                            # id for WHERE clause
                            update_values.append(existing[0])

                            query = f"UPDATE restaurants SET {', '.join(update_fields)} WHERE id = ?"
                            conn.execute(query, update_values)
                            updated_count += 1
                    else:
                        # Insert new record
                        conn.execute('''
                            INSERT INTO restaurants 
                            (name, cuisine_type, image_url, url, platform, rating, 
                             restaurant_lat, restaurant_lng, delivery_time, delivery_fee,
                             service_area_lat, service_area_lng)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            restaurant['name'],
                            restaurant['cuisine_type'],
                            restaurant['image_url'],
                            restaurant['url'],
                            restaurant['platform'],
                            restaurant['rating'],
                            restaurant['restaurant_lat'],
                            restaurant['restaurant_lng'],
                            restaurant['delivery_time'],
                            restaurant['delivery_fee'],
                            restaurant['service_area_lat'],
                            restaurant['service_area_lng']
                        ))
                        inserted_count += 1

                except Exception as e:
                    print(
                        f"[DATASET] Error processing {restaurant['name']}: {e}")

            print(
                f"[DATASET] Database updated: {inserted_count} new, {updated_count} updated")

    def export_dataset(self, format_type='json', output_path=None):
        """Export dataset with improved metadata"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"dataset/khabo_ki_dataset_{timestamp}.{format_type}"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT name, cuisine_type, image_url, url, platform, rating,
                       restaurant_lat, restaurant_lng, delivery_time, delivery_fee,
                       service_area_lat, service_area_lng, created_at, updated_at
                FROM restaurants 
                WHERE name != 'Unknown Restaurant' 
                  AND url IS NOT NULL 
                  AND url != ''
                ORDER BY platform, name
            ''')

            restaurants = [dict(row) for row in cursor.fetchall()]

        if format_type == 'json':
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Get additional stats for metadata
            platforms = list(set(r['platform'] for r in restaurants))
            cuisines = list(set(r['cuisine_type']
                            for r in restaurants if r['cuisine_type']))
            service_areas = list(
                set((r['service_area_lat'], r['service_area_lng']) for r in restaurants))

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': {
                        'dataset_name': 'Khabo Ki Restaurant Dataset',
                        'description': 'Food delivery restaurants dataset for Bangladesh with location-aware delivery information',
                        'version': '2.0',
                        'total_restaurants': len(restaurants),
                        'platforms': platforms,
                        'unique_cuisines': len(cuisines),
                        'service_areas_covered': len(service_areas),
                        'generated_at': datetime.now().isoformat(),
                        'data_structure': {
                            'name': 'Restaurant name',
                            'cuisine_type': 'Type of cuisine offered',
                            'platform': 'Delivery platform (foodpanda, foodi)',
                            'rating': 'Customer rating with review count',
                            'restaurant_lat/lng': 'Restaurant physical location',
                            'service_area_lat/lng': 'Area where delivery info applies',
                            'delivery_time': 'Estimated delivery time to service area',
                            'delivery_fee': 'Delivery cost to service area',
                            'url': 'Direct link to restaurant page',
                            'image_url': 'Restaurant image URL'
                        },
                        'usage_notes': [
                            'Same restaurant may appear multiple times for different service areas',
                            'Delivery time and fee are specific to the service area coordinates',
                            'Use service_area coordinates to find restaurants delivering to specific locations'
                        ]
                    },
                    'restaurants': restaurants
                }, f, indent=2, ensure_ascii=False)

        print(
            f"[DATASET] Exported {len(restaurants)} restaurants to {output_path}")
        return output_path

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive dataset statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                print(f"[DEBUG] Connected to database: {self.db_path}")

                # Test basic connection
                cursor = conn.execute('SELECT COUNT(*) FROM restaurants')
                total = cursor.fetchone()[0]
                print(f"[DEBUG] Total restaurants found: {total}")

                if total == 0:
                    return {
                        'total_restaurants': 0,
                        'restaurants_with_delivery_info': 0,
                        'platform_breakdown': {},
                        'top_cuisines': {},
                        'top_service_areas': [],
                        'rating_distribution': {},
                        'data_quality': {
                            'coverage_percentage': 0,
                            'platforms_active': 0,
                            'cuisine_variety': 0
                        },
                        'last_updated': datetime.now().isoformat(),
                        'debug_info': 'Database is empty'
                    }

                # Platform breakdown
                cursor = conn.execute('''
                    SELECT platform, COUNT(*) as count
                    FROM restaurants 
                    GROUP BY platform
                    ORDER BY count DESC
                ''')
                platform_stats = dict(cursor.fetchall())
                print(f"[DEBUG] Platform stats: {platform_stats}")

                # Cuisine breakdown
                cursor = conn.execute('''
                    SELECT cuisine_type, COUNT(*) as count
                    FROM restaurants 
                    WHERE cuisine_type IS NOT NULL AND cuisine_type != ''
                    GROUP BY cuisine_type 
                    ORDER BY count DESC
                    LIMIT 10
                ''')
                cuisine_stats = dict(cursor.fetchall())
                print(f"[DEBUG] Cuisine stats: {cuisine_stats}")

                # Service area breakdown
                cursor = conn.execute('''
                    SELECT 
                        ROUND(service_area_lat, 2) as lat_area,
                        ROUND(service_area_lng, 2) as lng_area,
                        COUNT(*) as count
                    FROM restaurants 
                    GROUP BY lat_area, lng_area
                    ORDER BY count DESC
                    LIMIT 10
                ''')
                area_stats = [{'lat': row[0], 'lng': row[1], 'count': row[2]}
                            for row in cursor.fetchall()]

                # Rating distribution
                cursor = conn.execute('''
                    SELECT 
                        CASE 
                            WHEN rating LIKE '4.%' THEN '4.0+'
                            WHEN rating LIKE '3.%' THEN '3.0-3.9'
                            WHEN rating LIKE '2.%' THEN '2.0-2.9'
                            WHEN rating LIKE '1.%' THEN '1.0-1.9'
                            ELSE 'No Rating'
                        END as rating_range,
                        COUNT(*) as count
                    FROM restaurants 
                    GROUP BY rating_range
                    ORDER BY count DESC
                ''')
                rating_distribution = dict(cursor.fetchall())

                # Count with delivery info
                delivery_info_cursor = conn.execute('''
                    SELECT COUNT(*) FROM restaurants 
                    WHERE delivery_time != '' OR delivery_fee != ''
                ''')
                with_delivery_info = delivery_info_cursor.fetchone()[0]

                result = {
                    'total_restaurants': total,
                    'restaurants_with_delivery_info': with_delivery_info,
                    'platform_breakdown': platform_stats,
                    'top_cuisines': cuisine_stats,
                    'top_service_areas': area_stats,
                    'rating_distribution': rating_distribution,
                    'data_quality': {
                        'coverage_percentage': round((with_delivery_info / total) * 100, 1) if total > 0 else 0,
                        'platforms_active': len(platform_stats),
                        'cuisine_variety': len(cuisine_stats)
                    },
                    'last_updated': datetime.now().isoformat()
                }

                print(f"[DEBUG] Final result: {result}")
                return result

        except Exception as e:
            print(f"[ERROR] Error in get_stats: {e}")
            import traceback
            traceback.print_exc()
            raise e

    def clean_database(self):
        """Clean invalid and duplicate entries"""
        with sqlite3.connect(self.db_path) as conn:
            # Remove entries with no URL
            removed_no_url = conn.execute('''
                DELETE FROM restaurants 
                WHERE url IS NULL OR url = '' OR url = 'null'
            ''').rowcount

            # Remove unknown restaurants
            removed_unknown = conn.execute('''
                DELETE FROM restaurants 
                WHERE name = 'Unknown Restaurant' 
                   OR name LIKE '%unknown%'
                   OR name = ''
            ''').rowcount

            # Remove entries without proper names
            removed_invalid_names = conn.execute('''
                DELETE FROM restaurants 
                WHERE name IS NULL OR LENGTH(name) < 2
            ''').rowcount

            print(f"[DATASET] Cleaned database:")
            print(f"  - Removed {removed_no_url} entries without URL")
            print(f"  - Removed {removed_unknown} unknown restaurants")
            print(
                f"  - Removed {removed_invalid_names} entries with invalid names")

    def get_restaurants_by_area(self, lat: float, lng: float, radius_km: float = 5) -> List[Dict]:
        """Get restaurants that serve a specific area"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Simple bounding box search (can be improved with proper distance calculation)
            lat_margin = radius_km / 111.0  # Rough conversion to degrees
            lng_margin = radius_km / (111.0 * abs(lat))

            cursor = conn.execute('''
                SELECT * FROM restaurants 
                WHERE service_area_lat BETWEEN ? AND ?
                  AND service_area_lng BETWEEN ? AND ?
                ORDER BY platform, name
            ''', (
                lat - lat_margin, lat + lat_margin,
                lng - lng_margin, lng + lng_margin
            ))

            return [dict(row) for row in cursor.fetchall()]


# Global instance
dataset_builder = DatasetBuilder()