from typing import Dict, List, Optional
from datetime import datetime
from .models import User, UserRole, UserCreateRequest
from .jwt_handler import get_password_hash, verify_password

# In-memory user storage (replace with database in production)
users_db: Dict[str, User] = {}

# Default admin user
DEFAULT_ADMIN = User(
    user_id="admin-001",
    username="admin",
    email="admin@pharma-forecasting.com",
    role=UserRole.ADMIN,
    brand_access=["*"],
    geo_access=["*"],
    is_active=True
)

# Initialize with default admin
users_db["admin-001"] = DEFAULT_ADMIN


def create_user(user_data: UserCreateRequest) -> User:
    """Create a new user."""
    user_id = f"user-{len(users_db) + 1:03d}"
    
    user = User(
        user_id=user_id,
        username=user_data.username,
        email=user_data.email,
        role=user_data.role,
        brand_access=user_data.brand_access,
        geo_access=user_data.geo_access,
        password_hash=get_password_hash(user_data.password)
    )
    
    users_db[user_id] = user
    return user


def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID."""
    return users_db.get(user_id)


def get_user_by_username(username: str) -> Optional[User]:
    """Get user by username."""
    for user in users_db.values():
        if user.username == username:
            return user
    return None


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password."""
    user = get_user_by_username(username)
    if not user:
        return None
    
    # Check if user has password_hash (for new users) or use default password
    if hasattr(user, 'password_hash'):
        if not verify_password(password, user.password_hash):
            return None
    else:
        # Default password for demo users
        if password != "password":
            return None
    
    return user


def update_user_last_login(user_id: str):
    """Update user's last login timestamp."""
    user = users_db.get(user_id)
    if user:
        user.last_login = datetime.utcnow()


def get_users_by_role(role: UserRole) -> List[User]:
    """Get all users with a specific role."""
    return [user for user in users_db.values() if user.role == role]


def update_user_access(user_id: str, brand_access: List[str] = None, geo_access: List[str] = None):
    """Update user's brand or geo access."""
    user = users_db.get(user_id)
    if user:
        if brand_access is not None:
            user.brand_access = brand_access
        if geo_access is not None:
            user.geo_access = geo_access


def check_brand_access(user: User, brand_id: str) -> bool:
    """Check if user has access to a specific brand."""
    if "*" in user.brand_access:
        return True
    return brand_id in user.brand_access


def check_geo_access(user: User, geo_id: str) -> bool:
    """Check if user has access to a specific geography."""
    if "*" in user.geo_access:
        return True
    return geo_id in user.geo_access
