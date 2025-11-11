"""
Seed Sample Chat Conversations
File: scripts/seed_chat_data.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from dotenv import load_dotenv
import random

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def seed_sample_conversations():
    """Seed sample chat conversations for testing"""
    
    engine = create_engine(DATABASE_URL)
    
    print("="*70)
    print("SEEDING SAMPLE CHAT CONVERSATIONS")
    print("="*70)
    
    # Sample conversations for different intents
    sample_conversations = [
        # Inventory queries
        {
            "message": "What medicines are low in stock?",
            "response": "Based on current inventory, the following medicines are low in stock:\n\n• Triphala Churna - 8 units (reorder level: 10)\n• Ashwagandha Capsules - 5 units (reorder level: 10)\n• Brahmi Oil - 3 units (reorder level: 10)\n\nI recommend creating purchase orders for these items.",
            "intent": "inventory_query",
            "confidence": 0.95
        },
        {
            "message": "Show me medicines expiring in next 30 days",
            "response": "Here are medicines expiring within 30 days:\n\n• Amla Juice (Batch: BATCH2024101) - expires in 15 days (50 units)\n• Kumari Asava (Batch: BATCH2024089) - expires in 22 days (30 units)\n• Chyawanprash (Batch: BATCH2024075) - expires in 28 days (20 units)\n\nConsider prioritizing these for dispensing.",
            "intent": "inventory_query",
            "confidence": 0.92
        },
        {
            "message": "Check stock for Triphala",
            "response": "Triphala inventory status:\n\n• Total stock: 45 units\n• Available batches: 3\n• Nearest expiry: 90 days\n• Reorder level: 10 units\n\nStock is adequate. No immediate action needed.",
            "intent": "inventory_query",
            "confidence": 0.88
        },
        
        # Procurement queries
        {
            "message": "How do I create a purchase order?",
            "response": "To create a purchase order:\n\n1. Select a vendor from the vendor list\n2. Add medicines with quantities and unit prices\n3. Review the total amount\n4. Submit for approval (if you're pharmacist)\n5. Doctor will approve the order\n6. Once approved, mark as 'ordered' and send to vendor\n\nYou can also use the procurement API endpoint to create POs programmatically.",
            "intent": "procurement",
            "confidence": 0.94
        },
        {
            "message": "List all active vendors",
            "response": "Active vendors in the system:\n\n1. Vaidyaratnam Ayurveda - Rating: 4.5/5, Lead time: 7 days\n2. Ayurved Pratishthan - Rating: 4.2/5, Lead time: 5 days\n3. Dhootpapeshwar - Rating: 4.7/5, Lead time: 10 days\n4. Baidyanath - Rating: 4.3/5, Lead time: 7 days\n5. Himalaya Wellness - Rating: 4.6/5, Lead time: 5 days\n\nAll vendors are verified and have good ratings.",
            "intent": "procurement",
            "confidence": 0.91
        },
        {
            "message": "Show pending purchase orders",
            "response": "Current pending purchase orders:\n\n• PO202400045 - Vendor: Vaidyaratnam, Amount: ₹15,450, Status: Approved\n• PO202400047 - Vendor: Himalaya, Amount: ₹8,200, Status: Ordered\n• PO202400049 - Vendor: Baidyanath, Amount: ₹12,800, Status: Approved\n\nTotal pending value: ₹36,450",
            "intent": "procurement",
            "confidence": 0.89
        },
        
        # Patient queries
        {
            "message": "How many appointments today?",
            "response": "Today's appointments summary:\n\n• Total appointments: 12\n• Morning slot: 7 appointments\n• Evening slot: 5 appointments\n• Completed: 8\n• Pending: 4\n\nNext appointment is at 3:00 PM with patient Rajesh Kumar.",
            "intent": "patient",
            "confidence": 0.93
        },
        {
            "message": "Add new patient procedure",
            "response": "To add a new patient:\n\n1. Go to Patient Management section\n2. Click 'Add New Patient'\n3. Enter required details:\n   - Unique Patient ID\n   - Full Name\n   - Gender\n   - Contact (phone/email)\n   - Date of Birth\n   - Address\n4. Save the record\n\nThe patient will be immediately available for appointments and billing.",
            "intent": "patient",
            "confidence": 0.90
        },
        
        # Billing queries
        {
            "message": "What was today's revenue?",
            "response": "Today's revenue summary:\n\n• Total bills: 15\n• Total revenue: ₹45,230\n• Consultation charges: ₹12,500\n• Medicine sales: ₹22,180\n• Treatment charges: ₹10,550\n• Payments collected: ₹43,500\n• Outstanding: ₹1,730\n\nRevenue is 15% higher than yesterday.",
            "intent": "billing",
            "confidence": 0.94
        },
        {
            "message": "Show unpaid bills",
            "response": "Bills with outstanding balance:\n\n• BILL202400234 - Patient: Amit Sharma, Balance: ₹850\n• BILL202400241 - Patient: Priya Patel, Balance: ₹1,200\n• BILL202400248 - Patient: Vikram Singh, Balance: ₹450\n\nTotal outstanding: ₹2,500\n\nConsider sending payment reminders to these patients.",
            "intent": "billing",
            "confidence": 0.87
        },
        
        # Reports queries
        {
            "message": "Show me monthly financial summary",
            "response": "Monthly financial summary (November 2024):\n\n**Revenue:**\n• Total: ₹4,25,680\n• Consultations: ₹1,45,200 (34%)\n• Medicines: ₹1,98,450 (47%)\n• Treatments: ₹82,030 (19%)\n\n**Expenses:**\n• Procurement: ₹2,15,340\n• Gross Profit: ₹2,10,340\n• Profit Margin: 49.4%\n\n**Growth:**\n• Revenue up 12% vs last month\n• Patient visits up 8%",
            "intent": "reports",
            "confidence": 0.96
        },
        {
            "message": "Give me inventory statistics",
            "response": "Inventory statistics:\n\n• Total medicines: 198\n• Total stock value: ₹3,45,670\n• Low stock items: 8\n• Expiring in 30 days: 5\n• Expired items: 2 (disposal needed)\n\n**Top categories:**\n1. Tablets: 45 items\n2. Oils: 38 items\n3. Choorna: 32 items\n4. Kashaya: 28 items\n\nInventory health: 92% (Good)",
            "intent": "reports",
            "confidence": 0.91
        },
        
        # General queries
        {
            "message": "Hello, how can you help me?",
            "response": "Hello! I'm your AI assistant for the Smart Procurement System. I can help you with:\n\n📦 Inventory Management - Check stock, expiry dates\n🛒 Procurement - Create POs, manage vendors\n👥 Patient Management - Appointments, records\n💰 Billing & Payments - Generate bills, track revenue\n📊 Reports & Analytics - Financial reports, statistics\n\nJust ask me anything about clinic operations!",
            "intent": "general",
            "confidence": 0.85
        },
        {
            "message": "What are your capabilities?",
            "response": "I can assist with various clinic management tasks:\n\n**Inventory:** Track stock levels, monitor expiry dates, identify shortages\n**Procurement:** Help create purchase orders, recommend vendors, track deliveries\n**Patients:** View appointments, search patient records, schedule visits\n**Billing:** Generate invoices, track payments, analyze revenue\n**Reports:** Provide insights, statistics, and financial summaries\n\nI use AI to understand your queries and provide accurate information from the database. How can I help you today?",
            "intent": "general",
            "confidence": 0.88
        }
    ]
    
    with engine.connect() as conn:
        # Get user IDs
        result = conn.execute(text("SELECT user_id, username FROM users WHERE is_active = true"))
        users = list(result)
        
        if not users:
            print("❌ No active users found. Please run data_pipeline.py first.")
            return
        
        print(f"\nFound {len(users)} active users")
        
        # Create sessions for different users
        sessions = []
        for i in range(3):  # Create 3 different sessions
            user_id, username = random.choice(users)
            session_id = f"session_{user_id}_{i+1}"
            sessions.append((session_id, user_id, username))
        
        print(f"\nCreating conversations for {len(sessions)} sessions...")
        
        total_inserted = 0
        
        for session_id, user_id, username in sessions:
            # Randomly select 4-6 conversations per session
            num_convos = random.randint(4, 6)
            selected_convos = random.sample(sample_conversations, num_convos)
            
            print(f"\n  Session: {session_id} (User: {username})")
            
            for i, convo in enumerate(selected_convos):
                # Create timestamp (spread over last 7 days)
                days_ago = random.randint(0, 7)
                hours_ago = random.randint(0, 23)
                created_at = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
                
                insert_query = """
                INSERT INTO chat_conversations 
                (session_id, user_id, message, response, intent, confidence, created_at)
                VALUES (:session_id, :user_id, :message, :response, :intent, :confidence, :created_at)
                """
                
                conn.execute(text(insert_query), {
                    "session_id": session_id,
                    "user_id": user_id,
                    "message": convo["message"],
                    "response": convo["response"],
                    "intent": convo["intent"],
                    "confidence": convo["confidence"],
                    "created_at": created_at
                })
                
                total_inserted += 1
            
            conn.commit()
            print(f"    ✓ Added {num_convos} conversations")
        
        # Get total count
        result = conn.execute(text("SELECT COUNT(*) FROM chat_conversations"))
        total_count = result.fetchone()[0]
        
        print("\n" + "="*70)
        print(f"✅ Successfully seeded {total_inserted} sample conversations")
        print(f"   Total conversations in database: {total_count}")
        print("="*70)


def seed_sample_alerts():
    """Seed sample alerts"""
    
    engine = create_engine(DATABASE_URL)
    
    print("\n" + "="*70)
    print("SEEDING SAMPLE ALERTS")
    print("="*70)
    
    sample_alerts = [
        {
            "alert_type": "low_stock",
            "title": "Low Stock Alert: Triphala Churna",
            "message": "Triphala Churna is running low. Current stock: 8, Reorder level: 10. Please create a purchase order.",
            "severity": "warning"
        },
        {
            "alert_type": "low_stock",
            "title": "Low Stock Alert: Ashwagandha Capsules",
            "message": "Ashwagandha Capsules is running low. Current stock: 5, Reorder level: 10. Please create a purchase order.",
            "severity": "warning"
        },
        {
            "alert_type": "expiry",
            "title": "Expiry Alert: Amla Juice",
            "message": "Amla Juice (Batch: BATCH2024101) will expire in 15 days. Quantity: 50. Consider marking down or using first.",
            "severity": "critical"
        },
        {
            "alert_type": "expiry",
            "title": "Expiry Alert: Kumari Asava",
            "message": "Kumari Asava (Batch: BATCH2024089) will expire in 22 days. Quantity: 30. Consider marking down or using first.",
            "severity": "warning"
        },
        {
            "alert_type": "payment_due",
            "title": "Outstanding Payment Reminder",
            "message": "Patient Amit Sharma has an outstanding balance of ₹850 (Bill: BILL202400234). Consider sending payment reminder.",
            "severity": "info"
        }
    ]
    
    with engine.connect() as conn:
        inserted = 0
        
        for alert_data in sample_alerts:
            days_ago = random.randint(0, 3)
            created_at = datetime.now() - timedelta(days=days_ago)
            
            insert_query = """
            INSERT INTO alerts 
            (alert_type, title, message, severity, target_user_id, is_read, created_at)
            VALUES (:alert_type, :title, :message, :severity, NULL, :is_read, :created_at)
            """
            
            conn.execute(text(insert_query), {
                "alert_type": alert_data["alert_type"],
                "title": alert_data["title"],
                "message": alert_data["message"],
                "severity": alert_data["severity"],
                "is_read": random.choice([True, False]),
                "created_at": created_at
            })
            
            inserted += 1
        
        conn.commit()
        
        result = conn.execute(text("SELECT COUNT(*) FROM alerts"))
        total_count = result.fetchone()[0]
        
        print(f"\n✅ Successfully seeded {inserted} sample alerts")
        print(f"   Total alerts in database: {total_count}")
        print("="*70)


if __name__ == "__main__":
    try:
        seed_sample_conversations()
        seed_sample_alerts()
        print("\n🎉 All sample data seeded successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()