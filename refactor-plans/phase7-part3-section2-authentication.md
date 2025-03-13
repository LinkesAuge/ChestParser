# Phase 7 Part 3 - Section 2: Authentication & Authorization

## Overview
This document details the implementation of authentication and authorization for the Total Battle Analyzer API. The system provides secure access control to API resources, user identity management, and permission-based restrictions. It implements multiple authentication methods and a flexible role-based permission system to ensure data security while allowing appropriate access to authorized users and applications.

## Key Components

### 1. Authentication Methods
- API key authentication
- OAuth 2.0 integration
- JWT token handling
- Session management
- Credential storage and encryption

### 2. Role-Based Access Control
- User role definitions
- Permission hierarchy
- Resource-based permissions
- Action-based permissions
- Dynamic permission validation

### 3. API Key Management
- Key generation and distribution
- Key validation and verification
- Key revocation and rotation
- Usage tracking and analytics
- Rate limiting per key

### 4. OAuth Integration
- OAuth 2.0 providers (Google, GitHub)
- Authorization code flow
- Token exchange and validation
- Profile information retrieval
- State management and CSRF protection

## Implementation Details

### 1. Authentication Service

```python
# src/goob_ai/auth/auth_service.py
from typing import Dict, List, Any, Optional, Tuple
import logging
import secrets
import string
import time
import jwt
from datetime import datetime, timedelta
from pathlib import Path
import json
import hashlib
import base64
from ..config import ConfigManager

logger = logging.getLogger(__name__)

class AuthService:
    """Service for authentication and authorization."""
    
    def __init__(self, config_manager: ConfigManager) -> None:
        """
        Initialize authentication service.
        
        Args:
            config_manager: Application configuration manager
        """
        self.config_manager = config_manager
        self.auth_config = self.config_manager.get("auth", {})
        self.secret_key = self.auth_config.get("secret_key")
        
        # Generate secret key if not present
        if not self.secret_key:
            self.secret_key = self._generate_secret_key()
            self.auth_config["secret_key"] = self.secret_key
            self.config_manager.set("auth", self.auth_config)
            self.config_manager.save()
            
        # Load API keys
        self.api_keys = self.auth_config.get("api_keys", {})
        
        # Load user roles
        self.user_roles = self.auth_config.get("user_roles", {})
        
        # Load role permissions
        self.role_permissions = self.auth_config.get("role_permissions", {
            "admin": ["*"],  # Admin has all permissions
            "user": ["read:data", "read:analysis", "create:report"],
            "guest": ["read:data"]
        })
        
    def _generate_secret_key(self) -> str:
        """
        Generate a secure random secret key.
        
        Returns:
            Secure random string
        """
        return secrets.token_hex(32)
        
    def generate_api_key(self, name: str, role: str = "user") -> str:
        """
        Generate a new API key.
        
        Args:
            name: Name or identifier for the API key
            role: Role to assign to the API key
            
        Returns:
            New API key
        """
        # Generate random API key
        alphabet = string.ascii_letters + string.digits
        api_key = ''.join(secrets.choice(alphabet) for _ in range(32))
        
        # Add key to API keys with metadata
        self.api_keys[api_key] = {
            "name": name,
            "role": role,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "usage_count": 0
        }
        
        # Save to configuration
        self.auth_config["api_keys"] = self.api_keys
        self.config_manager.set("auth", self.auth_config)
        self.config_manager.save()
        
        return api_key
        
    def validate_api_key(self, api_key: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate an API key.
        
        Args:
            api_key: API key to validate
            
        Returns:
            Tuple of (is_valid, key_metadata)
        """
        if api_key not in self.api_keys:
            return False, None
            
        # Update last used and usage count
        self.api_keys[api_key]["last_used"] = datetime.now().isoformat()
        self.api_keys[api_key]["usage_count"] += 1
        
        # Save to configuration (periodically, not every request)
        if self.api_keys[api_key]["usage_count"] % 100 == 0:
            self.auth_config["api_keys"] = self.api_keys
            self.config_manager.set("auth", self.auth_config)
            self.config_manager.save()
            
        return True, self.api_keys[api_key]
        
    def revoke_api_key(self, api_key: str) -> bool:
        """
        Revoke an API key.
        
        Args:
            api_key: API key to revoke
            
        Returns:
            True if key was revoked, False if key not found
        """
        if api_key not in self.api_keys:
            return False
            
        # Remove key
        del self.api_keys[api_key]
        
        # Save to configuration
        self.auth_config["api_keys"] = self.api_keys
        self.config_manager.set("auth", self.auth_config)
        self.config_manager.save()
        
        return True
        
    def get_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all API keys with metadata.
        
        Returns:
            Dict of API keys and their metadata
        """
        return self.api_keys
        
    def create_jwt_token(
        self, subject: str, role: str, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT token.
        
        Args:
            subject: Subject of the token (usually user ID)
            role: User role
            expires_delta: Token expiration time
            
        Returns:
            JWT token string
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=15)
            
        # Create token data
        now = datetime.utcnow()
        expires = now + expires_delta
        
        token_data = {
            "sub": subject,
            "role": role,
            "exp": expires,
            "iat": now,
            "type": "access"
        }
        
        # Create token
        token = jwt.encode(token_data, self.secret_key, algorithm="HS256")
        
        return token
        
    def validate_jwt_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate a JWT token.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Tuple of (is_valid, token_data)
        """
        try:
            # Decode and validate token
            token_data = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            # Check if token is expired
            expiration = datetime.fromtimestamp(token_data["exp"])
            if expiration < datetime.utcnow():
                return False, None
                
            return True, token_data
            
        except jwt.PyJWTError as e:
            logger.warning(f"JWT validation error: {str(e)}")
            return False, None
            
    def has_permission(self, role: str, permission: str) -> bool:
        """
        Check if a role has a specific permission.
        
        Args:
            role: User role
            permission: Permission to check
            
        Returns:
            True if role has permission, False otherwise
        """
        if role not in self.role_permissions:
            return False
            
        permissions = self.role_permissions[role]
        
        # Check for wildcard permission
        if "*" in permissions:
            return True
            
        # Check for specific permission
        if permission in permissions:
            return True
            
        # Check for category wildcard (e.g., "read:*")
        category = permission.split(":")[0] if ":" in permission else ""
        if f"{category}:*" in permissions:
            return True
            
        return False
        
    def get_user_role(self, user_id: str) -> str:
        """
        Get role for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            User role, defaults to "guest" if not found
        """
        return self.user_roles.get(user_id, "guest")
        
    def set_user_role(self, user_id: str, role: str) -> None:
        """
        Set role for a user.
        
        Args:
            user_id: User ID
            role: Role to assign
        """
        self.user_roles[user_id] = role
        
        # Save to configuration
        self.auth_config["user_roles"] = self.user_roles
        self.config_manager.set("auth", self.auth_config)
        self.config_manager.save()
```

