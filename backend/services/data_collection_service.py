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
            # Check if table exists before dropping
            table_exists = conn.execute('''
                SELECT name FROM sqlite_master WHERE type='table' AND name='restaurants'
            ''').fetchone()

            if not table_exists:
                # Only create table if it doesn't exist
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
                print("[DATASET] Created new restaurants table")
            else:
                print("[DATASET] Using existing restaurants table")

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
        """Clean and validate restaurant data with strict quality requirements"""
        name = restaurant.get('name', '').strip()

        # Skip unknown restaurants
        if not name or name == "Unknown Restaurant" or "unknown" in name.lower():
            print(f"[DATASET] Skipping unknown restaurant: {name}")
            return None

        # Skip if no valid URL (REQUIRED)
        url = restaurant.get('url', '').strip()
        if not url or url.lower() in ['null', 'none', '', 'not available']:
            print(f"[DATASET] Skipping restaurant without URL: {name}")
            return None

        # Skip if no image URL (REQUIRED for quality dataset)
        image_url = restaurant.get('image_url', '').strip()
        if (not image_url or
            image_url.lower() in ['null', 'none', '', 'not available'] or
            'placeholder' in image_url.lower() or
                image_url == 'https://'):
            print(f"[DATASET] Skipping restaurant without valid image: {name}")
            return None

        # Clean cuisine type (REQUIRED)
        cuisine_type = restaurant.get('cuisine_type', '').strip()
        if not cuisine_type or cuisine_type.lower() in ['not specified', 'unknown', '', 'null']:
            print(
                f"[DATASET] Skipping restaurant without cuisine type: {name}")
            return None
        else:
            cuisine_type = cuisine_type.title()

        # Handle rating - replace empty with "Not Reviewed"
        rating = restaurant.get('rating', '').strip()
        if not rating or rating.lower() in ['no rating', '0', 'unknown', '', 'null']:
            rating = 'Not Reviewed'

        # Clean delivery info - these can be empty for now
        delivery_time = restaurant.get('delivery_time', '').strip()
        delivery_fee = restaurant.get('delivery_fee', '').strip()

        if delivery_time.lower() in ['unknown', 'not specified', '', 'null']:
            delivery_time = ''
        if delivery_fee.lower() in ['unknown', 'not specified', '', 'null']:
            delivery_fee = ''

        # Only proceed if we have ALL required fields
        required_fields = [name, url, image_url, cuisine_type]
        if not all(required_fields):
            print(
                f"[DATASET] Skipping restaurant missing required fields: {name}")
            return None

        cleaned = {
            'name': name,
            'cuisine_type': cuisine_type,
            'image_url': image_url,
            'url': url,
            'platform': platform.lower(),
            'rating': rating,  # This will be "Not Reviewed" if empty
            # Restaurant's location (same as service area for now)
            'restaurant_lat': round(lat, 6),
            'restaurant_lng': round(lng, 6),
            'delivery_time': delivery_time,  # Can be empty
            'delivery_fee': delivery_fee,    # Can be empty
            # Area where this delivery info applies
            'service_area_lat': round(lat, 4),
            'service_area_lng': round(lng, 4)
        }

        print(f"[DATASET] ✅ Cleaned restaurant: {name} - {cuisine_type}")
        return cleaned

    def _batch_insert_restaurants(self, restaurants: List[Dict[str, Any]]):
        """Insert restaurants into database with smart conflict resolution"""
        with sqlite3.connect(self.db_path) as conn:
            inserted_count = 0
            updated_count = 0
            skipped_count = 0

            for restaurant in restaurants:
                try:
                    # Check if restaurant already exists for this service area
                    existing = conn.execute('''
                        SELECT id, rating, delivery_time, delivery_fee, image_url 
                        FROM restaurants 
                        WHERE name = ? AND platform = ? AND service_area_lat = ? AND service_area_lng = ?
                    ''', (
                        restaurant['name'],
                        restaurant['platform'],
                        restaurant['service_area_lat'],
                        restaurant['service_area_lng']
                    )).fetchone()

                    if existing:
                        # Update existing record only if we have BETTER data
                        should_update = False
                        update_fields = []
                        update_values = []

                        # Update rating if current is "Not Reviewed" and we have a real rating
                        if (restaurant['rating'] != 'Not Reviewed' and
                                (not existing[1] or existing[1] == 'Not Reviewed')):
                            update_fields.append('rating = ?')
                            update_values.append(restaurant['rating'])
                            should_update = True
                            print(
                                f"[DATASET] Updating rating for {restaurant['name']}: {existing[1]} -> {restaurant['rating']}")

                        # Update delivery info if we have new data and existing is empty
                        if restaurant['delivery_time'] and not existing[2]:
                            update_fields.append('delivery_time = ?')
                            update_values.append(restaurant['delivery_time'])
                            should_update = True

                        if restaurant['delivery_fee'] and not existing[3]:
                            update_fields.append('delivery_fee = ?')
                            update_values.append(restaurant['delivery_fee'])
                            should_update = True

                        # Update image_url only if existing is empty and we have a valid one
                        if restaurant['image_url'] and not existing[4]:
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
                            skipped_count += 1
                            print(
                                f"[DATASET] Skipping update for {restaurant['name']} - no better data")
                    else:
                        # Insert new record (we already validated all required fields exist)
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
                        print(
                            f"[DATASET] ✅ Inserted new restaurant: {restaurant['name']}")

                except Exception as e:
                    print(
                        f"[DATASET] Error processing {restaurant['name']}: {e}")

            print(
                f"[DATASET] Database updated: {inserted_count} new, {updated_count} updated, {skipped_count} skipped")

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
                  AND image_url IS NOT NULL
                  AND image_url != ''
                  AND cuisine_type IS NOT NULL
                  AND cuisine_type != ''
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
                        'description': 'High-quality food delivery restaurants dataset for Bangladesh with complete information',
                        'version': '2.1',
                        'total_restaurants': len(restaurants),
                        'platforms': platforms,
                        'unique_cuisines': len(cuisines),
                        'service_areas_covered': len(service_areas),
                        'generated_at': datetime.now().isoformat(),
                        'quality_requirements': [
                            'All restaurants have valid URLs',
                            'All restaurants have image URLs',
                            'All restaurants have cuisine types specified',
                            'Ratings marked as "Not Reviewed" if unavailable'
                        ],
                        'data_structure': {
                            'name': 'Restaurant name',
                            'cuisine_type': 'Type of cuisine offered',
                            'platform': 'Delivery platform (foodpanda, foodi)',
                            'rating': 'Customer rating with review count or "Not Reviewed"',
                            'restaurant_lat/lng': 'Restaurant physical location',
                            'service_area_lat/lng': 'Area where delivery info applies',
                            'delivery_time': 'Estimated delivery time to service area',
                            'delivery_fee': 'Delivery cost to service area',
                            'url': 'Direct link to restaurant page',
                            'image_url': 'Restaurant image URL'
                        }
                    },
                    'restaurants': restaurants
                }, f, indent=2, ensure_ascii=False)

        print(
            f"[DATASET] Exported {len(restaurants)} high-quality restaurants to {output_path}")
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
                            'cuisine_variety': 0,
                            'complete_records': 0
                        },
                        'last_updated': datetime.now().isoformat(),
                        'debug_info': 'Database is empty'
                    }

                # Count complete records (all required fields present)
                cursor = conn.execute('''
                    SELECT COUNT(*) FROM restaurants 
                    WHERE name IS NOT NULL AND name != '' 
                      AND url IS NOT NULL AND url != ''
                      AND image_url IS NOT NULL AND image_url != ''
                      AND cuisine_type IS NOT NULL AND cuisine_type != ''
                ''')
                complete_records = cursor.fetchone()[0]

                # Platform breakdown
                cursor = conn.execute('''
                    SELECT platform, COUNT(*) as count
                    FROM restaurants 
                    GROUP BY platform
                    ORDER BY count DESC
                ''')
                platform_stats = dict(cursor.fetchall())

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

                # Rating distribution (including "Not Reviewed")
                cursor = conn.execute('''
                    SELECT 
                        CASE 
                            WHEN rating = 'Not Reviewed' THEN 'Not Reviewed'
                            WHEN rating LIKE '4.%' THEN '4.0+'
                            WHEN rating LIKE '3.%' THEN '3.0-3.9'
                            WHEN rating LIKE '2.%' THEN '2.0-2.9'
                            WHEN rating LIKE '1.%' THEN '1.0-1.9'
                            ELSE 'Other'
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
                        'cuisine_variety': len(cuisine_stats),
                        'complete_records': complete_records,
                        'completeness_percentage': round((complete_records / total) * 100, 1) if total > 0 else 0
                    },
                    'last_updated': datetime.now().isoformat()
                }

                return result

        except Exception as e:
            print(f"[ERROR] Error in get_stats: {e}")
            import traceback
            traceback.print_exc()
            raise e

    def clean_database(self):
        """Clean invalid and duplicate entries with stricter criteria"""
        with sqlite3.connect(self.db_path) as conn:
            # Remove entries with no URL
            removed_no_url = conn.execute('''
                DELETE FROM restaurants 
                WHERE url IS NULL OR url = '' OR url = 'null' OR url = 'not available'
            ''').rowcount

            # Remove entries with no image URL
            removed_no_image = conn.execute('''
                DELETE FROM restaurants 
                WHERE image_url IS NULL OR image_url = '' OR image_url = 'null' 
                   OR image_url LIKE '%placeholder%' OR image_url = 'https://'
            ''').rowcount

            # Remove unknown restaurants
            removed_unknown = conn.execute('''
                DELETE FROM restaurants 
                WHERE name = 'Unknown Restaurant' 
                   OR name LIKE '%unknown%'
                   OR name = ''
                   OR name IS NULL
            ''').rowcount

            # Remove entries without cuisine type
            removed_no_cuisine = conn.execute('''
                DELETE FROM restaurants 
                WHERE cuisine_type IS NULL OR cuisine_type = '' 
                   OR cuisine_type = 'not specified' OR cuisine_type = 'unknown'
            ''').rowcount

            print(f"[DATASET] Cleaned database:")
            print(f"  - Removed {removed_no_url} entries without URL")
            print(f"  - Removed {removed_no_image} entries without image")
            print(f"  - Removed {removed_unknown} unknown restaurants")
            print(
                f"  - Removed {removed_no_cuisine} entries without cuisine type")

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
                  AND name IS NOT NULL AND name != ''
                  AND url IS NOT NULL AND url != ''
                  AND image_url IS NOT NULL AND image_url != ''
                  AND cuisine_type IS NOT NULL AND cuisine_type != ''
                ORDER BY platform, name
            ''', (
                lat - lat_margin, lat + lat_margin,
                lng - lng_margin, lng + lng_margin
            ))

            return [dict(row) for row in cursor.fetchall()]

    def migrate_existing_database(self):
        """Migrate existing database to new quality standards without dropping table"""
        print("[MIGRATION] Starting database migration to new quality standards...")

        with sqlite3.connect(self.db_path) as conn:
            # First, let's see what we have
            cursor = conn.execute('SELECT COUNT(*) FROM restaurants')
            total_before = cursor.fetchone()[0]
            print(f"[MIGRATION] Found {total_before} existing records")

            if total_before == 0:
                print("[MIGRATION] Database is empty, no migration needed")
                return

            # Step 1: Update empty ratings to "Not Reviewed"
            updated_ratings = conn.execute('''
                UPDATE restaurants 
                SET rating = 'Not Reviewed', updated_at = CURRENT_TIMESTAMP
                WHERE rating IS NULL OR rating = '' OR rating = 'null' 
                OR rating = 'unknown' OR rating = 'no rating' OR rating = '0'
            ''').rowcount
            print(
                f"[MIGRATION] Updated {updated_ratings} empty ratings to 'Not Reviewed'")

            # Step 2: Clean up delivery info (set empty strings for invalid values)
            updated_delivery_time = conn.execute('''
                UPDATE restaurants 
                SET delivery_time = '', updated_at = CURRENT_TIMESTAMP
                WHERE delivery_time IN ('unknown', 'not specified', 'null', 'not available')
            ''').rowcount

            updated_delivery_fee = conn.execute('''
                UPDATE restaurants 
                SET delivery_fee = '', updated_at = CURRENT_TIMESTAMP
                WHERE delivery_fee IN ('unknown', 'not specified', 'null', 'not available')
            ''').rowcount

            print(
                f"[MIGRATION] Cleaned {updated_delivery_time} delivery times and {updated_delivery_fee} delivery fees")

            # Step 3: Remove low-quality records (this is where we apply strict standards)
            print("[MIGRATION] Removing low-quality records...")

            # Mark records for deletion (don't delete yet, just log what would be removed)
            cursor = conn.execute('''
                SELECT COUNT(*) FROM restaurants 
                WHERE name IS NULL OR name = '' OR name = 'Unknown Restaurant' 
                OR name LIKE '%unknown%'
            ''')
            unknown_restaurants = cursor.fetchone()[0]

            cursor = conn.execute('''
                SELECT COUNT(*) FROM restaurants 
                WHERE url IS NULL OR url = '' OR url = 'null' OR url = 'not available'
            ''')
            no_url = cursor.fetchone()[0]

            cursor = conn.execute('''
                SELECT COUNT(*) FROM restaurants 
                WHERE image_url IS NULL OR image_url = '' OR image_url = 'null' 
                OR image_url LIKE '%placeholder%' OR image_url = 'https://'
            ''')
            no_image = cursor.fetchone()[0]

            cursor = conn.execute('''
                SELECT COUNT(*) FROM restaurants 
                WHERE cuisine_type IS NULL OR cuisine_type = '' 
                OR cuisine_type = 'not specified' OR cuisine_type = 'unknown'
            ''')
            no_cuisine = cursor.fetchone()[0]

            print(f"[MIGRATION] Records that will be removed:")
            print(f"  - {unknown_restaurants} unknown restaurants")
            print(f"  - {no_url} without URLs")
            print(f"  - {no_image} without images")
            print(f"  - {no_cuisine} without cuisine types")

            total_to_remove = unknown_restaurants + no_url + no_image + no_cuisine
            remaining_after_cleanup = total_before - total_to_remove

            print(
                f"[MIGRATION] Will keep {remaining_after_cleanup} high-quality records out of {total_before}")

            # Ask for confirmation before deleting
            print(
                "\n[MIGRATION] Do you want to proceed with removing low-quality records?")
            print("This will permanently delete records that don't meet quality standards.")

            # For now, let's not auto-delete. Instead, create a backup table
            self._create_backup_and_clean()

        print("[MIGRATION] Migration completed!")


    def _create_backup_and_clean(self):
        """Create backup of current data and clean the main table"""
        with sqlite3.connect(self.db_path) as conn:
            # Create backup table with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_table = f"restaurants_backup_{timestamp}"

            print(f"[MIGRATION] Creating backup table: {backup_table}")

            # Copy current table to backup
            conn.execute(f'''
                CREATE TABLE {backup_table} AS 
                SELECT * FROM restaurants
            ''')

            backup_count = conn.execute(
                f'SELECT COUNT(*) FROM {backup_table}').fetchone()[0]
            print(
                f"[MIGRATION] Backed up {backup_count} records to {backup_table}")

            # Now clean the main table
            removed_unknown = conn.execute('''
                DELETE FROM restaurants 
                WHERE name IS NULL OR name = '' OR name = 'Unknown Restaurant' 
                OR name LIKE '%unknown%'
            ''').rowcount

            removed_no_url = conn.execute('''
                DELETE FROM restaurants 
                WHERE url IS NULL OR url = '' OR url = 'null' OR url = 'not available'
            ''').rowcount

            removed_no_image = conn.execute('''
                DELETE FROM restaurants 
                WHERE image_url IS NULL OR image_url = '' OR image_url = 'null' 
                OR image_url LIKE '%placeholder%' OR image_url = 'https://'
            ''').rowcount

            removed_no_cuisine = conn.execute('''
                DELETE FROM restaurants 
                WHERE cuisine_type IS NULL OR cuisine_type = '' 
                OR cuisine_type = 'not specified' OR cuisine_type = 'unknown'
            ''').rowcount

            # Get final count
            final_count = conn.execute(
                'SELECT COUNT(*) FROM restaurants').fetchone()[0]

            print(f"[MIGRATION] Cleanup completed:")
            print(f"  - Removed {removed_unknown} unknown restaurants")
            print(f"  - Removed {removed_no_url} without URLs")
            print(f"  - Removed {removed_no_image} without images")
            print(f"  - Removed {removed_no_cuisine} without cuisine types")
            print(f"  - Final count: {final_count} high-quality records")
            print(f"  - Backup available in table: {backup_table}")


    def run_migration_safely(self):
        """Safe migration that you can run manually"""
        print("[MIGRATION] Starting safe migration process...")

        # First, just analyze what we have
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN name IS NULL OR name = '' OR name = 'Unknown Restaurant' THEN 1 END) as bad_names,
                    COUNT(CASE WHEN url IS NULL OR url = '' OR url = 'null' THEN 1 END) as bad_urls,
                    COUNT(CASE WHEN image_url IS NULL OR image_url = '' OR image_url = 'null' THEN 1 END) as bad_images,
                    COUNT(CASE WHEN cuisine_type IS NULL OR cuisine_type = '' THEN 1 END) as bad_cuisine,
                    COUNT(CASE WHEN rating IS NULL OR rating = '' OR rating = 'null' THEN 1 END) as empty_ratings
                FROM restaurants
            ''')

            stats = cursor.fetchone()
            total, bad_names, bad_urls, bad_images, bad_cuisine, empty_ratings = stats

            print(f"\n[ANALYSIS] Current database status:")
            print(f"  Total records: {total}")
            print(f"  Bad names: {bad_names}")
            print(f"  Bad URLs: {bad_urls}")
            print(f"  Bad images: {bad_images}")
            print(f"  Bad cuisine types: {bad_cuisine}")
            print(f"  Empty ratings: {empty_ratings}")

            high_quality = total - \
                max(bad_names, bad_urls, bad_images, bad_cuisine)
            print(f"  High-quality records: ~{high_quality}")

            return {
                'total': total,
                'bad_names': bad_names,
                'bad_urls': bad_urls,
                'bad_images': bad_images,
                'bad_cuisine': bad_cuisine,
                'empty_ratings': empty_ratings,
                'estimated_high_quality': high_quality
            }
# Global instance
dataset_builder = DatasetBuilder()