"""
API Routes Package
"""

from . import (
    auth, users, patients, medicines, inventory, 
    vendors, procurement, appointments, billing, reports, chatbot
)

__all__ = [
    "auth", "users", "patients", "medicines", "inventory",
    "vendors", "procurement", "appointments", "billing", "reports", "chatbot"
]