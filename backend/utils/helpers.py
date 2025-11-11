"""
Utility Helper Functions
File: backend/utils/helpers.py
"""

from datetime import datetime, date, timedelta
from typing import Any, Dict, List
import re


def format_currency(amount: float) -> str:
    """
    Format amount as Indian currency.
    
    Args:
        amount: Amount to format
        
    Returns:
        Formatted currency string (e.g., ₹1,234.56)
    """
    return f"₹{amount:,.2f}"


def parse_date(date_string: str) -> date:
    """
    Parse date string in multiple formats.
    
    Args:
        date_string: Date string
        
    Returns:
        date object
    """
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt).date()
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse date: {date_string}")


def get_date_range(period: str) -> tuple:
    """
    Get start and end dates for a period.
    
    Args:
        period: Period string (today, week, month, year)
        
    Returns:
        Tuple of (start_date, end_date)
    """
    today = date.today()
    
    if period == "today":
        return (today, today)
    elif period == "week":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        return (start, end)
    elif period == "month":
        start = date(today.year, today.month, 1)
        if today.month == 12:
            end = date(today.year, 12, 31)
        else:
            end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        return (start, end)
    elif period == "year":
        start = date(today.year, 1, 1)
        end = date(today.year, 12, 31)
        return (start, end)
    else:
        return (today, today)


def sanitize_string(text: str) -> str:
    """
    Sanitize string for safe use.
    
    Args:
        text: Input text
        
    Returns:
        Sanitized text
    """
    # Remove any potentially harmful characters
    sanitized = re.sub(r'[<>"\';]', '', text)
    return sanitized.strip()


def calculate_percentage(part: float, whole: float) -> float:
    """
    Calculate percentage.
    
    Args:
        part: Part value
        whole: Whole value
        
    Returns:
        Percentage (0-100)
    """
    if whole == 0:
        return 0.0
    return round((part / whole) * 100, 2)


def paginate_list(items: List[Any], page: int, per_page: int) -> Dict:
    """
    Paginate a list.
    
    Args:
        items: List of items
        page: Page number (1-indexed)
        per_page: Items per page
        
    Returns:
        Dictionary with paginated data
    """
    total_items = len(items)
    total_pages = (total_items + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        "items": items[start:end],
        "page": page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages
    }


def generate_bill_number(year: int, sequence: int) -> str:
    """
    Generate bill number.
    
    Args:
        year: Year
        sequence: Sequence number
        
    Returns:
        Bill number (e.g., BILL202400001)
    """
    return f"BILL{year}{sequence:05d}"


def generate_po_number(year: int, sequence: int) -> str:
    """
    Generate purchase order number.
    
    Args:
        year: Year
        sequence: Sequence number
        
    Returns:
        PO number (e.g., PO202400001)
    """
    return f"PO{year}{sequence:04d}"


def validate_phone(phone: str) -> bool:
    """
    Validate Indian phone number.
    
    Args:
        phone: Phone number string
        
    Returns:
        True if valid, False otherwise
    """
    # Indian phone pattern: +91xxxxxxxxxx or xxxxxxxxxx
    pattern = r'^(\+91)?[6-9]\d{9}$'
    return bool(re.match(pattern, phone.replace(' ', '').replace('-', '')))


def validate_email(email: str) -> bool:
    """
    Validate email address.
    
    Args:
        email: Email address
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def truncate_text(text: str, length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length.
    
    Args:
        text: Input text
        length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix


def get_financial_year(date_obj: date = None) -> str:
    """
    Get financial year for a date.
    Financial year in India: April to March
    
    Args:
        date_obj: Date object (default: today)
        
    Returns:
        Financial year string (e.g., "FY2024-25")
    """
    if date_obj is None:
        date_obj = date.today()
    
    if date_obj.month >= 4:
        start_year = date_obj.year
        end_year = date_obj.year + 1
    else:
        start_year = date_obj.year - 1
        end_year = date_obj.year
    
    return f"FY{start_year}-{str(end_year)[2:]}"