### 2. OAuth Integration

```python
# src/goob_ai/auth/oauth.py
from typing import Dict, Any, Optional, Tuple
import logging
from pathlib import Path
import json
import requests
import secrets
import base64
import hashlib
import time
from urllib.parse import urlencode
from ..config import ConfigManager
from .auth_service import AuthService

logger = logging.getLogger(__name__)

class OAuthProvider:
    """Base class for OAuth providers."""
    
    def __init__(
        self, 
        name: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scope: str
    ) -> None:
        """
        Initialize OAuth provider.
        
        Args:
            name: Provider name
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
            scope: OAuth scope
        """
        self.name = name
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        
    def get_authorization_url(self) -> Tuple[str, str]:
        """
        Get authorization URL for OAuth flow.
        
        Returns:
            Tuple of (authorization_url, state)
        """
        raise NotImplementedError("Subclasses must implement get_authorization_url")
        
    def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code
            state: State parameter
            
        Returns:
            Token response data
        """
        raise NotImplementedError("Subclasses must implement exchange_code_for_token")
        
    def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        Get user information using access token.
        
        Args:
            token: Access token
            
        Returns:
            User information
        """
        raise NotImplementedError("Subclasses must implement get_user_info")
        
class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth provider implementation."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scope: str = "openid email profile"
    ) -> None:
        """
        Initialize Google OAuth provider.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
            scope: OAuth scope
        """
        super().__init__(
            name="google",
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope
        )
        
        self.auth_url = "https://accounts.google.com/o/oauth2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        
    def get_authorization_url(self) -> Tuple[str, str]:
        """
        Get Google authorization URL for OAuth flow.
        
        Returns:
            Tuple of (authorization_url, state)
        """
        # Generate state for CSRF protection
        state = secrets.token_hex(16)
        
        # Generate PKCE code verifier and challenge
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).decode().rstrip("=")
        
        # Store code verifier for later use
        self.code_verifier = code_verifier
        
        # Build authorization URL
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",  # Request refresh token
            "prompt": "consent"  # Force consent screen
        }
        
        authorization_url = f"{self.auth_url}?{urlencode(params)}"
        
        return authorization_url, state
        
    def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code
            state: State parameter
            
        Returns:
            Token response data
        """
        # Build token request
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "code_verifier": getattr(self, "code_verifier", ""),
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }
        
        # Request access token
        response = requests.post(self.token_url, data=data)
        
        if response.status_code != 200:
            logger.error(f"Token exchange error: {response.text}")
            return {}
            
        return response.json()
        
    def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        Get user information using access token.
        
        Args:
            token: Access token
            
        Returns:
            User information
        """
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(self.userinfo_url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"User info error: {response.text}")
            return {}
            
        return response.json()
        
class GitHubOAuthProvider(OAuthProvider):
    """GitHub OAuth provider implementation."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scope: str = "read:user user:email"
    ) -> None:
        """
        Initialize GitHub OAuth provider.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
            scope: OAuth scope
        """
        super().__init__(
            name="github",
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope
        )
        
        self.auth_url = "https://github.com/login/oauth/authorize"
        self.token_url = "https://github.com/login/oauth/access_token"
        self.userinfo_url = "https://api.github.com/user"
        self.emails_url = "https://api.github.com/user/emails"
        
    def get_authorization_url(self) -> Tuple[str, str]:
        """
        Get GitHub authorization URL for OAuth flow.
        
        Returns:
            Tuple of (authorization_url, state)
        """
        # Generate state for CSRF protection
        state = secrets.token_hex(16)
        
        # Build authorization URL
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "state": state
        }
        
        authorization_url = f"{self.auth_url}?{urlencode(params)}"
        
        return authorization_url, state
        
    def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code
            state: State parameter
            
        Returns:
            Token response data
        """
        # Build token request
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "state": state
        }
        
        headers = {"Accept": "application/json"}
        
        # Request access token
        response = requests.post(self.token_url, data=data, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Token exchange error: {response.text}")
            return {}
            
        return response.json()
        
    def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        Get user information using access token.
        
        Args:
            token: Access token
            
        Returns:
            User information
        """
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/json"
        }
        
        # Get user profile
        response = requests.get(self.userinfo_url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"User info error: {response.text}")
            return {}
            
        user_data = response.json()
        
        # If email is private, get it from emails endpoint
        if not user_data.get("email"):
            emails_response = requests.get(self.emails_url, headers=headers)
            
            if emails_response.status_code == 200:
                emails = emails_response.json()
                primary_email = next((e for e in emails if e.get("primary")), None)
                
                if primary_email:
                    user_data["email"] = primary_email.get("email")
                    
        return user_data
```

