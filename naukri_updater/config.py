"""
Configuration settings for Naukri Profile Automation Tool
"""

import os
from pathlib import Path

# Naukri.com URLs
NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"
NAUKRI_PROFILE_URL = "https://www.naukri.com/mnjuser/profile"

# Credentials (loaded from environment variables)
NAUKRI_EMAIL = os.environ.get("NAUKRI_EMAIL", "")
NAUKRI_PASSWORD = os.environ.get("NAUKRI_PASSWORD", "")

# File paths
PROJECT_ROOT = Path(__file__).parent.parent
RESUME_DIR = PROJECT_ROOT / "resume"
RESUME_FILE = RESUME_DIR / "resume.pdf"

# Screenshots directory for debugging
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"

# Selenium settings
IMPLICIT_WAIT = 10  # seconds
PAGE_LOAD_TIMEOUT = 30  # seconds
SCRIPT_TIMEOUT = 30  # seconds

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
    
    if not NAUKRI_EMAIL:
        errors.append("NAUKRI_EMAIL environment variable is not set")
    
    if not NAUKRI_PASSWORD:
        errors.append("NAUKRI_PASSWORD environment variable is not set")
    
    if not RESUME_FILE.exists():
        errors.append(f"Resume file not found at: {RESUME_FILE}")
    
    return errors
