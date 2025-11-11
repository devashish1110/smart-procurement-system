"""
Test Database Connection
Run this script to verify database setup
File: scripts/test_connection.py
"""

import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config.database import check_db_connection, engine, SessionLocal
from backend.config.settings import validate_settings
from sqlalchemy import text


def test_environment_variables():
    """Test that all required environment variables are set"""
    print("\n" + "="*50)
    print("TESTING ENVIRONMENT VARIABLES")
    print("="*50)
    
    try:
        validate_settings()
        print("✓ All environment variables are set correctly")
        return True
    except Exception as e:
        print(f"✗ Environment variable error: {str(e)}")
        return False


def test_database_connection():
    """Test basic database connectivity"""
    print("\n" + "="*50)
    print("TESTING DATABASE CONNECTION")
    print("="*50)
    
    if check_db_connection():
        print("✓ Database connection successful")
        return True
    else:
        print("✗ Database connection failed")
        return False


def test_database_tables():
    """Test if all expected tables exist"""
    print("\n" + "="*50)
    print("TESTING DATABASE TABLES")
    print("="*50)
    
    expected_tables = [
        'users', 'patients', 'medicines', 'vendors',
        'inventory_stock', 'treatments', 'appointments',
        'bills', 'purchase_orders', 'purchase_order_items'
    ]
    
    try:
        db = SessionLocal()
        
        # Query to get all tables
        result = db.execute(text("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
        """))
        
        existing_tables = [row[0] for row in result]
        
        print(f"\nFound {len(existing_tables)} tables in database:")
        for table in existing_tables:
            status = "✓" if table in expected_tables else "?"
            print(f"  {status} {table}")
        
        missing_tables = set(expected_tables) - set(existing_tables)
        if missing_tables:
            print(f"\n⚠ Missing tables: {', '.join(missing_tables)}")
            print("  Run your data_pipeline.py to create and populate tables")
        else:
            print("\n✓ All expected tables exist")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"✗ Error checking tables: {str(e)}")
        return False


def test_table_data():
    """Test if tables have data"""
    print("\n" + "="*50)
    print("TESTING TABLE DATA")
    print("="*50)
    
    tables_to_check = [
        'users', 'patients', 'medicines', 'vendors',
        'inventory_stock', 'appointments', 'bills'
    ]
    
    try:
        db = SessionLocal()
        
        for table in tables_to_check:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.fetchone()[0]
            
            if count > 0:
                print(f"  ✓ {table:25s}: {count:6d} rows")
            else:
                print(f"  ⚠ {table:25s}: {count:6d} rows (empty)")
        
        db.close()
        print("\n✓ Data check complete")
        return True
        
    except Exception as e:
        print(f"✗ Error checking data: {str(e)}")
        return False


def test_sample_query():
    """Test a sample query"""
    print("\n" + "="*50)
    print("TESTING SAMPLE QUERY")
    print("="*50)
    
    try:
        db = SessionLocal()
        
        # Test query - get first user
        result = db.execute(text("SELECT username, full_name, role FROM users LIMIT 1"))
        user = result.fetchone()
        
        if user:
            print(f"\nSample User:")
            print(f"  Username: {user[0]}")
            print(f"  Name: {user[1]}")
            print(f"  Role: {user[2]}")
            print("\n✓ Sample query successful")
        else:
            print("⚠ No users found in database")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"✗ Error running query: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print(" DATABASE CONNECTION TEST SUITE")
    print("="*70)
    
    tests = [
        test_environment_variables,
        test_database_connection,
        test_database_tables,
        test_table_data,
        test_sample_query
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n✗ Test failed with exception: {str(e)}")
            failed += 1
    
    # Summary
    print("\n" + "="*70)
    print(f" TEST SUMMARY: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("\n🎉 All tests passed! Your database is ready.")
        print("\nNext steps:")
        print("  1. If tables are empty, run: python scripts/data_pipeline.py")
        print("  2. Start building the FastAPI backend")
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")
        print("\nCommon issues:")
        print("  - Check .env file is in the project root")
        print("  - Verify PostgreSQL is running")
        print("  - Confirm database credentials are correct")


if __name__ == "__main__":
    main()