"""
Naukri Profile Automation Tool - Main Script

This script automates the process of updating your resume on Naukri.com
to keep your profile active and visible to recruiters.

Usage:
    python -m naukri_updater.main

Environment Variables:
    NAUKRI_EMAIL: Your Naukri.com login email
    NAUKRI_PASSWORD: Your Naukri.com password
"""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
from webdriver_manager.chrome import ChromeDriverManager

from . import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class NaukriUpdater:
    """Automates Naukri.com profile updates."""

    def __init__(self):
        self.driver = None
        self.wait = None

    def setup_driver(self):
        """Initialize Chrome WebDriver with headless options."""
        logger.info("Setting up Chrome WebDriver...")

        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Anti-detection measures
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Fix for HTTP2 protocol errors - use HTTP/1.1
        chrome_options.add_argument("--disable-http2")
        
        # Additional anti-detection
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        # Realistic user agent
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        
        # Language and accept headers
        chrome_options.add_argument("--lang=en-US,en")
        chrome_options.add_argument("--accept-lang=en-US,en;q=0.9")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute stealth scripts to avoid detection
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                window.chrome = {runtime: {}};
            """
        })

        # Set timeouts
        self.driver.implicitly_wait(config.IMPLICIT_WAIT)
        self.driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
        self.driver.set_script_timeout(config.SCRIPT_TIMEOUT)

        # Initialize explicit wait
        self.wait = WebDriverWait(self.driver, config.IMPLICIT_WAIT)

        logger.info("Chrome WebDriver initialized successfully")

    def take_screenshot(self, name: str):
        """Take a screenshot for debugging purposes."""
        try:
            config.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = config.SCREENSHOTS_DIR / f"{name}_{timestamp}.png"
            self.driver.save_screenshot(str(filepath))
            logger.info(f"Screenshot saved: {filepath}")
        except Exception as e:
            logger.warning(f"Failed to take screenshot: {e}")

    def load_cookies(self) -> bool:
        """Load cookies from environment variable to bypass login."""
        logger.info("Attempting cookie-based authentication...")
        
        cookies = config.get_cookies()
        if not cookies:
            logger.warning("No cookies available")
            return False
        
        try:
            # First navigate to the domain to set cookies
            logger.info("Navigating to Naukri.com to set cookies...")
            
            # Try navigating with error handling
            try:
                self.driver.get(config.NAUKRI_HOME_URL)
            except Exception as nav_error:
                logger.warning(f"Initial navigation error (will retry): {nav_error}")
                time.sleep(2)
                self.driver.get(config.NAUKRI_HOME_URL)
            
            time.sleep(3)
            
            self.take_screenshot("before_cookies")
            
            # Add each cookie
            cookies_added = 0
            for cookie in cookies:
                try:
                    # Remove problematic fields that Selenium doesn't accept
                    cookie_clean = {
                        'name': cookie.get('name'),
                        'value': cookie.get('value'),
                        'domain': cookie.get('domain', '.naukri.com'),
                        'path': cookie.get('path', '/'),
                    }
                    
                    # Only add if we have required fields
                    if cookie_clean['name'] and cookie_clean['value']:
                        # Handle domain - ensure it's valid for the current page
                        if 'naukri.com' in cookie_clean.get('domain', ''):
                            self.driver.add_cookie(cookie_clean)
                            cookies_added += 1
                except Exception as e:
                    logger.debug(f"Could not add cookie {cookie.get('name')}: {e}")
                    continue
            
            logger.info(f"Added {cookies_added} cookies")
            
            # Refresh to apply cookies
            time.sleep(1)
            self.driver.refresh()
            time.sleep(4)
            
            self.take_screenshot("after_cookies_refresh")
            
            # Navigate to profile with retry logic
            logger.info("Navigating to profile page...")
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.driver.get(config.NAUKRI_PROFILE_URL)
                    time.sleep(4)
                    break
                except Exception as e:
                    logger.warning(f"Profile navigation attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        # Try alternate URL
                        logger.info("Trying alternate navigation...")
                        self.driver.get("https://www.naukri.com/mnjuser/homepage")
                        time.sleep(3)
            
            self.take_screenshot("after_cookie_auth")
            
            # Check if we're on profile page (means we're logged in)
            current_url = self.driver.current_url
            logger.info(f"Current URL after cookie auth: {current_url}")
            
            if "profile" in current_url.lower() and "login" not in current_url.lower():
                logger.info("Cookie authentication successful!")
                return True
            elif "homepage" in current_url.lower() or "mnjuser" in current_url.lower():
                logger.info("Cookie authentication successful! (on homepage)")
                return True
            elif "login" in current_url.lower():
                logger.warning("Redirected to login page - cookies may be expired")
                return False
            else:
                # Could be on some other page, let's check if we see logged-in elements
                try:
                    # Look for elements that indicate we're logged in
                    self.driver.find_element(By.CSS_SELECTOR, ".nI-gNb-drawer__icon, .user-badge, [class*='logged'], .nI-gNb-sb__plc")
                    logger.info("Cookie authentication appears successful (found logged-in elements)")
                    return True
                except:
                    logger.warning("Could not verify login status")
                    return False
                    
        except Exception as e:
            logger.error(f"Cookie authentication failed: {e}")
            self.take_screenshot("cookie_auth_error")
            return False

    def find_element_with_fallback(self, selectors: list, description: str):
        """Try multiple selectors to find an element."""
        for selector in selectors:
            try:
                if selector.startswith("//"):
                    # XPath selector
                    element = self.driver.find_element(By.XPATH, selector)
                else:
                    # CSS selector
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element:
                    logger.info(f"Found {description} with selector: {selector}")
                    return element
            except NoSuchElementException:
                continue
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        return None

    def login(self) -> bool:
        """Log in to Naukri.com."""
        logger.info("Navigating to Naukri login page...")

        try:
            self.driver.get(config.NAUKRI_LOGIN_URL)
            time.sleep(3)  # Wait for page to fully load
            
            # Take screenshot of login page for debugging
            self.take_screenshot("login_page")

            # Multiple selectors for email input (in order of preference)
            email_selectors = [
                "input[placeholder='Enter Email ID / Username']",
                "input[placeholder*='Email']",
                "input[type='text'][name*='email']",
                "input[type='email']",
                "#usernameField",
                "//input[contains(@placeholder, 'Email')]",
                "//input[@type='text']",
            ]
            
            # Multiple selectors for password input
            password_selectors = [
                "input[placeholder='Enter Password']",
                "input[placeholder*='Password']",
                "input[type='password']",
                "#passwordField",
                "//input[@type='password']",
            ]
            
            # Multiple selectors for login button
            login_button_selectors = [
                "button[type='submit']",
                "button.loginButton",
                "button[class*='login']",
                "input[type='submit']",
                "//button[@type='submit']",
                "//button[contains(text(), 'Login')]",
            ]

            # Find and fill email
            logger.info("Looking for email input...")
            email_input = self.find_element_with_fallback(email_selectors, "email input")
            
            if not email_input:
                # Try waiting for it
                try:
                    email_input = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[type='email']"))
                    )
                    logger.info("Found email input via generic wait")
                except:
                    pass
            
            if not email_input:
                logger.error("Could not find email input field")
                self.take_screenshot("no_email_input")
                return False
            
            logger.info("Entering email...")
            email_input.clear()
            email_input.send_keys(config.NAUKRI_EMAIL)
            time.sleep(0.5)

            # Find and fill password
            logger.info("Looking for password input...")
            password_input = self.find_element_with_fallback(password_selectors, "password input")
            
            if not password_input:
                logger.error("Could not find password input field")
                self.take_screenshot("no_password_input")
                return False
            
            logger.info("Entering password...")
            password_input.clear()
            password_input.send_keys(config.NAUKRI_PASSWORD)
            time.sleep(0.5)

            # Find and click login button
            logger.info("Looking for login button...")
            login_button = self.find_element_with_fallback(login_button_selectors, "login button")
            
            if not login_button:
                logger.error("Could not find login button")
                self.take_screenshot("no_login_button")
                return False
            
            logger.info("Clicking login button...")
            login_button.click()

            # Wait for login to complete
            time.sleep(5)
            
            # Take screenshot after login attempt
            self.take_screenshot("after_login")

            # Check if login was successful
            current_url = self.driver.current_url
            logger.info(f"Current URL after login: {current_url}")
            
            # Success if we're no longer on login page
            if "login" not in current_url.lower() and "nlogin" not in current_url.lower():
                logger.info("Login successful! (redirected away from login page)")
                return True
            
            # Check for error messages
            try:
                error_selectors = [".error-msg", ".err-msg", ".error", "[class*='error']"]
                for sel in error_selectors:
                    try:
                        error_msg = self.driver.find_element(By.CSS_SELECTOR, sel)
                        if error_msg.is_displayed() and error_msg.text:
                            logger.error(f"Login error message: {error_msg.text}")
                            return False
                    except:
                        continue
            except:
                pass
            
            # If no errors found, assume success (some pages stay on same URL)
            logger.info("No login errors detected, assuming success")
            return True

        except TimeoutException:
            logger.error("Timeout waiting for login page elements")
            self.take_screenshot("login_timeout")
            return False
        except Exception as e:
            logger.error(f"Login failed with error: {e}")
            self.take_screenshot("login_error")
            return False

    def navigate_to_profile(self) -> bool:
        """Navigate to the profile page."""
        logger.info("Navigating to profile page...")

        try:
            self.driver.get(config.NAUKRI_PROFILE_URL)
            time.sleep(3)

            logger.info(f"Current URL: {self.driver.current_url}")

            if "profile" in self.driver.current_url.lower():
                logger.info("Successfully navigated to profile page")
                return True
            else:
                logger.warning("May not be on profile page, attempting to continue...")
                return True

        except Exception as e:
            logger.error(f"Failed to navigate to profile: {e}")
            self.take_screenshot("profile_navigation_error")
            return False

    def update_resume(self) -> bool:
        """Upload/update the resume on Naukri."""
        logger.info("Attempting to update resume...")

        try:
            # Wait for page to load
            time.sleep(3)
            
            # Look for file input element (may be hidden)
            # Naukri uses different selectors, try multiple approaches
            file_input = None
            
            # Try to find file input directly
            file_input_selectors = [
                "input[type='file']",
                "input[accept*='.pdf']",
                "input[accept*='.doc']",
                "#attachCV",
                ".upload-resume input[type='file']",
            ]
            
            for selector in file_input_selectors:
                try:
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if inputs:
                        file_input = inputs[0]
                        logger.info(f"Found file input with selector: {selector}")
                        break
                except:
                    continue

            if file_input is None:
                # Try to click on resume update button/section first
                try:
                    # Look for the resume section and click to expand/enable upload
                    resume_section_selectors = [
                        ".widgetHead.resumeWidget",
                        "[class*='resume']",
                        ".row.resumeWidget",
                        "a[title*='resume']",
                        ".updateBtn",
                    ]
                    
                    for selector in resume_section_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for elem in elements:
                                if elem.is_displayed():
                                    elem.click()
                                    time.sleep(2)
                                    break
                        except:
                            continue

                    # Try finding file input again after clicking
                    for selector in file_input_selectors:
                        try:
                            inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if inputs:
                                file_input = inputs[0]
                                break
                        except:
                            continue
                except Exception as e:
                    logger.warning(f"Could not click resume section: {e}")

            if file_input is None:
                # Last resort - use JavaScript to find hidden inputs
                try:
                    file_input = self.driver.execute_script(
                        "return document.querySelector('input[type=file]')"
                    )
                except:
                    pass

            if file_input is None:
                logger.error("Could not find file input element")
                self.take_screenshot("no_file_input")
                
                # Log page source for debugging
                logger.info("Page title: " + self.driver.title)
                return False

            # Make the file input visible if hidden
            self.driver.execute_script(
                "arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible';",
                file_input,
            )

            # Upload the resume file
            resume_path = str(config.RESUME_FILE.absolute())
            logger.info(f"Uploading resume from: {resume_path}")
            
            file_input.send_keys(resume_path)
            
            # Wait for upload to complete
            time.sleep(5)

            logger.info("Resume upload completed successfully!")
            self.take_screenshot("resume_upload_success")
            return True

        except Exception as e:
            logger.error(f"Failed to update resume: {e}")
            self.take_screenshot("resume_update_error")
            return False

    def update_headline(self) -> bool:
        """Update resume headline by toggling a period (optional visibility boost)."""
        logger.info("Attempting to update resume headline...")

        try:
            # Find the headline edit button
            edit_btn = self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, config.SELECTORS["edit_headline_btn"])
                )
            )
            edit_btn.click()
            time.sleep(2)

            # Find the headline textarea
            headline_textarea = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, config.SELECTORS["headline_textarea"])
                )
            )

            # Get current headline and toggle period
            current_headline = headline_textarea.get_attribute("value")
            
            if current_headline.endswith("."):
                new_headline = current_headline[:-1]
            else:
                new_headline = current_headline + "."

            # Update headline
            headline_textarea.clear()
            headline_textarea.send_keys(new_headline)

            # Save changes
            save_btn = self.driver.find_element(
                By.CSS_SELECTOR, config.SELECTORS["save_headline_btn"]
            )
            save_btn.click()
            time.sleep(2)

            logger.info(f"Headline updated: '{current_headline}' -> '{new_headline}'")
            return True

        except Exception as e:
            logger.warning(f"Could not update headline (non-critical): {e}")
            return False

    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")

    def run(self) -> bool:
        """Run the complete update process."""
        logger.info("=" * 50)
        logger.info("Starting Naukri Profile Update")
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 50)

        # Validate configuration
        errors = config.validate_config()
        if errors:
            for error in errors:
                logger.error(error)
            return False

        success = False
        logged_in = False

        try:
            # Setup browser
            self.setup_driver()

            # Try cookie-based authentication first (bypasses OTP)
            if config.use_cookie_auth():
                logger.info("Cookie authentication is available, trying it first...")
                logged_in = self.load_cookies()
                if logged_in:
                    logger.info("Successfully authenticated using cookies!")
                else:
                    logger.warning("Cookie authentication failed, will try password login...")
            
            # Fall back to password login if cookies didn't work
            if not logged_in:
                if config.NAUKRI_EMAIL and config.NAUKRI_PASSWORD:
                    logger.info("Attempting password-based login...")
                    if not self.login():
                        logger.error("Login failed, aborting...")
                        return False
                    logged_in = True
                else:
                    logger.error("No valid authentication method available!")
                    return False

            # Navigate to profile (if not already there from cookie auth)
            if not self.navigate_to_profile():
                logger.error("Failed to navigate to profile, aborting...")
                return False

            # Update resume
            if self.update_resume():
                success = True
                logger.info("Resume update completed successfully!")
            else:
                logger.error("Resume update failed")

            # Optionally update headline (uncomment if desired)
            # self.update_headline()

        except WebDriverException as e:
            logger.error(f"WebDriver error: {e}")
            self.take_screenshot("webdriver_error")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.take_screenshot("unexpected_error")
        finally:
            self.cleanup()

        logger.info("=" * 50)
        logger.info(f"Update completed. Success: {success}")
        logger.info("=" * 50)

        return success


def main():
    """Main entry point."""
    updater = NaukriUpdater()
    success = updater.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
