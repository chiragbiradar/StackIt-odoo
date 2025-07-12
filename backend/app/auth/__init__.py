"""
Authentication package for StackIt API.
"""
from .password import hash_password, verify_password
from .jwt import create_access_token, verify_token, get_current_user, get_current_active_user
from .dependencies import require_auth, require_admin, require_owner_or_admin
from .utils import get_user_permissions

__all__ = [
    "hash_password",
    "verify_password", 
    "create_access_token",
    "verify_token",
    "get_current_user",
    "get_current_active_user",
    "require_auth",
    "require_admin", 
    "require_owner_or_admin",
    "get_user_permissions"
]
