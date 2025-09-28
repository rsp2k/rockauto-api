"""Base client functionality for RockAuto API."""

import json
from typing import Dict, Optional

import httpx


class BaseClient:
    """Base client with common HTTP functionality."""

    def __init__(self, use_mobile_profile: bool = True):
        """Initialize the base client with proper headers and session.

        Args:
            use_mobile_profile: If True, use mobile browser headers and behavior
        """
        self.API_ENDPOINT = "https://www.rockauto.com/catalog/catalogapi.php"
        self.CATALOG_BASE = "https://www.rockauto.com/en/catalog"
        self.use_mobile_profile = use_mobile_profile

        # Choose headers based on profile type
        if use_mobile_profile:
            # Mobile Chrome headers - often trigger less aggressive anti-bot detection
            headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0"
            }
        else:
            # Desktop Chrome headers (based on Playwright analysis)
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Sec-Ch-Ua": '"Chromium";v="139", "Not;A=Brand";v="99"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Linux"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0"
            }

        # Create HTTP session with chosen headers
        self.session = httpx.AsyncClient(
            headers=headers,
            timeout=30.0,
            follow_redirects=True,  # Handle 302 redirects automatically
            cookies=httpx.Cookies()  # Use httpx's built-in cookie jar
        )

        # Set required initial cookies for RockAuto API
        self.session.cookies.set("idlist", "0", domain="www.rockauto.com")
        self.session.cookies.set("mkt_CA", "false", domain="www.rockauto.com")
        self.session.cookies.set("mkt_MX", "false", domain="www.rockauto.com")
        self.session.cookies.set("year_2005", "true", domain="www.rockauto.com")
        self.session.cookies.set("ck", "1", domain="www.rockauto.com")
        self.session.cookies.set("mkt_US", "true", domain="www.rockauto.com")

        # Keep backward compatibility with legacy cookies dict for troubleshooting
        self.cookies = dict(self.session.cookies)

        # Navigation state tracking (critical for CAPTCHA bypass)
        self.last_navigation_context: Optional[str] = None
        self.current_year_context: Optional[str] = None

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
                headers=headers
            )
            response.raise_for_status()

            # Update legacy cookies dict for backward compatibility
            self.cookies = dict(self.session.cookies)

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

            except (ValueError, KeyError):
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
                headers=headers
            )
            response.raise_for_status()

            # Reset authentication state
            self.is_authenticated = False
            self.user_email = None

            # Clear authentication cookies from session
            auth_cookies_to_clear = ["session", "login", "auth", "user"]
            for cookie_name in list(self.session.cookies.keys()):
                if any(auth_key in cookie_name.lower() for auth_key in auth_cookies_to_clear):
                    self.session.cookies.delete(cookie_name, domain="www.rockauto.com")

            # Update legacy cookies dict for backward compatibility
            self.cookies = dict(self.session.cookies)

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

            # Use AJAX-specific headers for API requests (based on Playwright analysis)
            api_headers = {
                "Accept": "text/plain, */*; q=0.01",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://www.rockauto.com/",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
            }

            response = await self.session.post(self.API_ENDPOINT, data=data, headers=api_headers)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            raise Exception(f"API request failed: {str(e)}")

    async def _simulate_navigation_context(self, make: str = None, year: str = None) -> None:
        """
        Simulate browser navigation context to avoid CAPTCHA detection.

        This method replicates the navnode_fetch calls that real browsers make
        when navigating the vehicle hierarchy, which is critical for bypassing
        anti-bot detection systems.
        """
        try:
            # Update navigation cookies like a real browser
            if make:
                catalog_href = f"https://www.rockauto.com/en/catalog/{make.lower()}"
                self.session.cookies.set("lastcathref", catalog_href, domain="www.rockauto.com")
                self.last_navigation_context = catalog_href

            if year:
                self.session.cookies.set(f"year_{year}", "true", domain="www.rockauto.com")
                self.current_year_context = year

            # Send navnode_fetch request like real browsers do
            if make:
                navnode_payload = {
                    "jsn": {
                        "groupindex": "46",  # This varies, but 46 is common for makes
                        "tab": "catalog",
                        "make": make.upper(),
                        "nodetype": "make",
                        "jsdata": {
                            "markets": [
                                {"c": "US", "y": "Y", "i": "Y"},
                                {"c": "CA", "y": "Y", "i": "Y"},
                                {"c": "MX", "y": "Y", "i": "Y"}
                            ],
                            "mktlist": "US,CA,MX",
                            "showForMarkets": {"US": True, "CA": True, "MX": True},
                            "importanceByMarket": {"US": "Y", "CA": "Y", "MX": "Y"},
                            "Show": 1
                        },
                        "label": make.upper(),
                        "href": catalog_href,
                        "labelset": True,
                        "jump_to_after_expand": True,
                        "dont_change_url": True,
                        "has_more_auto_open_steps": True,
                        "loaded": False,
                        "expand_after_load": True,
                        "fetching": True
                    },
                    "max_group_index": 363
                }

                # Make the navnode_fetch call with proper browser headers
                nav_headers = {
                    "Accept": "text/plain, */*; q=0.01",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Cache-Control": "no-cache",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Origin": "https://www.rockauto.com",
                    "Pragma": "no-cache",
                    "Referer": catalog_href,
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-origin",
                    "X-Requested-With": "XMLHttpRequest"
                }

                data = {
                    "func": "navnode_fetch",
                    "payload": json.dumps(navnode_payload),
                    "api_json_request": "1",
                    "sctchecked": "1",
                    "scbeenloaded": "false",
                    "curCartGroupID": "",
                    # Note: _jnck parameter is a dynamic anti-bot token generated by
                    # mobile JavaScript. Without this token, some requests may trigger CAPTCHA.
                    # Real browsers generate this from mobilecatalogmainbelowfold.js
                }

                # Send the navigation simulation request
                await self.session.post(self.API_ENDPOINT, data=data, headers=nav_headers)

            # Update legacy cookies dict
            self.cookies = dict(self.session.cookies)

        except Exception as e:
            # Don't fail the main request if navigation simulation fails
            # but log the issue for debugging
            pass

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
