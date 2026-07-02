"""
Main Chatbot Engine
File: backend/ai/chatbot_engine.py
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime
from sqlalchemy.orm import Session

import os
from backend.ai.llm_service import get_llm_service
from backend.models.database import ChatConversation, User
from backend.config.database import get_db_context

logger = logging.getLogger(__name__)


class ChatbotEngine:
    """Main chatbot engine coordinating LLM and RAG"""
    
    def __init__(self):
        """Initialize chatbot engine"""
        self.llm_service = get_llm_service()
        self.use_mock = os.getenv('USE_MOCK_LLM', 'false').lower() == 'true'
        if self.use_mock:
            # Skip torch/FAISS in mock mode — free-tier Render has only 512MB RAM
            # and loading sentence-transformers would OOM-kill the process.
            self.rag_pipeline = None
            logger.info("✓ Chatbot Engine initialized (mock mode, RAG disabled)")
        else:
            from backend.ai.rag_pipeline import get_rag_pipeline
            self.rag_pipeline = get_rag_pipeline()
            logger.info("✓ Chatbot Engine initialized")
    
    def process_message(
        self,
        user_message: str,
        user_id: int,
        session_id: str,
        db: Session
    ) -> Dict:
        """
        Process user message and generate response.
        
        Args:
            user_message: User's message
            user_id: ID of the user
            session_id: Conversation session ID
            db: Database session
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # 1. Classify intent
            intent_data = self.llm_service.classify_intent(user_message)
            intent = intent_data.get("intent", "general")
            confidence = intent_data.get("confidence", 0.5)
            
            logger.info(f"Intent classified: {intent} (confidence: {confidence})")
            
            # 2. Get relevant context
            if self.use_mock:
                context = self._get_db_context(intent, db)
            else:
                context = self.rag_pipeline.get_context(user_message, top_k=3)
            
            # 3. Get conversation history
            conversation_history = self._get_conversation_history(session_id, db)
            
            # 4. Get user info
            user = db.query(User).filter(User.user_id == user_id).first()
            user_role = user.role if user else "unknown"
            
            # 5. Build enhanced system prompt based on intent and role
            system_prompt = self._build_system_prompt(intent, user_role)
            
            # 6. Generate response using LLM
            response = self.llm_service.generate_response(
                user_message=user_message,
                context=context,
                conversation_history=conversation_history,
                system_prompt=system_prompt
            )
            
            # 7. Get suggested actions based on intent
            suggested_actions = self._get_suggested_actions(intent, user_role)
            
            # 8. Save conversation to database
            self._save_conversation(
                session_id=session_id,
                user_id=user_id,
                message=user_message,
                response=response,
                intent=intent,
                confidence=confidence,
                db=db
            )
            
            # 9. Return result
            return {
                "response": response,
                "session_id": session_id,
                "intent": intent,
                "confidence": confidence,
                "suggested_actions": suggested_actions,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "response": "I apologize, but I encountered an error. Please try again or contact support.",
                "session_id": session_id,
                "intent": "error",
                "confidence": 0.0,
                "suggested_actions": [],
                "timestamp": datetime.now()
            }
    
    def _get_db_context(self, intent: str, db: Session) -> str:
        """Query DB directly for live data — used in mock mode instead of RAG/torch."""
        from datetime import date, timedelta
        from backend.models.database import InventoryStock, Medicine, PurchaseOrder, Appointment, Bill, Patient
        try:
            if intent == "inventory_query":
                low = db.query(InventoryStock).filter(InventoryStock.status == 'low_stock').count()
                expiring = db.query(InventoryStock).filter(
                    InventoryStock.expiry_date <= date.today() + timedelta(days=30),
                    InventoryStock.expiry_date >= date.today(),
                    InventoryStock.quantity_available > 0
                ).count()
                total = db.query(Medicine).filter(Medicine.is_active == True).count()
                return f"{low} medicines are low in stock, {expiring} batches expiring within 30 days, {total} active medicines in catalog."
            elif intent == "procurement":
                pending = db.query(PurchaseOrder).filter(PurchaseOrder.status.in_(['approved', 'ordered'])).count()
                draft = db.query(PurchaseOrder).filter(PurchaseOrder.status == 'draft').count()
                return f"{pending} purchase orders pending (approved/ordered, awaiting delivery), {draft} in draft."
            elif intent == "patient":
                total = db.query(Patient).count()
                today = db.query(Appointment).filter(Appointment.appointment_date == date.today()).count()
                return f"{total} patients registered. {today} appointments scheduled for today."
            elif intent == "billing":
                today_bills = db.query(Bill).filter(Bill.bill_date == date.today()).all()
                month_bills = db.query(Bill).filter(Bill.bill_date >= date.today().replace(day=1)).all()
                return (f"Today: ₹{sum(b.total_amount or 0 for b in today_bills):.2f} from {len(today_bills)} bills. "
                        f"This month: ₹{sum(b.total_amount or 0 for b in month_bills):.2f} from {len(month_bills)} bills.")
            elif intent == "reports":
                month_bills = db.query(Bill).filter(Bill.bill_date >= date.today().replace(day=1)).all()
                low = db.query(InventoryStock).filter(InventoryStock.status == 'low_stock').count()
                pending = db.query(PurchaseOrder).filter(PurchaseOrder.status.in_(['approved', 'ordered'])).count()
                return (f"This month's revenue: ₹{sum(b.total_amount or 0 for b in month_bills):.2f}. "
                        f"Low stock items: {low}. Pending purchase orders: {pending}.")
            return ""
        except Exception as e:
            logger.error(f"DB context error: {e}")
            return ""

    def _get_conversation_history(
        self,
        session_id: str,
        db: Session,
        limit: int = 5
    ) -> List[Dict]:
        """Get recent conversation history"""
        conversations = db.query(ChatConversation).filter(
            ChatConversation.session_id == session_id
        ).order_by(
            ChatConversation.created_at.desc()
        ).limit(limit).all()
        
        history = []
        for conv in reversed(conversations):
            history.append({"role": "user", "content": conv.message})
            history.append({"role": "assistant", "content": conv.response})
        
        return history
    
    def _build_system_prompt(self, intent: str, user_role: str) -> str:
        """Build system prompt based on intent and user role"""
        base_prompt = """You are an AI assistant for a Smart Procurement System used in Ayurvedic clinics.

Your role is to help with:
- Inventory management queries
- Procurement and purchase orders
- Medicine information
- Vendor management
- Billing and payments
- Reports and analytics

User role: {role}
Current query type: {intent}

Guidelines:
- Be helpful, professional, and concise
- Use the provided context to give accurate information
- If you don't have enough information, say so clearly
- Use Indian Rupees (₹) for currency
- Provide actionable suggestions when possible
"""
        
        role_specific = {
            "doctor": "You're assisting a doctor. They can approve purchase orders and access all patient data.",
            "pharmacist": "You're assisting a pharmacist. They manage inventory and can create purchase orders.",
            "receptionist": "You're assisting a receptionist. They handle appointments and basic billing.",
            "therapist": "You're assisting a therapist. They work with patient treatments.",
            "admin": "You're assisting an admin. They have full system access."
        }
        
        intent_specific = {
            "inventory_query": "Focus on providing accurate stock levels, expiry information, and inventory status.",
            "procurement": "Help with vendor selection, purchase order creation, and procurement processes.",
            "patient": "Assist with patient information, appointments, and visit history.",
            "billing": "Help with bill generation, payment tracking, and financial queries.",
            "reports": "Provide data insights, statistics, and report summaries."
        }
        
        prompt = base_prompt.format(role=user_role, intent=intent)
        
        if user_role in role_specific:
            prompt += f"\n{role_specific[user_role]}"
        
        if intent in intent_specific:
            prompt += f"\n{intent_specific[intent]}"
        
        return prompt
    
    def _get_suggested_actions(self, intent: str, user_role: str) -> List[Dict]:
        """Get suggested actions based on intent"""
        actions = {
            "inventory_query": [
                {"label": "View Low Stock", "action": "view_low_stock"},
                {"label": "Check Expiring Items", "action": "view_expiring"},
                {"label": "Inventory Summary", "action": "inventory_stats"}
            ],
            "procurement": [
                {"label": "Create Purchase Order", "action": "create_po"},
                {"label": "View Vendors", "action": "view_vendors"},
                {"label": "Pending Orders", "action": "pending_orders"}
            ],
            "billing": [
                {"label": "Create Bill", "action": "create_bill"},
                {"label": "View Today's Bills", "action": "todays_bills"},
                {"label": "Outstanding Payments", "action": "outstanding"}
            ],
            "patient": [
                {"label": "Add Patient", "action": "add_patient"},
                {"label": "Today's Appointments", "action": "todays_appointments"},
                {"label": "Search Patient", "action": "search_patient"}
            ],
            "reports": [
                {"label": "Dashboard", "action": "dashboard"},
                {"label": "Financial Report", "action": "financial_report"},
                {"label": "Inventory Report", "action": "inventory_report"}
            ]
        }
        
        return actions.get(intent, [])
    
    def _save_conversation(
        self,
        session_id: str,
        user_id: int,
        message: str,
        response: str,
        intent: str,
        confidence: float,
        db: Session
    ):
        """Save conversation to database"""
        try:
            conversation = ChatConversation(
                session_id=session_id,
                user_id=user_id,
                message=message,
                response=response,
                intent=intent,
                confidence=confidence
            )
            
            db.add(conversation)
            db.commit()
            
            logger.info(f"Conversation saved for session: {session_id}")
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            db.rollback()


# Global chatbot instance
_chatbot_engine = None


def get_chatbot_engine() -> ChatbotEngine:
    """Get or create global chatbot engine instance"""
    global _chatbot_engine
    
    if _chatbot_engine is None:
        _chatbot_engine = ChatbotEngine()
    
    return _chatbot_engine