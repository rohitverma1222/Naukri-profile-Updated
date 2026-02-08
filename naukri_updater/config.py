"""
Configuration settings for Naukri Profile Automation Tool
"""

import os
import json
from pathlib import Path

# Naukri.com URLs
NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"
NAUKRI_PROFILE_URL = "https://www.naukri.com/mnjuser/profile"
NAUKRI_HOME_URL = "https://www.naukri.com"

# Credentials (loaded from environment variables)
NAUKRI_EMAIL = os.environ.get("NAUKRI_EMAIL", "")
NAUKRI_PASSWORD = os.environ.get("NAUKRI_PASSWORD", "")

# Cookie-based authentication (preferred method to bypass OTP)
NAUKRI_COOKIES_JSON = os.environ.get("NAUKRI_COOKIES", "")

def get_cookies():
    """Parse cookies from environment variable."""
    if not NAUKRI_COOKIES_JSON:
        return None
    try:
        cookies = json.loads(NAUKRI_COOKIES_JSON)
        return cookies if isinstance(cookies, list) else None
    except json.JSONDecodeError:
        return None

# File paths
PROJECT_ROOT = Path(__file__).parent.parent
RESUME_DIR = PROJECT_ROOT / "resume"
RESUME_FILE = RESUME_DIR / "resume.pdf"

# Screenshots directory for debugging
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"

# Selenium settings
IMPLICIT_WAIT = 15  # seconds
PAGE_LOAD_TIMEOUT = 60  # seconds
SCRIPT_TIMEOUT = 60  # seconds

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# CSS Selectors for Naukri.com (updated to match current site)
SELECTORS = {
    # Login page selectors
    "email_input": "input[placeholder='Enter Email ID / Username']",
    "password_input": "input[placeholder='Enter Password']",
    "login_button": "button[type='submit']",
    
    # Alternative selectors (fallbacks)
    "email_input_alt": "#usernameField",
    "password_input_alt": "#passwordField",
    
    # Profile page selectors
    "profile_photo": ".nI-gNb-drawer__icon",
    "view_profile": "a[href*='/mnjuser/profile']",
    "resume_section": ".widgetHead.resumeWidget",
    "upload_resume_input": "input[type='file']",
    "update_resume_btn": "input[type='file'][accept*='.doc']",
    "resume_headline": ".row.resumeHeadline .txt-bold",
    "edit_headline_btn": ".resumeHeadline .pencilIcon",
    "headline_textarea": "textarea[name='resumeHeadline']",
    "save_headline_btn": "button.btn-dark-ot",
}

# Validate required configuration
def validate_config():
    """Validate that required environment variables are set."""
    errors = []
    
    # Check if we have cookies OR credentials
    cookies = get_cookies()
    has_cookies = cookies is not None and len(cookies) > 0
    has_credentials = NAUKRI_EMAIL and NAUKRI_PASSWORD
    
    if not has_cookies and not has_credentials:
        errors.append(
            "Either NAUKRI_COOKIES or both NAUKRI_EMAIL and NAUKRI_PASSWORD must be set. "
            "NAUKRI_COOKIES is recommended to bypass OTP."
        )
    
    if not RESUME_FILE.exists():
        errors.append(f"Resume file not found at: {RESUME_FILE}")
    
    return errors

def use_cookie_auth():
    """Check if cookie-based authentication should be used."""
    cookies = get_cookies()
    return cookies is not None and len(cookies) > 0

