"""
Cocobase Python Client

The official Python SDK for Cocobase - Backend as a Service platform.
"""

from .client import CocoBaseClient
from .exceptions import CocobaseError, InvalidApiKeyError
from .record import Record, Collection
from .query import QueryBuilder
from .auth import AuthHandler, AppUser, LoginResult
from .functions import CloudFunction, FunctionResponse

__version__ = "1.5.0"

__all__ = [
    "CocoBaseClient",
    "CocobaseError",
    "InvalidApiKeyError",
    "Record",
    "Collection",
    "QueryBuilder",
    "AuthHandler",
    "AppUser",
    "LoginResult",
    "CloudFunction",
    "FunctionResponse",
]
