import sqlite3
import os
from datetime import datetime

def migrate_database_standalone():
    """Standalone migration without Flask dependencies"""
    db_path = "dataset/restaurants.db"
    
    if not os.path.exists(db_path):
        print("Database file not found!")
        return
    
    print("[MIGRATION] Starting standalone database migration...")
    
    try:
        # Use a longer timeout and different connection settings
        conn = sqlite3.connect(db_path, timeout=30.0, isolation_level=None)
        conn.execute('PRAGMA journal_mode=WAL')  # Better for concurrent access
        
        # First, analyze what we have
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
        
        if total == 0:
            print("Database is empty, no migration needed")
            return
        
        # Ask for confirmation
        proceed = input(f"\nProceed with migration? This will clean {bad_names + bad_urls + bad_images + bad_cuisine} low-quality records. (y/N): ")
        
        if proceed.lower() != 'y':
            print("Migration cancelled.")
            return
        
        # Create backup first
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_table = f"restaurants_backup_{timestamp}"
        
        print(f"[MIGRATION] Creating backup table: {backup_table}")
        conn.execute(f'CREATE TABLE {backup_table} AS SELECT * FROM restaurants')
        
        backup_count = conn.execute(f'SELECT COUNT(*) FROM {backup_table}').fetchone()[0]
        print(f"[MIGRATION] Backed up {backup_count} records")
        
        # Step 1: Update empty ratings to "Not Reviewed"
        print("[MIGRATION] Updating empty ratings...")
        updated_ratings = conn.execute('''
            UPDATE restaurants 
            SET rating = 'Not Reviewed'
            WHERE rating IS NULL OR rating = '' OR rating = 'null' 
               OR rating = 'unknown' OR rating = 'no rating' OR rating = '0'
        ''').rowcount
        print(f"[MIGRATION] Updated {updated_ratings} empty ratings")
        
        # Step 2: Clean delivery info
        print("[MIGRATION] Cleaning delivery info...")
        conn.execute('''
            UPDATE restaurants 
            SET delivery_time = ''
            WHERE delivery_time IN ('unknown', 'not specified', 'null', 'not available')
        ''')
        
        conn.execute('''
            UPDATE restaurants 
            SET delivery_fee = ''
            WHERE delivery_fee IN ('unknown', 'not specified', 'null', 'not available')
        ''')
        
        # Step 3: Remove low-quality records
        print("[MIGRATION] Removing low-quality records...")
        
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
        final_count = conn.execute('SELECT COUNT(*) FROM restaurants').fetchone()[0]
        
        print(f"\n[MIGRATION] ✅ Migration completed successfully!")
        print(f"  - Removed {removed_unknown} unknown restaurants")
        print(f"  - Removed {removed_no_url} without URLs")
        print(f"  - Removed {removed_no_image} without images")
        print(f"  - Removed {removed_no_cuisine} without cuisine types")
        print(f"  - Final count: {final_count} high-quality records")
        print(f"  - Backup saved as: {backup_table}")
        
        conn.close()
        
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            print("❌ Database is still locked. Please:")
            print("  1. Stop your Flask application completely")
            print("  2. Close VS Code or any database viewers")
            print("  3. Wait 30 seconds and try again")
        else:
            print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate_database_standalone()