from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from .models import User, TokenData, UserRole

# JWT settings
SECRET_KEY = "your-secret-key-change-in-production"  # In production, use env var
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role")
        
        if user_id is None:
            return None
        
        return TokenData(user_id=user_id, username=username, role=role)
    except jwt.PyJWTError:
        return None


def check_permission(user_role: UserRole, resource: str, action: str, scope: str = "all") -> bool:
    """Check if a user role has permission for a resource/action/scope."""
    from .models import ROLE_PERMISSIONS
    
    permissions = ROLE_PERMISSIONS.get(user_role, [])
    
    for permission in permissions:
        # Check for wildcard permissions (admin)
        if permission.resource == "*" and permission.action == "*":
            return True
        
        # Check exact match
        if (permission.resource == resource or permission.resource == "*") and \
           (permission.action == action or permission.action == "*") and \
           (permission.scope == scope or permission.scope == "all"):
            return True
    
    return False
