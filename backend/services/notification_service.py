"""
Notification Service for Alerts
File: backend/services/notification_service.py
"""

from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import List
import logging

from backend.models.database import Alert, InventoryStock, Medicine, User
from backend.config.database import get_db_context

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for creating and managing system notifications"""
    
    @staticmethod
    def create_alert(
        alert_type: str,
        title: str,
        message: str,
        severity: str,
        target_user_id: int = None,
        db: Session = None
    ) -> Alert:
        """
        Create a new alert.
        
        Args:
            alert_type: Type of alert (low_stock, expiry, payment_due, etc.)
            title: Alert title
            message: Alert message
            severity: Severity level (info, warning, critical)
            target_user_id: Target user ID (optional, None = broadcast)
            db: Database session
            
        Returns:
            Created Alert object
        """
        alert = Alert(
            alert_type=alert_type,
            title=title,
            message=message,
            severity=severity,
            target_user_id=target_user_id,
            is_read=False
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        logger.info(f"Alert created: {alert_type} - {title}")
        return alert
    
    @staticmethod
    def check_inventory_alerts(db: Session) -> List[Alert]:
        """
        Check inventory and create alerts for low stock and expiring items.
        
        Args:
            db: Database session
            
        Returns:
            List of created alerts
        """
        alerts = []
        today = date.today()
        
        # Check low stock items
        from sqlalchemy import func
        
        low_stock_medicines = db.query(
            Medicine.medicine_id,
            Medicine.medicine_name,
            Medicine.reorder_level,
            func.sum(InventoryStock.quantity_available).label('total_stock')
        ).join(
            InventoryStock, Medicine.medicine_id == InventoryStock.medicine_id
        ).filter(
            Medicine.is_active == True
        ).group_by(
            Medicine.medicine_id,
            Medicine.medicine_name,
            Medicine.reorder_level
        ).having(
            func.sum(InventoryStock.quantity_available) <= Medicine.reorder_level
        ).all()
        
        for med_id, name, reorder, stock in low_stock_medicines:
            # Check if alert already exists for today
            existing = db.query(Alert).filter(
                Alert.alert_type == 'low_stock',
                Alert.message.contains(name),
                Alert.created_at >= today
            ).first()
            
            if not existing:
                alert = NotificationService.create_alert(
                    alert_type='low_stock',
                    title=f'Low Stock Alert: {name}',
                    message=f'{name} is running low. Current stock: {int(stock or 0)}, Reorder level: {reorder}. Please create a purchase order.',
                    severity='warning',
                    db=db
                )
                alerts.append(alert)
        
        # Check expiring items (within 30 days)
        expiry_threshold = today + timedelta(days=30)
        
        expiring_items = db.query(
            InventoryStock,
            Medicine.medicine_name
        ).join(
            Medicine, InventoryStock.medicine_id == Medicine.medicine_id
        ).filter(
            InventoryStock.expiry_date <= expiry_threshold,
            InventoryStock.expiry_date >= today,
            InventoryStock.quantity_available > 0,
            InventoryStock.alert_sent == False
        ).all()
        
        for stock, med_name in expiring_items:
            days_left = (stock.expiry_date - today).days
            
            severity = 'critical' if days_left <= 7 else 'warning'
            
            alert = NotificationService.create_alert(
                alert_type='expiry',
                title=f'Expiry Alert: {med_name}',
                message=f'{med_name} (Batch: {stock.batch_number}) will expire in {days_left} days. Quantity: {stock.quantity_available}. Consider marking down or using first.',
                severity=severity,
                db=db
            )
            alerts.append(alert)
            
            # Mark alert as sent
            stock.alert_sent = True
        
        db.commit()
        
        logger.info(f"Created {len(alerts)} inventory alerts")
        return alerts
    
    @staticmethod
    def get_user_alerts(
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        db: Session = None
    ) -> List[Alert]:
        """
        Get alerts for a specific user.
        
        Args:
            user_id: User ID
            unread_only: Only return unread alerts
            limit: Maximum number of alerts
            db: Database session
            
        Returns:
            List of Alert objects
        """
        query = db.query(Alert).filter(
            (Alert.target_user_id == user_id) | (Alert.target_user_id == None)
        )
        
        if unread_only:
            query = query.filter(Alert.is_read == False)
        
        alerts = query.order_by(
            Alert.created_at.desc()
        ).limit(limit).all()
        
        return alerts
    
    @staticmethod
    def mark_alert_read(alert_id: int, db: Session) -> bool:
        """
        Mark an alert as read.
        
        Args:
            alert_id: Alert ID
            db: Database session
            
        Returns:
            True if successful, False otherwise
        """
        alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
        
        if alert:
            alert.is_read = True
            alert.read_at = datetime.now()
            db.commit()
            return True
        
        return False


def run_scheduled_alerts():
    """
    Run scheduled alert checks.
    This should be called by a scheduler (e.g., cron job, celery task)
    """
    try:
        with get_db_context() as db:
            service = NotificationService()
            alerts = service.check_inventory_alerts(db)
            logger.info(f"Scheduled alerts check completed: {len(alerts)} alerts created")
    except Exception as e:
        logger.error(f"Error running scheduled alerts: {e}", exc_info=True)