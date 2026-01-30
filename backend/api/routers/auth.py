"""
Authentication router - Login and Signup endpoints
"""

from datetime import datetime, timedelta
from typing import Optional
import jwt
import yaml
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

# JWT Configuration
SECRET_KEY = "reunite-ai-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str
    role: str = "family"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    role: str
    area: Optional[str] = None
    city: Optional[str] = None


def create_access_token(data: dict) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_yaml_credentials(username: str, password: str) -> Optional[dict]:
    """Verify credentials against login_config.yml (backward compatibility)."""
    try:
        with open("login_config.yml") as file:
            config = yaml.safe_load(file)
        
        users = config.get("credentials", {}).get("usernames", {})
        if username in users:
            user_data = users[username]
            # Note: In the YAML, passwords are hashed with streamlit_authenticator
            # For now, we'll do a simple comparison (should be updated for production)
            stored_password = user_data.get("password", "")
            
            # For demo: accept any password for existing users
            # In production, use proper password hashing verification
            return {
                "id": username,
                "name": user_data.get("name", username),
                "email": user_data.get("email", f"{username}@reunite.ai"),
                "phone": user_data.get("phone", ""),
                "role": user_data.get("role", "admin"),
                "area": user_data.get("area", ""),
                "city": user_data.get("city", ""),
            }
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error reading config: {e}")
    
    return None


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.
    
    Currently supports:
    - YAML-based users from login_config.yml (legacy Streamlit users)
    - Demo login for development
    """
    # Try YAML-based authentication first
    user_data = verify_yaml_credentials(request.username, request.password)
    
    # If no YAML user found, allow demo login
    if user_data is None:
        # Demo mode: accept any login for development
        user_data = {
            "id": request.username,
            "name": request.username.title(),
            "email": f"{request.username}@reunite.ai",
            "phone": "+91 98765 43210",
            "role": "admin",
            "area": "Demo Area",
            "city": "Demo City",
        }
    
    # Create JWT token
    access_token = create_access_token({"sub": user_data["id"], "name": user_data["name"]})
    
    return TokenResponse(
        access_token=access_token,
        user=user_data,
    )


@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest):
    """
    Register a new user.
    
    Note: For now, this creates a session but doesn't persist the user.
    In production, this should save to a users table in SQLite.
    """
    user_data = {
        "id": request.email.split("@")[0],
        "name": request.name,
        "email": request.email,
        "phone": request.phone,
        "role": request.role,
    }
    
    access_token = create_access_token({"sub": user_data["id"], "name": user_data["name"]})
    
    return TokenResponse(
        access_token=access_token,
        user=user_data,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user():
    """Get current user info (placeholder - needs JWT verification)."""
    # TODO: Extract user from JWT token
    return UserResponse(
        id="demo",
        name="Demo User",
        email="demo@reunite.ai",
        phone="+91 98765 43210",
        role="admin",
    )
