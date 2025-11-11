"""
Create Chat Conversations and Alerts Tables
File: scripts/create_chat_tables.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def create_tables():
    """Create chat_conversations and alerts tables"""
    
    engine = create_engine(DATABASE_URL)
    
    print("="*70)
    print("CREATING MISSING TABLES")
    print("="*70)
    
    with engine.connect() as conn:
        
        # 1. Create chat_conversations table
        print("\n[1/2] Creating chat_conversations table...")
        
        create_chat_table = """
        CREATE TABLE IF NOT EXISTS chat_conversations (
            conversation_id SERIAL PRIMARY KEY,
            session_id VARCHAR(100) NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            intent VARCHAR(50),
            confidence FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_conversations(session_id);
        CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_conversations(user_id);
        CREATE INDEX IF NOT EXISTS idx_chat_created ON chat_conversations(created_at);
        """
        
        conn.execute(text(create_chat_table))
        conn.commit()
        print("✓ chat_conversations table created")
        
        
        # 2. Create alerts table
        print("\n[2/2] Creating alerts table...")
        
        create_alerts_table = """
        CREATE TABLE IF NOT EXISTS alerts (
            alert_id SERIAL PRIMARY KEY,
            alert_type VARCHAR(50) NOT NULL,
            title VARCHAR(200) NOT NULL,
            message TEXT NOT NULL,
            severity VARCHAR(20) NOT NULL,
            target_user_id INTEGER,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read_at TIMESTAMP,
            FOREIGN KEY (target_user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_alert_type ON alerts(alert_type);
        CREATE INDEX IF NOT EXISTS idx_alert_user ON alerts(target_user_id);
        CREATE INDEX IF NOT EXISTS idx_alert_read ON alerts(is_read);
        CREATE INDEX IF NOT EXISTS idx_alert_created ON alerts(created_at);
        """
        
        conn.execute(text(create_alerts_table))
        conn.commit()
        print("✓ alerts table created")
        
        
        # 3. Verify tables exist
        print("\n" + "="*70)
        print("VERIFYING TABLES")
        print("="*70)
        
        verify_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('chat_conversations', 'alerts')
        ORDER BY table_name;
        """
        
        result = conn.execute(text(verify_query))
        tables = [row[0] for row in result]
        
        print("\nFound tables:")
        for table in tables:
            print(f"  ✓ {table}")
        
        if len(tables) == 2:
            print("\n✅ All tables created successfully!")
        else:
            print(f"\n⚠️  Warning: Expected 2 tables, found {len(tables)}")
        
        print("="*70)


if __name__ == "__main__":
    try:
        create_tables()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()