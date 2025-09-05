from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    DATA_SCIENTIST = "data_scientist"
    ANALYST = "analyst"
    VIEWER = "viewer"


class User(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="User email")
    role: UserRole = Field(..., description="User role")
    brand_access: List[str] = Field(default_factory=list, description="Brands user can access")
    geo_access: List[str] = Field(default_factory=list, description="Geographies user can access")
    is_active: bool = Field(default=True, description="Whether user is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    role: str


class TokenData(BaseModel):
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class UserCreateRequest(BaseModel):
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email")
    password: str = Field(..., description="Password")
    role: UserRole = Field(..., description="User role")
    brand_access: List[str] = Field(default_factory=list, description="Brands user can access")
    geo_access: List[str] = Field(default_factory=list, description="Geographies user can access")


class Permission(BaseModel):
    resource: str = Field(..., description="Resource (e.g., 'forecasts', 'runs', 'scenarios')")
    action: str = Field(..., description="Action (e.g., 'read', 'write', 'delete')")
    scope: str = Field(..., description="Scope (e.g., 'all', 'brand', 'geo')")


# Role-based permissions
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission(resource="*", action="*", scope="all")
    ],
    UserRole.DATA_SCIENTIST: [
        Permission(resource="forecasts", action="read", scope="all"),
        Permission(resource="forecasts", action="write", scope="all"),
        Permission(resource="runs", action="read", scope="all"),
        Permission(resource="runs", action="write", scope="all"),
        Permission(resource="backtest", action="read", scope="all"),
        Permission(resource="backtest", action="write", scope="all"),
        Permission(resource="scenarios", action="read", scope="all"),
        Permission(resource="scenarios", action="write", scope="all"),
        Permission(resource="dashboard", action="read", scope="all"),
        Permission(resource="models", action="read", scope="all"),
        Permission(resource="models", action="write", scope="all"),
    ],
    UserRole.ANALYST: [
        Permission(resource="forecasts", action="read", scope="brand"),
        Permission(resource="forecasts", action="write", scope="brand"),
        Permission(resource="runs", action="read", scope="brand"),
        Permission(resource="runs", action="write", scope="brand"),
        Permission(resource="backtest", action="read", scope="brand"),
        Permission(resource="backtest", action="write", scope="brand"),
        Permission(resource="scenarios", action="read", scope="brand"),
        Permission(resource="scenarios", action="write", scope="brand"),
        Permission(resource="dashboard", action="read", scope="brand"),
        Permission(resource="models", action="read", scope="brand"),
    ],
    UserRole.VIEWER: [
        Permission(resource="forecasts", action="read", scope="brand"),
        Permission(resource="runs", action="read", scope="brand"),
        Permission(resource="backtest", action="read", scope="brand"),
        Permission(resource="scenarios", action="read", scope="brand"),
        Permission(resource="dashboard", action="read", scope="brand"),
        Permission(resource="models", action="read", scope="brand"),
    ]
}
