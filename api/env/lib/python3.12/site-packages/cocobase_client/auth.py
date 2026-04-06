"""
Authentication handler for Cocobase client.

Provides methods for user authentication, registration, and user management.
This class handles all authentication-related operations and maintains user session state.
"""

from typing import Optional, Dict, Any, Callable, List
import requests
from cocobase_client.config import BASEURL
from cocobase_client.exceptions import CocobaseError


class AppUser:
    """Represents a user in the authentication system."""

    def __init__(self, data: Dict[str, Any]):
        self.id: str = data.get("id", "")
        self.email: str = data.get("email", "")
        self.created_at: str = data.get("created_at", "")
        self.data: Dict[str, Any] = data.get("data", {})
        self.client_id: str = data.get("client_id", "")
        self.roles: List[str] = data.get("roles", [])
        self._raw_data = data

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary."""
        return self._raw_data


class LoginResult:
    """Login result that clearly indicates whether 2FA is required."""

    def __init__(self, requires_2fa: bool, user: Optional[AppUser] = None, message: Optional[str] = None):
        self.requires_2fa = requires_2fa
        self.user = user
        self.message = message


class AuthCallbacks:
    """Collection of authentication event callbacks."""

    def __init__(self):
        self.on_login: Optional[Callable[[AppUser, str], None]] = None
        self.on_register: Optional[Callable[[AppUser, str], None]] = None
        self.on_logout: Optional[Callable[[], None]] = None
        self.on_user_update: Optional[Callable[[AppUser], None]] = None
        self.on_token_change: Optional[Callable[[Optional[str]], None]] = None
        self.on_auth_state_change: Optional[Callable[[Optional[AppUser], Optional[str]], None]] = None


class AuthHandler:
    """
    Authentication handler for Cocobase client.

    Provides methods for user authentication, registration, and user management.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.base_url = base_url or BASEURL
        self.api_key = api_key
        self.token: Optional[str] = None
        self.user: Optional[AppUser] = None
        self.callbacks = AuthCallbacks()

    def on_auth_event(
        self,
        on_login: Optional[Callable[[AppUser, str], None]] = None,
        on_register: Optional[Callable[[AppUser, str], None]] = None,
        on_logout: Optional[Callable[[], None]] = None,
        on_user_update: Optional[Callable[[AppUser], None]] = None,
        on_token_change: Optional[Callable[[Optional[str]], None]] = None,
        on_auth_state_change: Optional[Callable[[Optional[AppUser], Optional[str]], None]] = None,
    ):
        """Register callbacks for authentication events."""
        if on_login:
            self.callbacks.on_login = on_login
        if on_register:
            self.callbacks.on_register = on_register
        if on_logout:
            self.callbacks.on_logout = on_logout
        if on_user_update:
            self.callbacks.on_user_update = on_user_update
        if on_token_change:
            self.callbacks.on_token_change = on_token_change
        if on_auth_state_change:
            self.callbacks.on_auth_state_change = on_auth_state_change

    def clear_auth_callbacks(self):
        """Remove all registered callbacks."""
        self.callbacks = AuthCallbacks()

    def get_token(self) -> Optional[str]:
        """Gets the current authentication token."""
        return self.token

    def set_token(self, token: str):
        """Sets the authentication token."""
        self.token = token
        if self.callbacks.on_token_change:
            self.callbacks.on_token_change(token)

    def set_user(self, user: AppUser):
        """Updates the current user object."""
        self.user = user

    def get_user(self) -> Optional[AppUser]:
        """Gets the current user object."""
        return self.user

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        use_data_key: bool = True,
    ) -> Dict[str, Any]:
        """Makes an authenticated request to the API."""
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json"}

        if self.api_key:
            headers["x-api-key"] = self.api_key
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        payload = {"data": data} if use_data_key and data else data

        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=payload)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, json=payload)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, json=payload)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            if not response.ok:
                error_detail = response.text
                try:
                    error_detail = response.json()
                except:
                    pass

                raise CocobaseError(
                    f"Request failed: {response.status_code} - {error_detail}"
                )

            return response.json()
        except requests.RequestException as e:
            raise CocobaseError(f"Request error: {str(e)}")

    def init_auth(self):
        """Initializes authentication by restoring the session from storage."""
        # Note: Python doesn't have localStorage like JS
        # Users should implement their own session persistence
        if self.callbacks.on_auth_state_change:
            self.callbacks.on_auth_state_change(self.user, self.token)

    def login(self, email: str, password: str) -> LoginResult:
        """
        Authenticates a user with email and password.

        Args:
            email: User's email address
            password: User's password

        Returns:
            LoginResult indicating success or 2FA requirement
        """
        response = self._request(
            "POST",
            "/auth-collections/login",
            {"email": email, "password": password},
            use_data_key=False,
        )

        # Check if 2FA is required
        if response.get("requires_2fa"):
            return LoginResult(
                requires_2fa=True,
                message=response.get("message"),
            )

        # Normal login flow
        self.token = response["access_token"]
        self.set_token(self.token)

        if not response.get("user"):
            self.get_current_user()
        else:
            user = AppUser(response["user"])
            self.set_user(user)

        # Trigger login callback
        if self.user and self.callbacks.on_login:
            self.callbacks.on_login(self.user, self.token)

        return LoginResult(requires_2fa=False, user=self.user)

    def register(
        self,
        email: str,
        password: str,
        data: Optional[Dict[str, Any]] = None,
        roles: Optional[List[str]] = None,
        phone_number: Optional[str] = None,
    ) -> LoginResult:
        """
        Registers a new user with email, password, and optional additional data.

        Args:
            email: User's email address
            password: User's password
            data: Optional additional user data
            roles: Optional list of role names
            phone_number: Optional phone number

        Returns:
            LoginResult (registration may require 2FA if enabled)
        """
        payload = {"email": email, "password": password}
        if data:
            payload["data"] = data
        if roles:
            payload["roles"] = roles
        if phone_number:
            payload["phone_number"] = phone_number

        response = self._request(
            "POST",
            "/auth-collections/signup",
            payload,
            use_data_key=False,
        )

        # Check if 2FA is required
        if response.get("requires_2fa"):
            return LoginResult(
                requires_2fa=True,
                message=response.get("message"),
            )

        self.token = response["access_token"]
        self.set_token(self.token)

        if not response.get("user"):
            self.get_current_user()
        else:
            user = AppUser(response["user"])
            self.set_user(user)

        # Trigger register callback
        if self.user and self.callbacks.on_register:
            self.callbacks.on_register(self.user, self.token)

        return LoginResult(requires_2fa=False, user=self.user)

    def login_with_google(self, id_token: str, platform: str = "web") -> AppUser:
        """
        Authenticates a user using Google Sign-In with ID token.

        Args:
            id_token: Google ID token obtained from Google Sign-In
            platform: Platform identifier ('web', 'mobile', 'ios', 'android')

        Returns:
            Authenticated user object
        """
        response = self._request(
            "POST",
            "/auth-collections/google-verify",
            {"id_token": id_token, "platform": platform},
            use_data_key=False,
        )

        self.token = response["access_token"]
        self.set_token(self.token)
        user = AppUser(response["user"])
        self.set_user(user)

        # Trigger login callback
        if self.callbacks.on_login:
            self.callbacks.on_login(user, self.token)

        return user

    def login_with_github(self, code: str, redirect_uri: str, platform: str = "web") -> AppUser:
        """
        Authenticates a user using GitHub OAuth with authorization code.

        Args:
            code: GitHub authorization code from OAuth callback
            redirect_uri: The redirect URI used in the OAuth flow
            platform: Platform identifier ('web', 'mobile', 'ios', 'android')

        Returns:
            Authenticated user object
        """
        response = self._request(
            "POST",
            "/auth-collections/github-verify",
            {"code": code, "redirect_uri": redirect_uri, "platform": platform},
            use_data_key=False,
        )

        self.token = response["access_token"]
        self.set_token(self.token)
        user = AppUser(response["user"])
        self.set_user(user)

        # Trigger login callback
        if self.callbacks.on_login:
            self.callbacks.on_login(user, self.token)

        return user

    def register_with_files(
        self,
        email: str,
        password: str,
        data: Optional[Dict[str, Any]] = None,
        roles: Optional[List[str]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> LoginResult:
        """
        Register a new user with file uploads (avatar, cover photo, etc.)

        Args:
            email: User's email address
            password: User's password
            data: Optional additional user data
            roles: Optional list of role names
            files: Dictionary mapping field names to file objects

        Returns:
            LoginResult
        """
        import json

        form_data = {"data": json.dumps({"email": email, "password": password, "data": data, "roles": roles})}

        # Add files if provided
        files_dict = {}
        if files:
            for field_name, file_or_files in files.items():
                if isinstance(file_or_files, list):
                    # Multiple files
                    for file_obj in file_or_files:
                        if not files_dict.get(field_name):
                            files_dict[field_name] = []
                        files_dict[field_name].append(file_obj)
                else:
                    files_dict[field_name] = file_or_files

        url = f"{self.base_url}/auth-collections/signup"
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        response = requests.post(url, data=form_data, files=files_dict, headers=headers)

        if not response.ok:
            raise CocobaseError(f"Registration failed: {response.text}")

        result = response.json()

        # Check if 2FA is required
        if result.get("requires_2fa"):
            return LoginResult(
                requires_2fa=True,
                message=result.get("message"),
            )

        self.token = result["access_token"]
        self.set_token(self.token)
        user = AppUser(result["user"])
        self.set_user(user)

        # Trigger register callback
        if self.callbacks.on_register:
            self.callbacks.on_register(user, self.token)

        return LoginResult(requires_2fa=False, user=user)

    def logout(self):
        """Logs out the current user by clearing the token and user data."""
        self.token = None
        self.user = None

        # Trigger logout callback
        if self.callbacks.on_logout:
            self.callbacks.on_logout()
        if self.callbacks.on_token_change:
            self.callbacks.on_token_change(None)

    def is_authenticated(self) -> bool:
        """Checks if a user is currently authenticated."""
        return self.token is not None

    def get_current_user(self) -> AppUser:
        """Fetches the current authenticated user's data from the server."""
        if not self.token:
            raise CocobaseError("User is not authenticated")

        response = self._request("GET", "/auth-collections/user")
        user = AppUser(response)
        self.user = user
        self.set_user(user)
        return user

    def update_user(
        self,
        data: Optional[Dict[str, Any]] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
    ) -> AppUser:
        """
        Updates the current user's profile data.

        Args:
            data: Optional user data fields to update
            email: Optional new email address
            password: Optional new password

        Returns:
            Updated user object
        """
        if not self.token:
            raise CocobaseError("User is not authenticated")

        # Build request body
        body = {}
        if data is not None:
            # Merge with existing user data
            existing_data = self.user.data if self.user else {}
            merged_data = {**existing_data, **data}
            body["data"] = merged_data
        if email is not None:
            body["email"] = email
        if password is not None:
            body["password"] = password

        response = self._request(
            "PATCH",
            "/auth-collections/user",
            body,
            use_data_key=False,
        )

        user = AppUser(response)
        self.user = user
        self.set_user(user)

        # Trigger user update callback
        if self.callbacks.on_user_update:
            self.callbacks.on_user_update(user)

        return user

    def update_user_with_files(
        self,
        data: Optional[Dict[str, Any]] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> AppUser:
        """
        Update current user with file uploads.

        Args:
            data: Optional user data fields to update
            email: Optional new email address
            password: Optional new password
            files: Dictionary mapping field names to file objects

        Returns:
            Updated user object
        """
        if not self.token:
            raise CocobaseError("User is not authenticated")

        import json

        # Build request body
        body = {}
        if data is not None:
            existing_data = self.user.data if self.user else {}
            merged_data = {**existing_data, **data}
            body["data"] = merged_data
        if email is not None:
            body["email"] = email
        if password is not None:
            body["password"] = password

        form_data = {}
        if body:
            form_data["data"] = json.dumps(body)

        # Add files if provided
        files_dict = {}
        if files:
            for field_name, file_or_files in files.items():
                if isinstance(file_or_files, list):
                    for file_obj in file_or_files:
                        if not files_dict.get(field_name):
                            files_dict[field_name] = []
                        files_dict[field_name].append(file_obj)
                else:
                    files_dict[field_name] = file_or_files

        url = f"{self.base_url}/auth-collections/user"
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        response = requests.patch(url, data=form_data, files=files_dict, headers=headers)

        if not response.ok:
            raise CocobaseError(f"User update failed: {response.text}")

        result = response.json()
        user = AppUser(result)
        self.user = user
        self.set_user(user)

        # Trigger user update callback
        if self.callbacks.on_user_update:
            self.callbacks.on_user_update(user)

        return user

    def has_role(self, role: str) -> bool:
        """
        Checks if the current user has a specific role.

        Args:
            role: Role to check for

        Returns:
            True if user has the role, false otherwise
        """
        if not self.user:
            raise CocobaseError("User is not authenticated")
        return role in self.user.roles

    def list_users(self, query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Lists users from the auth collection with optional filtering and pagination.

        Args:
            query: Optional query parameters for filtering, sorting, and pagination

        Returns:
            Dictionary containing list of users and metadata
        """
        from urllib.parse import urlencode

        query_str = ""
        if query:
            query_str = "?" + urlencode(query)

        url = f"/auth-collections/users{query_str}"
        return self._request("GET", url)

    def get_user_by_id(self, user_id: str) -> AppUser:
        """
        Gets a user by their ID.

        Args:
            user_id: Unique ID of the user

        Returns:
            User object
        """
        response = self._request("GET", f"/auth-collections/users/{user_id}")
        return AppUser(response)

    def enable_2fa(self):
        """Enables Two-Factor Authentication (2FA) for the current user."""
        self._request("POST", "/auth-collections/2fa/enable", {}, use_data_key=False)

    def disable_2fa(self):
        """Disables Two-Factor Authentication (2FA) for the current user."""
        self._request("POST", "/auth-collections/2fa/disable", {}, use_data_key=False)

    def send_2fa_code(self, email: str):
        """
        Sends a Two-Factor Authentication (2FA) code to the user's email.

        Args:
            email: Email address to send the code to
        """
        self._request("POST", "/auth-collections/2fa/send-code", {"email": email}, use_data_key=False)

    def verify_2fa_login(self, email: str, code: str) -> AppUser:
        """
        Completes login after 2FA verification.

        Args:
            email: User's email address
            code: 2FA verification code

        Returns:
            Authenticated user object
        """
        response = self._request(
            "POST",
            "/auth-collections/2fa/verify",
            {"email": email, "code": code},
            use_data_key=False,
        )

        self.token = response["access_token"]
        self.set_token(self.token)
        user = AppUser(response["user"])
        self.set_user(user)

        # Trigger login callback
        if self.callbacks.on_login:
            self.callbacks.on_login(user, self.token)

        return user

    def request_email_verification(self):
        """Requests an email verification to be sent to the user's email address."""
        return self._request("POST", "/auth-collections/verify-email/send", {}, use_data_key=False)

    def verify_email(self, token: str):
        """
        Verifies the user's email using the provided token.

        Args:
            token: Verification token
        """
        return self._request("POST", "/auth-collections/verify-email/verify", {"token": token}, use_data_key=False)

    def resend_verification_email(self):
        """Resends the email verification to the user's email address."""
        self._request("POST", "/auth-collections/verify-email/resend", {}, use_data_key=False)
