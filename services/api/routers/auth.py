from fastapi import APIRouter, HTTPException, Depends, status
from datetime import timedelta
from typing import List

from auth.models import LoginRequest, UserCreateRequest, Token, User, UserRole
from auth.jwt_handler import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from auth.user_service import authenticate_user, create_user, get_users_by_role, update_user_access
from auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
def login(login_data: LoginRequest):
    """Authenticate user and return access token."""
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.user_id, "username": user.username, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.user_id,
        role=user.role.value
    )


@router.get("/me", response_model=User)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@router.post("/users", response_model=User)
def create_new_user(
    user_data: UserCreateRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Create a new user (admin only)."""
    # Check if username already exists
    from auth.user_service import get_user_by_username
    existing_user = get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    user = create_user(user_data)
    return user


@router.get("/users", response_model=List[User])
def list_users(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """List all users (admin only)."""
    from auth.user_service import users_db
    return list(users_db.values())


@router.get("/users/by-role/{role}", response_model=List[User])
def get_users_by_role_endpoint(
    role: UserRole,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Get users by role (admin only)."""
    return get_users_by_role(role)


@router.put("/users/{user_id}/access")
def update_user_access_endpoint(
    user_id: str,
    brand_access: List[str] = None,
    geo_access: List[str] = None,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Update user access permissions (admin only)."""
    from auth.user_service import get_user_by_id
    
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_user_access(user_id, brand_access, geo_access)
    return {"message": "User access updated successfully"}


@router.post("/refresh")
def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh access token."""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.user_id, "username": current_user.username, "role": current_user.role.value},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=current_user.user_id,
        role=current_user.role.value
    )