### 3. Role-Based Access Control

```python
# src/goob_ai/auth/rbac.py
from typing import Dict, List, Any, Optional, Set, Callable
import logging
import functools
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from ..config import ConfigManager
from .auth_service import AuthService

logger = logging.getLogger(__name__)

class RBACService:
    """Role-Based Access Control service."""
    
    def __init__(self, auth_service: AuthService) -> None:
        """
        Initialize RBAC service.
        
        Args:
            auth_service: Authentication service
        """
        self.auth_service = auth_service
        
        # Define permission hierarchy
        self.permission_hierarchy = {
            # Data permissions
            "read:data": ["read:players", "read:battles", "read:chests"],
            "write:data": ["write:players", "write:battles", "write:chests"],
            
            # Analysis permissions
            "read:analysis": ["read:stats", "read:charts"],
            "write:analysis": ["write:stats", "write:charts"],
            
            # Report permissions
            "read:reports": [],
            "create:report": [],
            "export:report": [],
            
            # Admin permissions
            "admin:users": ["create:user", "update:user", "delete:user"],
            "admin:system": ["read:logs", "update:settings", "backup:data"]
        }
        
        # Build expanded permissions
        self.expanded_permissions = self._build_expanded_permissions()
        
    def _build_expanded_permissions(self) -> Dict[str, Set[str]]:
        """
        Build expanded permissions from hierarchy.
        
        Returns:
            Dict mapping permissions to sets of expanded permissions
        """
        expanded = {}
        
        def expand_permission(perm, visited=None):
            if visited is None:
                visited = set()
                
            if perm in visited:
                return set()
                
            visited.add(perm)
            
            result = {perm}
            for sub_perm in self.permission_hierarchy.get(perm, []):
                result.update(expand_permission(sub_perm, visited))
                
            return result
            
        for perm in self.permission_hierarchy:
            expanded[perm] = expand_permission(perm)
            
        return expanded
        
    def has_permission(self, role: str, required_permission: str) -> bool:
        """
        Check if a role has a specific permission.
        
        Args:
            role: User role
            required_permission: Permission to check
            
        Returns:
            True if role has permission, False otherwise
        """
        # Direct permission check
        direct_permission = self.auth_service.has_permission(role, required_permission)
        if direct_permission:
            return True
            
        # Check expanded permissions
        expanded_required = self.expanded_permissions.get(required_permission, {required_permission})
        
        for perm in expanded_required:
            if self.auth_service.has_permission(role, perm):
                return True
                
        return False
        
def require_permission(permission: str):
    """
    Decorator to require a specific permission.
    
    Args:
        permission: Required permission
        
    Returns:
        Dependency function
    """
    api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
    
    async def check_permission(
        request: Request,
        api_key: Optional[str] = Depends(api_key_header)
    ):
        # Get services
        auth_service = request.app.state.auth_service
        rbac_service = request.app.state.rbac_service
        
        # Check API key
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key is required",
                headers={"WWW-Authenticate": "APIKey"},
            )
            
        is_valid, key_data = auth_service.validate_api_key(api_key)
        
        if not is_valid or not key_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "APIKey"},
            )
            
        # Get role from key data
        role = key_data.get("role", "guest")
        
        # Check permission
        if not rbac_service.has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions (required: {permission})",
            )
            
        # Set user info in request state
        request.state.user = {
            "api_key": api_key,
            "role": role,
            "name": key_data.get("name")
        }
        
    return check_permission
```

