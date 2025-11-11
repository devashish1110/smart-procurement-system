"""
RAG Pipeline with FAISS Vector Store
File: backend/ai/rag_pipeline.py
"""

import faiss
import numpy as np
from typing import List, Dict, Tuple
import logging
from sqlalchemy.orm import Session

from backend.ai.embeddings import get_embedding_generator
from backend.models.database import Medicine, InventoryStock, Vendor, PurchaseOrder
from backend.config.database import get_db_context

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Retrieval-Augmented Generation Pipeline"""
    
    def __init__(self):
        """Initialize RAG pipeline with FAISS index"""
        self.embedding_generator = get_embedding_generator()
        self.dimension = self.embedding_generator.embedding_dimension
        
        # FAISS index for vector search
        self.index = None
        self.documents = []
        self.metadata = []
        
        logger.info("✓ RAG Pipeline initialized")
    
    def build_knowledge_base(self, db: Session):
        """
        Build knowledge base from database.
        Creates embeddings for medicines, inventory, and vendors.
        
        Args:
            db: Database session
        """
        logger.info("Building knowledge base...")
        
        documents = []
        metadata = []
        
        # 1. Add medicines information
        medicines = db.query(Medicine).filter(Medicine.is_active == True).all()
        for med in medicines:
            doc = f"Medicine: {med.medicine_name}, Category: {med.category or 'N/A'}, Company: {med.company or 'N/A'}, MRP: ₹{med.mrp_per_unit or 0}, Reorder Level: {med.reorder_level}"
            documents.append(doc)
            metadata.append({
                "type": "medicine",
                "id": med.medicine_id,
                "name": med.medicine_name,
                "category": med.category
            })
        
        # 2. Add inventory information
        from sqlalchemy import func
        stock_summary = db.query(
            Medicine.medicine_name,
            Medicine.category,
            func.sum(InventoryStock.quantity_available).label('total_stock')
        ).join(
            InventoryStock, Medicine.medicine_id == InventoryStock.medicine_id
        ).group_by(
            Medicine.medicine_id, Medicine.medicine_name, Medicine.category
        ).all()
        
        for name, category, stock in stock_summary:
            doc = f"Stock: {name} ({category or 'N/A'}) has {int(stock or 0)} units in inventory"
            documents.append(doc)
            metadata.append({
                "type": "inventory",
                "medicine_name": name,
                "stock": int(stock or 0)
            })
        
        # 3. Add vendor information
        vendors = db.query(Vendor).filter(Vendor.is_active == True).all()
        for vendor in vendors:
            doc = f"Vendor: {vendor.vendor_name}, Contact: {vendor.contact_person or 'N/A'}, Phone: {vendor.phone or 'N/A'}, Rating: {vendor.rating or 0}/5, Lead Time: {vendor.lead_time_days or 0} days"
            documents.append(doc)
            metadata.append({
                "type": "vendor",
                "id": vendor.vendor_id,
                "name": vendor.vendor_name,
                "rating": vendor.rating
            })
        
        # 4. Add common queries and answers
        faq_data = [
            ("How to check low stock medicines?", "You can view low stock medicines through inventory alerts. Medicines below reorder level are flagged."),
            ("How to create purchase order?", "To create a purchase order, select vendor, add medicines with quantities, and submit for approval."),
            ("How to check expiring medicines?", "Check inventory alerts for medicines expiring within 30-90 days."),
            ("How to add new patient?", "Register new patient with unique ID, name, contact details, and medical history."),
            ("How to generate bill?", "Create bill by selecting patient, adding consultation/medicine/treatment charges, and processing payment."),
        ]
        
        for query, answer in faq_data:
            doc = f"Q: {query} A: {answer}"
            documents.append(doc)
            metadata.append({
                "type": "faq",
                "query": query,
                "answer": answer
            })
        
        # Generate embeddings
        if not documents:
            logger.warning("No documents to index")
            return
        
        logger.info(f"Generating embeddings for {len(documents)} documents...")
        embeddings = self.embedding_generator.generate_embeddings(documents)
        
        # Create FAISS index
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings.astype('float32'))
        
        self.documents = documents
        self.metadata = metadata
        
        logger.info(f"✓ Knowledge base built with {len(documents)} documents")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of relevant documents with metadata
        """
        if self.index is None or len(self.documents) == 0:
            logger.warning("Knowledge base not built. Building now...")
            with get_db_context() as db:
                self.build_knowledge_base(db)
        
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        
        # Search in FAISS index
        distances, indices = self.index.search(query_embedding, min(top_k, len(self.documents)))
        
        # Prepare results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents):
                results.append({
                    "document": self.documents[idx],
                    "metadata": self.metadata[idx],
                    "score": float(1 / (1 + dist))  # Convert distance to similarity score
                })
        
        return results
    
    def get_context(self, query: str, top_k: int = 3) -> str:
        """
        Get relevant context for a query.
        
        Args:
            query: User query
            top_k: Number of context documents
            
        Returns:
            Concatenated context string
        """
        results = self.search(query, top_k)
        
        if not results:
            return "No relevant context found."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Context {i}] {result['document']}")
        
        return "\n".join(context_parts)


# Global RAG instance
_rag_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create global RAG pipeline instance"""
    global _rag_pipeline
    
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
        # Build knowledge base on first access
        with get_db_context() as db:
            _rag_pipeline.build_knowledge_base(db)
    
    return _rag_pipeline


def rebuild_knowledge_base():
    """Rebuild knowledge base (call after database updates)"""
    global _rag_pipeline
    
    if _rag_pipeline is not None:
        with get_db_context() as db:
            _rag_pipeline.build_knowledge_base(db)
        logger.info("✓ Knowledge base rebuilt") 