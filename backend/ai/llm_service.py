"""
Groq LLM Service Integration
File: backend/ai/llm_service.py
"""

from groq import Groq
from typing import List, Dict, Optional
import logging
import os

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Groq LLM Service for generating responses"""
    
    def __init__(self):
        """Initialize Groq client"""
        try:
            self.client = Groq(api_key=settings.GROQ_API_KEY)
            self.model = settings.MODEL_NAME
            logger.info(f"✓ Groq LLM initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            raise
    
    def generate_response(
        self,
        user_message: str,
        context: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate response using Groq LLM.
        
        Args:
            user_message: User's message
            context: RAG context (optional)
            conversation_history: Previous messages (optional)
            system_prompt: Custom system prompt (optional)
            
        Returns:
            Generated response text
        """
        try:
            # Build messages
            messages = []
            
            # System prompt
            if system_prompt is None:
                system_prompt = self._get_default_system_prompt()
            
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history[-5:])  # Keep last 5 messages
            
            # Add context if provided
            if context:
                messages.append({
                    "role": "system",
                    "content": f"Relevant context:\n{context}"
                })
            
            # Add user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                top_p=0.9
            )
            
            generated_text = response.choices[0].message.content
            
            logger.info(f"Generated response for query: {user_message[:50]}...")
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I encountered an error processing your request. Please try again."
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for the chatbot"""
        return """You are an AI assistant for a Smart Procurement System used in Ayurvedic clinics. 

Your role:
- Help with inventory management queries
- Assist with procurement and purchase orders
- Provide information about medicines, vendors, and stock levels
- Help with billing and financial queries
- Guide users through clinic operations

Guidelines:
- Be helpful, professional, and concise
- Use the provided context to give accurate information
- If you don't have enough information, say so clearly
- For sensitive operations (approvals, financial data), remind users of required permissions
- Use Indian Rupees (₹) for currency
- Be aware this is an Ayurvedic clinic context

Response format:
- Keep responses clear and actionable
- Use bullet points for lists
- Provide specific numbers/data when available
- Suggest next steps when relevant"""
    
    def classify_intent(self, user_message: str) -> Dict[str, any]:
        """
        Classify user intent.
        
        Args:
            user_message: User's message
            
        Returns:
            Dictionary with intent and confidence
        """
        try:
            prompt = f"""Classify the following user query into one of these categories:
- inventory_query: Questions about stock, medicines availability
- procurement: Purchase orders, vendor queries
- patient: Patient management queries
- billing: Bill generation, payment queries
- reports: Reports and analytics queries
- general: General questions or greetings

User query: "{user_message}"

Respond with JSON format: {{"intent": "category", "confidence": 0.0-1.0}}"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100
            )
            
            import json
            result_text = response.choices[0].message.content
            
            # Try to extract JSON
            try:
                # Find JSON in response
                start = result_text.find('{')
                end = result_text.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = result_text[start:end]
                    result = json.loads(json_str)
                    return result
            except:
                pass
            
            # Fallback: simple keyword matching
            message_lower = user_message.lower()
            
            if any(word in message_lower for word in ['stock', 'inventory', 'medicine', 'available', 'expiry']):
                return {"intent": "inventory_query", "confidence": 0.7}
            elif any(word in message_lower for word in ['order', 'purchase', 'vendor', 'buy', 'procurement']):
                return {"intent": "procurement", "confidence": 0.7}
            elif any(word in message_lower for word in ['patient', 'appointment', 'visit']):
                return {"intent": "patient", "confidence": 0.7}
            elif any(word in message_lower for word in ['bill', 'payment', 'invoice', 'receipt']):
                return {"intent": "billing", "confidence": 0.7}
            elif any(word in message_lower for word in ['report', 'analytics', 'statistics', 'summary']):
                return {"intent": "reports", "confidence": 0.7}
            else:
                return {"intent": "general", "confidence": 0.5}
                
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return {"intent": "general", "confidence": 0.3}



class MockLLMService(LLMService):
    """Simple mock LLM used for demos when external API is unavailable."""

    def __init__(self):
        # Do not call super().__init__ which initializes the real client
        self.model = os.getenv('MODEL_NAME', 'mock-model')

    def generate_response(self, user_message: str, context: Optional[str] = None, conversation_history: Optional[List[Dict]] = None, system_prompt: Optional[str] = None) -> str:
        # Return a deterministic, friendly mock response
        base = "Hello! I'm a demo assistant for the Smart Procurement System."
        if 'inventory' in user_message.lower():
            return base + " I can help with inventory queries — e.g., tell me which medicine or vendor details you need."
        if 'order' in user_message.lower() or 'purchase' in user_message.lower():
            return base + " I can help create or track purchase orders."
        return base + " How can I help you today?"



# Global LLM service instance
_llm_service = None


def get_llm_service() -> LLMService:
    """Get or create global LLM service instance"""
    global _llm_service
    # Allow using a mock LLM during demos or when external API access is blocked
    use_mock = os.getenv('USE_MOCK_LLM', 'false').lower() == 'true' or getattr(settings, 'USE_MOCK_LLM', False)

    if _llm_service is None:
        if use_mock:
            logger.info('Using MockLLMService (USE_MOCK_LLM=true)')
            _llm_service = MockLLMService()
        else:
            _llm_service = LLMService()
    
    return _llm_service