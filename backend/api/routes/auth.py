"""
Authentication API Routes
File: backend/api/routes/auth.py
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from backend.config.database import get_db
from backend.config.settings import settings
from backend.models.database import User
from backend.schemas.schemas import (
    UserLogin, Token, UserResponse, UserWithToken, 
    UserCreate, UserRole
)
from backend.auth.security import (
    authenticate_user, create_access_token, 
    get_password_hash, get_current_user,
    require_admin
)


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=UserWithToken)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint - authenticate user and return JWT token.
    
    **Request Body:**
    - username: User's username
    - password: User's password
    
    **Returns:**
    - access_token: JWT token for authentication
    - token_type: Type of token (bearer)
    - user: User information
    
    **Example:**
    ```
    POST /api/v1/auth/login
    {
        "username": "admin",
        "password": "admin123"
    }
    ```
    """
    # Authenticate user
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.user_id,
            "role": user.role
        },
        expires_delta=access_token_expires
    )
    
    # Return token and user info
    return UserWithToken(
        user=UserResponse.from_orm(user),
        access_token=access_token,
        token_type="bearer"
    )


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Register new user (Admin only).
    
    **Request Body:**
    - username: Unique username
    - password: Password (min 6 characters)
    - full_name: Full name of user
    - role: User role (admin, doctor, pharmacist, receptionist, therapist)
    - email: Email address (optional)
    - phone: Phone number (optional)
    
    **Returns:**
    - User information (without password)
    
    **Note:** Only admins can create new users
    """
    # Check if username already exists
    existing_user = db.query(User).filter(
        User.username == user_data.username
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists (if provided)
    if user_data.email:
        existing_email = db.query(User).filter(
            User.email == user_data.email
        ).first()
        
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create new user
    new_user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        email=user_data.email,
        phone=user_data.phone,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse.from_orm(new_user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's information.
    
    **Returns:**
    - Current user's profile information
    
    **Example:**
    ```
    GET /api/v1/auth/me
    Headers: Authorization: Bearer <token>
    ```
    """
    return UserResponse.from_orm(current_user)


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password.
    
    **Request Body:**
    - old_password: Current password
    - new_password: New password (min 6 characters)
    
    **Returns:**
    - Success message
    """
    from backend.auth.security import verify_password
    
    # Verify old password
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    # Validate new password
    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long"
        )
    
    # Update password
    current_user.password_hash = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout endpoint (for future use with token blacklisting).
    Currently, logout is handled client-side by removing the token.
    
    **Returns:**
    - Success message
    """
    # In a production system, you would:
    # 1. Add token to blacklist in Redis
    # 2. Invalidate refresh tokens
    # For now, client should just remove the token
    
    return {"message": "Logged out successfully"}