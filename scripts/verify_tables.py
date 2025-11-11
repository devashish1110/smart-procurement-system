"""
Verify All Database Tables
File: scripts/verify_tables.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def verify_all_tables():
    """Verify all required tables exist and have data"""
    
    engine = create_engine(DATABASE_URL)
    
    print("="*70)
    print("DATABASE VERIFICATION")
    print("="*70)
    
    required_tables = [
        'users', 'patients', 'medicines', 'vendors',
        'inventory_stock', 'treatments', 'appointments', 'bills',
        'purchase_orders', 'purchase_order_items',
        'chat_conversations', 'alerts'
    ]
    
    with engine.connect() as conn:
        print("\nChecking tables and row counts:\n")
        
        all_exist = True
        results = []
        
        for table in required_tables:
            try:
                # Check if table exists and get count
                count_query = f"SELECT COUNT(*) FROM {table}"
                result = conn.execute(text(count_query))
                count = result.fetchone()[0]
                
                status = "✓" if count > 0 else "⚠"
                results.append((status, table, count))
                
            except Exception as e:
                results.append(("✗", table, "NOT FOUND"))
                all_exist = False
        
        # Print results in organized format
        for status, table, count in results:
            if isinstance(count, int):
                print(f"  {status} {table:30s}: {count:6d} rows")
            else:
                print(f"  {status} {table:30s}: {count}")
        
        print("\n" + "="*70)
        
        if all_exist:
            total_rows = sum(r[2] for r in results if isinstance(r[2], int))
            print(f"✅ All {len(required_tables)} tables verified!")
            print(f"   Total rows across all tables: {total_rows:,}")
        else:
            missing = [r[1] for r in results if r[2] == "NOT FOUND"]
            print(f"❌ Missing tables: {', '.join(missing)}")
        
        print("="*70)


if __name__ == "__main__":
    verify_all_tables()