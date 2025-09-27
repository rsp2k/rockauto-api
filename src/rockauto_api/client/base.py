"""Base client functionality for RockAuto API."""

import json
from typing import Dict, Optional

import httpx


class BaseClient:
    """Base client with common HTTP functionality."""

    def __init__(self):
        """Initialize the base client with proper headers and session."""
        self.API_ENDPOINT = "https://www.rockauto.com/catalog/catalogapi.php"
        self.CATALOG_BASE = "https://www.rockauto.com/en/catalog"

        # Create HTTP session with modern browser headers
        self.session = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://www.rockauto.com/",
                "Origin": "https://www.rockauto.com",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            },
            timeout=30.0,
        )

        # Required cookies for RockAuto API
        self.cookies = {
            "idlist": "0",
            "mkt_CA": "false",
            "mkt_MX": "false",
            "year_2005": "true",
            "ck": "1",
            "mkt_US": "true",
        }

        # Authentication state
        self.is_authenticated = False
        self.user_email: Optional[str] = None

    async def close(self) -> None:
        """Close the HTTP session."""
        await self.session.aclose()

    async def login(self, email: str, password: str, keep_signed_in: bool = False) -> bool:
        """
        Authenticate with RockAuto using email and password.

        Args:
            email: Account email address
            password: Account password
            keep_signed_in: Whether to persist login session

        Returns:
            bool: True if login was successful, False otherwise

        Raises:
            Exception: If login request fails
        """
        try:
            # Prepare login form data based on captured browser behavior
            form_data = {
                "loginaction": "login",
                "accountemail": email,
                "captchacode": "",  # Empty for normal logins
                "passworddecoy": "",  # Security field
                "password": password,
                "passwordconfirmdecoy": "",  # Security field
                "passwordconfirm": "",  # Security field
                "keepsignin": "true" if keep_signed_in else "false",
                "async": "1",
                "accountlogin_php": "1"
            }

            # Submit login request to the catalogapi.php endpoint with realistic browser headers
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": "https://www.rockauto.com/",
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "text/plain, */*; q=0.01",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            }

            response = await self.session.post(
                self.API_ENDPOINT,
                data=form_data,
                headers=headers,
                cookies=self.cookies
            )
            response.raise_for_status()

            # Update session cookies from response
            if response.cookies:
                self.cookies.update(dict(response.cookies))

            # Parse JSON response to check for login success
            try:
                response_json = response.json()

                # Check for CAPTCHA requirement
                if response_json.get("accountcaptchaerror") == 1:
                    self.is_authenticated = False
                    self.user_email = None
                    raise Exception("CAPTCHA required: RockAuto is requiring a security code for login. This typically happens when automated requests are detected. Try logging in manually through a browser first.")

                # Check for other errors
                if response_json.get("error"):
                    self.is_authenticated = False
                    self.user_email = None
                    raise Exception(f"Login error: {response_json.get('error')}")

                # Check for successful login using the exact API response format
                if (response_json.get("message") == "Log In Successful" and
                    response_json.get("email") == email and
                    response_json.get("act") == "login"):
                    self.is_authenticated = True
                    self.user_email = email
                    return True
                else:
                    self.is_authenticated = False
                    self.user_email = None
                    return False

            except (ValueError, KeyError) as e:
                # If JSON parsing fails, fall back to text analysis
                response_text = response.text.lower()
                if "log in successful" in response_text:
                    self.is_authenticated = True
                    self.user_email = email
                    return True
                else:
                    self.is_authenticated = False
                    self.user_email = None
                    return False

        except Exception as e:
            self.is_authenticated = False
            self.user_email = None
            raise Exception(f"Login failed: {str(e)}")

    async def logout(self) -> bool:
        """
        Log out from RockAuto session.

        Returns:
            bool: True if logout was successful
        """
        try:
            # Prepare logout form data
            form_data = {
                "loginaction": "logout",
                "async": "1",
                "accountlogin_php": "1"
            }

            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": "https://www.rockauto.com/",
                "X-Requested-With": "XMLHttpRequest"
            }

            response = await self.session.post(
                self.API_ENDPOINT,
                data=form_data,
                headers=headers,
                cookies=self.cookies
            )
            response.raise_for_status()

            # Reset authentication state
            self.is_authenticated = False
            self.user_email = None

            # Clear authentication cookies
            auth_cookies_to_clear = ["session", "login", "auth", "user"]
            for cookie_name in list(self.cookies.keys()):
                if any(auth_key in cookie_name.lower() for auth_key in auth_cookies_to_clear):
                    del self.cookies[cookie_name]

            return True

        except Exception as e:
            raise Exception(f"Logout failed: {str(e)}")

    def get_authentication_status(self) -> Dict[str, any]:
        """
        Get current authentication status.

        Returns:
            Dict containing authentication information
        """
        return {
            "is_authenticated": self.is_authenticated,
            "user_email": self.user_email,
            "has_session_cookies": bool(self.cookies)
        }

    async def _make_api_request(self, func: str, payload: dict) -> dict:
        """Make a request to the RockAuto catalogapi.php endpoint."""
        try:
            data = {
                "func": func,
                "payload": json.dumps(payload),
                "api_json_request": "1",
                "sctchecked": "1",
                "scbeenloaded": "false",
                "curCartGroupID": "",
            }

            response = await self.session.post(self.API_ENDPOINT, data=data, cookies=self.cookies)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            raise Exception(f"API request failed: {str(e)}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()