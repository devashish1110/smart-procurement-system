"""
Shared API Dependencies
File: backend/api/dependencies.py
"""

from fastapi import Header, HTTPException, status
from typing import Optional


async def get_api_key(x_api_key: Optional[str] = Header(None)):
    """
    Validate API key for external integrations (if needed in future).
    Currently not enforced - for future use.
    """
    # For now, we're using JWT tokens, so this is optional
    # Can be implemented later for third-party integrations
    return x_api_key


async def common_parameters(
    skip: int = 0,
    limit: int = 100
):
    """
    Common pagination parameters.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        Dictionary with skip and limit
    """
    if skip < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skip parameter must be non-negative"
        )
    
    if limit < 1 or limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 1000"
        )
    
    return {"skip": skip, "limit": limit}