### 4. API Integration

```python
# src/goob_ai/api/auth_router.py
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
import logging
from ..auth.auth_service import AuthService
from ..auth.oauth import GoogleOAuthProvider, GitHubOAuthProvider
from ..auth.rbac import require_permission

logger = logging.getLogger(__name__)

# Models
class TokenResponse(BaseModel):
    """Token response model."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    
class APIKeyResponse(BaseModel):
    """API key response model."""
    
    api_key: str = Field(..., description="API key")
    name: str = Field(..., description="API key name")
    role: str = Field(..., description="API key role")
    
class APIKeyRequest(BaseModel):
    """API key request model."""
    
    name: str = Field(..., description="API key name")
    role: str = Field("user", description="API key role")
    
class OAuthUrlResponse(BaseModel):
    """OAuth URL response model."""
    
    url: str = Field(..., description="OAuth authorization URL")
    
class OAuthCallbackRequest(BaseModel):
    """OAuth callback request model."""
    
    code: str = Field(..., description="Authorization code")
    state: str = Field(..., description="State parameter")
    provider: str = Field(..., description="OAuth provider")

# Create auth router
auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"description": "Unauthorized"}},
)

@auth_router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    auth_service = request.app.state.auth_service
    
    # This is a simplified example - in a real application, you would validate
    # username and password against a database
    if form_data.username != "admin" or form_data.password != "password":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Create access token
    access_token = auth_service.create_jwt_token(
        subject=form_data.username,
        role="admin",
        expires_delta=None
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600
    }
    
@auth_router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    request: Request,
    key_request: APIKeyRequest,
    _: None = Depends(require_permission("admin:system"))
):
    """
    Create a new API key.
    """
    auth_service = request.app.state.auth_service
    
    # Generate API key
    api_key = auth_service.generate_api_key(
        name=key_request.name,
        role=key_request.role
    )
    
    return {
        "api_key": api_key,
        "name": key_request.name,
        "role": key_request.role
    }
    
@auth_router.get("/api-keys", response_model=List[Dict[str, Any]])
async def list_api_keys(
    request: Request,
    _: None = Depends(require_permission("admin:system"))
):
    """
    List all API keys.
    """
    auth_service = request.app.state.auth_service
    
    # Get API keys
    api_keys = auth_service.get_api_keys()
    
    # Format response
    result = []
    for key, data in api_keys.items():
        result.append({
            "api_key": key,
            **data
        })
        
    return result
    
@auth_router.delete("/api-keys/{api_key}")
async def revoke_api_key(
    api_key: str,
    request: Request,
    _: None = Depends(require_permission("admin:system"))
):
    """
    Revoke an API key.
    """
    auth_service = request.app.state.auth_service
    
    # Revoke API key
    success = auth_service.revoke_api_key(api_key)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
        
    return {"detail": "API key revoked successfully"}
    
@auth_router.get("/oauth/{provider}/url", response_model=OAuthUrlResponse)
async def get_oauth_url(provider: str, request: Request):
    """
    Get OAuth authorization URL.
    """
    # Get OAuth provider
    oauth_provider = None
    if provider == "google":
        oauth_provider = request.app.state.google_oauth
    elif provider == "github":
        oauth_provider = request.app.state.github_oauth
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )
        
    # Get authorization URL
    url, state = oauth_provider.get_authorization_url()
    
    # Store state in session
    request.session[f"oauth_state_{provider}"] = state
    
    return {"url": url}
    
@auth_router.post("/oauth/callback", response_model=TokenResponse)
async def oauth_callback(callback: OAuthCallbackRequest, request: Request):
    """
    Handle OAuth callback.
    """
    auth_service = request.app.state.auth_service
    provider_name = callback.provider
    
    # Get OAuth provider
    oauth_provider = None
    if provider_name == "google":
        oauth_provider = request.app.state.google_oauth
    elif provider_name == "github":
        oauth_provider = request.app.state.github_oauth
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider_name}"
        )
        
    # Verify state
    stored_state = request.session.get(f"oauth_state_{provider_name}")
    if not stored_state or stored_state != callback.state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
        
    # Exchange code for token
    token_data = oauth_provider.exchange_code_for_token(
        code=callback.code,
        state=callback.state
    )
    
    if not token_data or "access_token" not in token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange code for token"
        )
        
    # Get user info
    user_info = oauth_provider.get_user_info(token_data["access_token"])
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user info"
        )
        
    # Get user ID
    user_id = user_info.get("id") or user_info.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user ID"
        )
        
    # Create user ID with provider prefix
    provider_user_id = f"{provider_name}:{user_id}"
    
    # Get user role (or assign default)
    role = auth_service.get_user_role(provider_user_id)
    
    # Create JWT token
    access_token = auth_service.create_jwt_token(
        subject=provider_user_id,
        role=role,
        expires_delta=None
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600
    }
```

