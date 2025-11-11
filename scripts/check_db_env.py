"""
Quick script to print DATABASE_URL and attempt a lightweight DB connectivity check.
Run from project root: python scripts/check_db_env.py
"""
from dotenv import load_dotenv
import os
import traceback
from sqlalchemy import create_engine, text


def main():
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    print("DATABASE_URL:", url)
    if not url:
        print("ERROR: DATABASE_URL is empty or not set in .env")
        return 2

    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            res = conn.execute(text("SELECT 1"))
            print("SELECT 1 ->", list(res))
        print("Connection test succeeded")
        return 0
    except Exception:
        print("ERROR: Exception while testing DB connection:")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
