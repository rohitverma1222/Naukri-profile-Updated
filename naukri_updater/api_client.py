"""
Naukri API Client — Direct HTTP-based profile update fallback.

Uses curl_cffi to impersonate a real browser's TLS fingerprint,
bypassing Akamai WAF on datacenter IPs where Selenium gets blocked.

When SCRAPE_DO_TOKEN is set, all requests are routed through Scrape.do's
API mode (URL wrapper) to use residential IPs.
"""

import json
import logging
import re
import time
import random
import urllib.parse
from pathlib import Path

from . import config

logger = logging.getLogger(__name__)

# Naukri internal API base URLs
PROFILE_PAGE_URL = "https://www.naukri.com/mnjuser/profile"


class NaukriAPIClient:
    """Performs Naukri profile updates via direct HTTP requests with TLS impersonation."""

    def __init__(self):
        self.session = None
        self.user_id = None
        self.scrape_do_token = config.SCRAPE_DO_TOKEN

    def _wrap_url(self, url: str) -> str:
        """Wrap URL through Scrape.do API if token is configured."""
        if self.scrape_do_token:
            encoded = urllib.parse.quote(url, safe="")
            return f"http://api.scrape.do/?token={self.scrape_do_token}&url={encoded}&super=true"
        return url

    def setup_session(self) -> bool:
        """Create a curl_cffi session with browser impersonation and load cookies."""
        try:
            from curl_cffi.requests import Session
        except ImportError:
            logger.error("curl_cffi is not installed. Run: pip install curl_cffi")
            return False

        logger.info("[API] Setting up TLS-impersonated HTTP session...")

        self.session = Session(
            impersonate="chrome124",
            verify=False,  # Scrape.do may redirect through different certs
        )

        if self.scrape_do_token:
            logger.info("[API] Scrape.do API mode enabled (super=true for residential IPs)")
        else:
            logger.info("[API] No proxy configured (running direct)")

        # Set common headers to mimic a real browser
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
            ),
        })

        # Load cookies
        cookies = config.get_cookies()
        if not cookies:
            logger.error("[API] No cookies available")
            return False

        cookies_loaded = 0
        for cookie in cookies:
            name = cookie.get("name", "")
            value = cookie.get("value", "")
            domain = cookie.get("domain", ".naukri.com")
            if name and value:
                self.session.cookies.set(name, value, domain=domain)
                cookies_loaded += 1

        logger.info(f"[API] Loaded {cookies_loaded} cookies into session")
        return True

    def _make_request(self, method: str, url: str, **kwargs):
        """Make an HTTP request, routing through Scrape.do if configured."""
        wrapped_url = self._wrap_url(url)
        if wrapped_url != url:
            logger.info(f"[API] Routing through Scrape.do: {method.upper()} {url}")

        # When using Scrape.do API mode, cookies must be sent as a header
        # because the request goes to api.scrape.do, not naukri.com directly
        if self.scrape_do_token and self.session:
            cookie_str = "; ".join(
                f"{c.name}={c.value}" for c in self.session.cookies
                if c.domain and "naukri" in c.domain
            )
            if cookie_str:
                if "headers" not in kwargs:
                    kwargs["headers"] = {}
                kwargs["headers"]["Cookie"] = cookie_str

        if method.lower() == "get":
            return self.session.get(wrapped_url, **kwargs)
        elif method.lower() == "post":
            return self.session.post(wrapped_url, **kwargs)
        elif method.lower() == "put":
            return self.session.put(wrapped_url, **kwargs)
        return None

    def _extract_user_id(self, page_html: str) -> str | None:
        """Extract user ID from the profile page HTML."""
        patterns = [
            r'"userId"\s*:\s*"?(\d+)"?',
            r'"user_id"\s*:\s*"?(\d+)"?',
            r'data-user-id="(\d+)"',
            r'/users/(\d+)/',
        ]
        for pattern in patterns:
            match = re.search(pattern, page_html)
            if match:
                return match.group(1)
        return None

    def _extract_headline(self, page_html: str) -> str | None:
        """Extract the current headline from the profile page."""
        patterns = [
            r'"resumeHeadline"\s*:\s*"([^"]*)"',
            r'id="resumeHeadlineTxt"[^>]*>([^<]*)<',
            r'"headline"\s*:\s*"([^"]*)"',
        ]
        for pattern in patterns:
            match = re.search(pattern, page_html)
            if match:
                return match.group(1)
        return None

    def verify_session(self) -> bool:
        """Check if the session is authenticated by accessing the profile page."""
        logger.info("[API] Verifying session by accessing profile page...")

        try:
            time.sleep(random.uniform(1.0, 3.0))
            response = self._make_request(
                "get",
                PROFILE_PAGE_URL,
                timeout=60,
                allow_redirects=True,
            )

            if response is None:
                logger.error("[API] No response received")
                return False

            logger.info(f"[API] Profile page status: {response.status_code}")
            logger.info(f"[API] Response size: {len(response.text)} bytes")

            if response.status_code == 403 or "Access Denied" in response.text[:500]:
                logger.error("[API] Access Denied on profile page")
                logger.info(f"[API] Snippet: {response.text[:300]}")
                return False

            if response.status_code != 200:
                logger.error(f"[API] Unexpected status code: {response.status_code}")
                return False

            # Check if we're redirected to login
            final_url = str(response.url) if hasattr(response, 'url') else ""
            if "login" in final_url.lower() or "nlogin" in final_url.lower():
                logger.error("[API] Redirected to login — cookies are invalid")
                return False

            # Try to extract user ID
            self.user_id = self._extract_user_id(response.text)
            if self.user_id:
                logger.info(f"[API] Found user ID: {self.user_id}")
            else:
                logger.warning("[API] Could not extract user ID from profile page")

            # Check for logged-in indicators
            page_lower = response.text.lower()
            if "logout" in page_lower or "my naukri" in page_lower or "profile" in page_lower:
                logger.info("[API] Session verified successfully!")
                return True

            logger.warning("[API] Could not confirm login status")
            return False

        except Exception as e:
            logger.error(f"[API] Session verification failed: {e}")
            return False

    def update_headline(self) -> bool:
        """Update the resume headline by toggling a period at the end."""
        logger.info("[API] Attempting to update headline via API...")

        try:
            # Fetch the profile page to get the current headline
            time.sleep(random.uniform(1.0, 3.0))
            response = self._make_request("get", PROFILE_PAGE_URL, timeout=60)

            if response is None or response.status_code != 200:
                status = response.status_code if response else "No response"
                logger.error(f"[API] Failed to load profile page: {status}")
                return False

            current_headline = self._extract_headline(response.text)
            if not current_headline:
                logger.error("[API] Could not extract current headline")
                logger.info(f"[API] Page snippet: {response.text[:500]}")
                return False

            logger.info(f"[API] Current headline: '{current_headline}'")

            # Toggle the period
            if current_headline.endswith("."):
                new_headline = current_headline[:-1]
            else:
                new_headline = current_headline + "."

            # Try multiple API endpoint patterns to update headline
            success = False

            # Attempt 1: Direct PUT/POST to internal API (if user_id is known)
            if self.user_id:
                success = self._try_api_headline_update(new_headline)

            # Attempt 2: Form-based POST to the profile page
            if not success:
                success = self._try_form_headline_update(new_headline)

            if success:
                logger.info(f"[API] Headline updated: '{current_headline}' -> '{new_headline}'")
            else:
                logger.error("[API] All headline update methods failed")

            return success

        except Exception as e:
            logger.error(f"[API] Headline update failed: {e}")
            return False

    def _try_api_headline_update(self, new_headline: str) -> bool:
        """Try updating headline via the internal JSON API."""
        if not self.user_id:
            return False

        url = f"https://www.naukri.com/cloudgateway-mynaukri/resman-aggregator-services/v0/users/{self.user_id}/profiles/headline"
        logger.info(f"[API] Trying JSON API: PUT {url}")

        try:
            time.sleep(random.uniform(1.0, 2.0))

            payload = {"resumeHeadline": new_headline}

            # Try PUT first
            response = self._make_request(
                "put", url,
                json=payload,
                timeout=60,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )

            if response and response.status_code in (200, 201, 204):
                logger.info("[API] Headline updated via JSON API (PUT)")
                return True

            logger.info(f"[API] PUT response: {response.status_code if response else 'None'}")

            # Try POST
            response = self._make_request(
                "post", url,
                json=payload,
                timeout=60,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )

            if response and response.status_code in (200, 201, 204):
                logger.info("[API] Headline updated via JSON API (POST)")
                return True

            logger.warning(f"[API] JSON API failed: {response.status_code if response else 'None'}")
            return False

        except Exception as e:
            logger.warning(f"[API] JSON API headline update error: {e}")
            return False

    def _try_form_headline_update(self, new_headline: str) -> bool:
        """Try updating headline via form-style POST."""
        url = "https://www.naukri.com/mnjuser/profile"
        logger.info(f"[API] Trying form POST to {url}")

        try:
            time.sleep(random.uniform(1.0, 2.0))

            payload = {
                "resumeHeadline": new_headline,
                "action": "saveHeadline",
            }

            response = self._make_request(
                "post", url,
                data=payload,
                timeout=60,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response and response.status_code in (200, 201, 204, 302):
                if response.status_code == 302 or "success" in response.text.lower():
                    logger.info("[API] Headline updated via form POST")
                    return True

            logger.warning(f"[API] Form POST failed: {response.status_code if response else 'None'}")
            return False

        except Exception as e:
            logger.warning(f"[API] Form POST headline update error: {e}")
            return False

    def update_resume(self) -> bool:
        """Upload the resume file via API."""
        logger.info("[API] Attempting to upload resume via API...")

        resume_path = config.RESUME_FILE
        if not resume_path.exists():
            logger.error(f"[API] Resume file not found: {resume_path}")
            return False

        try:
            time.sleep(random.uniform(1.0, 3.0))

            # Try multipart upload to profile page
            with open(resume_path, "rb") as f:
                files = {"file": (resume_path.name, f, "application/pdf")}
                response = self._make_request(
                    "post",
                    "https://www.naukri.com/mnjuser/profile",
                    files=files,
                    data={"action": "uploadResume"},
                    timeout=120,
                )

                if response and response.status_code in (200, 201, 204, 302):
                    logger.info("[API] Resume uploaded successfully!")
                    return True

                logger.info(f"[API] Resume upload response: {response.status_code if response else 'None'}")

            # Try the cloudgateway endpoint if user_id is available
            if self.user_id:
                url = f"https://www.naukri.com/cloudgateway-mynaukri/resman-aggregator-services/v0/users/{self.user_id}/profiles/resumeUpload"
                logger.info(f"[API] Trying cloudgateway upload: {url}")

                with open(resume_path, "rb") as f:
                    files = {"file": (resume_path.name, f, "application/pdf")}
                    response = self._make_request(
                        "post", url,
                        files=files,
                        timeout=120,
                    )

                    if response and response.status_code in (200, 201, 204):
                        logger.info("[API] Resume uploaded via cloudgateway!")
                        return True

            logger.error("[API] All resume upload methods failed")
            return False

        except Exception as e:
            logger.error(f"[API] Resume upload failed: {e}")
            return False

    def run(self, mode: str = "all") -> bool:
        """Run the API-based update process.

        Args:
            mode: One of 'all', 'resume', or 'profile'.
        """
        logger.info("=" * 50)
        logger.info(f"[API] Starting Naukri API-based Update  [mode={mode}]")
        logger.info("=" * 50)

        if not self.setup_session():
            return False

        if not self.verify_session():
            logger.error("[API] Session verification failed — cookies may be expired or IP-bound")
            return False

        success = False

        if mode in ("all", "resume"):
            if self.update_resume():
                success = True
                logger.info("[API] Resume update completed!")
            else:
                logger.error("[API] Resume update failed")

        if mode in ("all", "profile"):
            if self.update_headline():
                success = True
                logger.info("[API] Profile headline update completed!")
            else:
                logger.warning("[API] Profile headline update failed")

        logger.info("=" * 50)
        logger.info(f"[API] Update completed. Mode: {mode} | Success: {success}")
        logger.info("=" * 50)

        return success