## Integration with API Server

To integrate the authentication and authorization system with the API server, we need to:

1. Initialize the authentication services in the API server
2. Add OAuth providers
3. Include the authentication router
4. Set up the RBAC middleware

Here's how to update the API server initialization:

```python
# In src/goob_ai/api/server.py, add:

# Import authentication services
from ..auth.auth_service import AuthService
from ..auth.rbac import RBACService
from ..auth.oauth import GoogleOAuthProvider, GitHubOAuthProvider
from .auth_router import auth_router

# In APIServer.__init__, add:
# Initialize authentication services
self.auth_service = AuthService(config_manager)
self.rbac_service = RBACService(self.auth_service)

# Initialize OAuth providers
api_config = config_manager.get("api", {})
oauth_config = api_config.get("oauth", {})

# Google OAuth
google_config = oauth_config.get("google", {})
if google_config:
    self.google_oauth = GoogleOAuthProvider(
        client_id=google_config.get("client_id", ""),
        client_secret=google_config.get("client_secret", ""),
        redirect_uri=google_config.get("redirect_uri", "")
    )
    
# GitHub OAuth
github_config = oauth_config.get("github", {})
if github_config:
    self.github_oauth = GitHubOAuthProvider(
        client_id=github_config.get("client_id", ""),
        client_secret=github_config.get("client_secret", ""),
        redirect_uri=github_config.get("redirect_uri", "")
    )

# Store services in app state
self.app.state.auth_service = self.auth_service
self.app.state.rbac_service = self.rbac_service
if hasattr(self, "google_oauth"):
    self.app.state.google_oauth = self.google_oauth
if hasattr(self, "github_oauth"):
    self.app.state.github_oauth = self.github_oauth

# In _include_router, add:
# Include authentication router
self.app.include_router(
    auth_router,
    prefix="/api/v1",
    dependencies=[Depends(self._get_services)],
)
```

## Implementation Steps

### Week 1: Authentication Framework (Days 1-3)
1. Implement the AuthService class for API key management and JWT token handling
2. Create RBACService for role-based access control
3. Develop the authentication router endpoints

### Week 2: OAuth Integration (Days 4-7)
1. Implement OAuth providers for Google and GitHub
2. Create the OAuth authorization flow endpoints
3. Develop token exchange and user profile retrieval
4. Integrate with the API server

## Dependencies
- Python 3.8+
- PyJWT (for JWT token handling)
- Authlib (for OAuth 2.0 implementation)
- requests (for HTTP requests)
- FastAPI security components

## Testing Strategy
1. Unit tests for AuthService and RBACService
2. Integration tests for API key authentication
3. OAuth flow testing with mock providers
4. Security testing for token validation and permission enforcement

## Security Considerations
1. Store secrets securely using environment variables or secure storage
2. Implement HTTPS for all OAuth redirects and API endpoints
3. Use short-lived JWT tokens and implement token refresh
4. Follow OAuth 2.0 best practices including PKCE for public clients
5. Implement rate limiting for authentication endpoints
6. Add brute force protection for credential-based authentication
7. Use secure random generators for tokens and keys 