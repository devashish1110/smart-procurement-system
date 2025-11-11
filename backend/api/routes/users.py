"""
User Management API Routes
File: backend/api/routes/users.py
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.config.database import get_db
from backend.models.database import User
from backend.schemas.schemas import UserResponse, UserUpdate
from backend.auth.security import get_current_user, require_admin


router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get all users (Admin only).
    
    **Query Parameters:**
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    
    **Returns:**
    - List of all users
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserResponse.from_orm(user) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get specific user by ID (Admin only).
    
    **Path Parameters:**
    - user_id: ID of the user to retrieve
    
    **Returns:**
    - User information
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return UserResponse.from_orm(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update user information (Admin only).
    
    **Path Parameters:**
    - user_id: ID of the user to update
    
    **Request Body:**
    - full_name: Updated full name (optional)
    - email: Updated email (optional)
    - phone: Updated phone (optional)
    - is_active: Updated active status (optional)
    
    **Returns:**
    - Updated user information
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Update fields if provided
    update_data = user_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return UserResponse.from_orm(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete user (Admin only).
    Soft delete - sets is_active to False.
    
    **Path Parameters:**
    - user_id: ID of the user to delete
    
    **Returns:**
    - Success message
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Prevent deleting yourself
    if user.user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Soft delete
    user.is_active = False
    db.commit()
    
    return {"message": f"User {user.username} deactivated successfully"}


@router.get("/role/{role}", response_model=List[UserResponse])
async def get_users_by_role(
    role: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all users with a specific role.
    
    **Path Parameters:**
    - role: Role to filter by (admin, doctor, pharmacist, receptionist, therapist)
    
    **Returns:**
    - List of users with the specified role
    """
    users = db.query(User).filter(
        User.role == role,
        User.is_active == True
    ).all()
    
    return [UserResponse.from_orm(user) for user in users]