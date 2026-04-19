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
import argparse
import random
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
# Selenium 4.6+ has built-in Selenium Manager — no need for webdriver-manager

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
        
        # Re-enabling HTTP/2 as modern browsers use it; disabling it can be a bot signal
        # chrome_options.add_argument("--disable-http2")
        
        # Additional anti-detection
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        # Modern realistic User Agent (reflecting April 2026 version: Chrome 147)
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
        )
        
        # Client Hints (essential for modern anti-bot bypass)
        chrome_options.add_argument('--sec-ch-ua="Google Chrome";v="147", "Chromium";v="147", "Not(A:Brand)";v="24"')
        chrome_options.add_argument('--sec-ch-ua-mobile=?0')
        chrome_options.add_argument('--sec-ch-ua-platform="Windows"')
        
        # Language and accept headers
        chrome_options.add_argument("--lang=en-US,en")
        chrome_options.add_argument("--accept-lang=en-US,en;q=0.9")

        # Proxy configuration (Scrape.do residential proxy to bypass Akamai)
        proxy_url = config.get_proxy_url()
        if proxy_url:
            chrome_options.add_argument(f"--proxy-server={proxy_url}")
            logger.info("Scrape.do residential proxy enabled")
        else:
            logger.info("No proxy configured (running direct)")

        # Selenium 4.6+ automatically manages ChromeDriver via built-in Selenium Manager
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Execute comprehensive stealth scripts to mask automation and match modern Chrome behavior
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                // Overwrite the 'webdriver' property
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

                // Overwrite the 'plugins' property
                Object.defineProperty(navigator, 'plugins', {get: () => [
                    { name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer' },
                    { name: 'Chromium PDF Viewer', filename: 'internal-pdf-viewer' },
                    { name: 'Microsoft Edge PDF Viewer', filename: 'internal-pdf-viewer' },
                    { name: 'PDF Viewer', filename: 'internal-pdf-viewer' },
                    { name: 'WebKit built-in PDF', filename: 'internal-pdf-viewer' }
                ]});

                // Overwrite languages
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});

                // Spoof Chrome-specific properties
                window.chrome = {
                    runtime: {},
                    app: {
                        isInstalled: false,
                        InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
                        RunningState: { CANNOT_RUN: 'cannot_run', RUNNING: 'running', CAN_RUN: 'can_run' }
                    },
                    loadTimes: () => ({}),
                    csi: () => ({})
                };

                // Spoof hardwareConcurrency and deviceMemory
                Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
                Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});

                // Mock WebGL fingerprints (basic)
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) return 'Intel Inc.';
                    if (parameter === 37446) return 'Intel(R) Iris(TM) Plus Graphics 640';
                    return getParameter.apply(this, arguments);
                };
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
        """Take a screenshot and save page source for debugging purposes."""
        if not config.SCREENSHOTS_ENABLED:
            return
            
        try:
            config.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save screenshot
            screenshot_path = config.SCREENSHOTS_DIR / f"{name}_{timestamp}.png"
            self.driver.save_screenshot(str(screenshot_path))
            
            # Save page source
            source_path = config.SCREENSHOTS_DIR / f"{name}_{timestamp}.html"
            with open(source_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
                
            logger.info(f"Debug files saved: {name}_{timestamp} (.png and .html)")
        except Exception as e:
            logger.warning(f"Failed to save debug info: {e}")

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
            
            self.driver.get(config.NAUKRI_HOME_URL)
            time.sleep(5)
            
            self.take_screenshot("before_cookies")
            
            # Add each cookie using Selenium
            cookies_added = 0
            for cookie in cookies:
                try:
                    # Clean cookie for Selenium
                    cookie_clean = {
                        'name': cookie.get('name'),
                        'value': cookie.get('value'),
                        'path': cookie.get('path', '/'),
                    }
                    
                    # Set domain appropriately
                    domain = cookie.get('domain', '')
                    if domain.startswith('.'):
                        cookie_clean['domain'] = domain
                    
                    if cookie_clean['name'] and cookie_clean['value']:
                        try:
                            self.driver.add_cookie(cookie_clean)
                            cookies_added += 1
                        except Exception as ce:
                            # Try without domain
                            try:
                                del cookie_clean['domain']
                                self.driver.add_cookie(cookie_clean)
                                cookies_added += 1
                            except:
                                pass
                except Exception as e:
                    continue
            
            logger.info(f"Added {cookies_added} cookies")
            
            # Also set cookies via JavaScript as backup
            try:
                for cookie in cookies:
                    name = cookie.get('name', '')
                    value = cookie.get('value', '')
                    if name and value:
                        self.driver.execute_script(
                            f"document.cookie = '{name}={value}; path=/; domain=.naukri.com';"
                        )
            except Exception as js_err:
                logger.debug(f"JS cookie setting failed: {js_err}")
            
            # Navigate to the dashboard (less guarded than direct profile access)
            logger.info("Navigating to user dashboard to verify session...")
            try:
                # Add a brief human-like pause before navigation
                time.sleep(random.uniform(2.0, 4.0))
                self.driver.get("https://www.naukri.com/mnjuser/homepage")
                # Longer wait for dynamic content to load on dashboard
                time.sleep(random.uniform(7.0, 10.0))
            except Exception as e:
                logger.warning(f"Dashboard navigation error: {e}")
                # Try generic user area instead
                self.driver.get("https://www.naukri.com/mnjuser/homepage")
                time.sleep(10)
            
            # Check for Access Denied immediately
            page_title = self.driver.title
            if "Access Denied" in page_title or "Access Denied" in self.driver.page_source:
                logger.warning(f"Access Denied detected on dashboard load. Title: {page_title}")
                snippet = self.driver.page_source[:300].replace('\n', ' ')
                logger.info(f"Page content snippet: {snippet}")
                
                logger.info("Access Denied! Attempting to navigate back to Home and try again...")
                self.driver.get(config.NAUKRI_HOME_URL)
                time.sleep(random.uniform(15.0, 20.0))
                
                # Check if we can see the "My Naukri" or logout even on home
                if "logout" in self.driver.page_source.lower() or "my naukri" in self.driver.page_source.lower():
                    logger.info("Session verified on Home page after Access Denied redirect")
                else:
                    logger.info("Attempting one last refresh of the dashboard...")
                    self.driver.get("https://www.naukri.com/mnjuser/homepage")
                    time.sleep(10)

            self.take_screenshot("after_dashboard_navigation")
            
            # Check if we're logged in by looking at the page content
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            logger.info(f"Current URL: {current_url}")
            
            # Check for login indicators in URL
            if "login" in current_url.lower() or "nlogin" in current_url.lower():
                logger.warning("Redirected to login - cookies are invalid or IP-bound")
                logger.info("Note: Naukri may block cookies from different IPs for security")
                return False
            
            # Check for login indicators in page
            if "logout" in page_source or "my naukri" in page_source:
                logger.info("Cookie authentication successful! (found logout/my naukri)")
                return True
            
            # Check for profile-specific content
            if "profile" in current_url.lower() and "edit" in page_source:
                logger.info("Cookie authentication successful! (on profile page)")
                return True
            
            # Check if we see the login/register buttons (means NOT logged in)
            try:
                login_btn = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='login'], button:contains('Login')")
                if login_btn and len(login_btn) > 0:
                    # Check if there's also a user menu (might be both visible)
                    user_menu = self.driver.find_elements(By.CSS_SELECTOR, ".nI-gNb-drawer__icon, [class*='user'], .user-name")
                    if user_menu and len(user_menu) > 0:
                        logger.info("Cookie authentication appears successful")
                        return True
                    else:
                        logger.warning("Not logged in - login button visible, no user menu")
                        return False
            except:
                pass
            
            # Default: check URL patterns
            if "mnjuser" in current_url.lower():
                logger.info("Cookie authentication successful! (on user area)")
                return True
                
            logger.warning("Could not verify login status, assuming failure")
            return False
                    
        except Exception as e:
            logger.error(f"Cookie authentication failed: {e}")
            self.take_screenshot("cookie_auth_error")
            return False

    def find_element_with_fallback(self, selectors: list, description: str, timeout: int = 5):
        """Try multiple selectors to find an element with a shorter per-selector timeout."""
        # Temporarily reduce implicit wait to make fallback faster
        self.driver.implicitly_wait(2)
        
        try:
            for selector in selectors:
                try:
                    if selector.startswith("//"):
                        element = self.driver.find_element(By.XPATH, selector)
                    else:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if element and element.is_displayed():
                        logger.info(f"Found {description} with selector: {selector}")
                        return element
                except NoSuchElementException:
                    continue
                except Exception:
                    continue
            return None
        finally:
            # Restore original implicit wait
            self.driver.implicitly_wait(config.IMPLICIT_WAIT)

    def scroll_to_element(self, element):
        """Scroll element into view."""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(1)
        except Exception as e:
            logger.warning(f"Failed to scroll to element: {e}")


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
        """Navigate to the profile page with smart redundancy check."""
        current_url = self.driver.current_url
        if config.NAUKRI_PROFILE_URL in current_url:
            logger.info("Already on profile page, checking for stability...")
            
            # Check for 'Access Denied' even if URL is correct
            if "Access Denied" in self.driver.title:
                logger.warning("Page shows Access Denied! Attempting to re-load via Home...")
                self.driver.get(config.NAUKRI_HOME_URL)
                time.sleep(random.uniform(3.0, 5.0))
                self.driver.get(config.NAUKRI_PROFILE_URL)
                time.sleep(5)
            else:
                return True

        logger.info("Navigating to profile page...")
        try:
            # Mimic human scroll before navigation if on homepage
            if "homepage" in self.driver.current_url:
                self.driver.execute_script("window.scrollTo(0, 300);")
                time.sleep(2)

            self.driver.get(config.NAUKRI_PROFILE_URL)
            time.sleep(random.uniform(5.0, 8.0))

            current_url = self.driver.current_url
            logger.info(f"Current URL: {current_url}")

            if "profile" in current_url.lower():
                if "Access Denied" in self.driver.title:
                    logger.error("Access Denied on profile page load")
                    snippet = self.driver.page_source[:300].replace('\n', ' ')
                    logger.info(f"Page content snippet: {snippet}")
                    return False
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
        """Update resume headline by toggling a period (visibility boost).

        This triggers a profile-modified timestamp update on Naukri,
        keeping the profile fresh for recruiters.
        """
        logger.info("Attempting to update resume headline...")

        try:
            # ── 1. Click the edit (pencil) icon ──
            edit_selectors = [
                config.SELECTORS["edit_headline_btn"],  # #lazyResumeHead .edit.icon
                "#lazyResumeHead .edit",
                ".resumeHeadline .edit.icon",
                ".resumeHeadline .pencilIcon",
                "//span[contains(@class,'edit') and ancestor::*[contains(@class,'resumeHeadline')]]",
            ]
            edit_btn = self.find_element_with_fallback(edit_selectors, "headline edit button")
            if not edit_btn:
                # Last resort – wait for it
                try:
                    edit_btn = self.wait.until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "#lazyResumeHead .edit.icon, .resumeHeadline .edit")
                        )
                    )
                except Exception:
                    pass

            if not edit_btn:
                logger.warning("Could not find headline edit button")
                # Log current URL and title for context
                logger.info(f"URL: {self.driver.current_url} | Title: {self.driver.title}")
                self.take_screenshot("no_headline_edit_btn")
                return False

            # Scroll to button and click
            self.scroll_to_element(edit_btn)
            edit_btn.click()
            time.sleep(2)
            self.take_screenshot("headline_edit_opened")

            # ── 2. Find the headline textarea ──
            textarea_selectors = [
                config.SELECTORS["headline_textarea"],  # #resumeHeadlineTxt
                "textarea[name='resumeHeadline']",
                ".resumeHeadlineEdit textarea",
                "textarea.fue__text-area",
            ]
            headline_textarea = self.find_element_with_fallback(textarea_selectors, "headline textarea")
            if not headline_textarea:
                try:
                    headline_textarea = self.wait.until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "#resumeHeadlineTxt, textarea[name='resumeHeadline']")
                        )
                    )
                except Exception:
                    pass

            if not headline_textarea:
                logger.warning("Could not find headline textarea")
                self.take_screenshot("no_headline_textarea")
                return False

            # ── 3. Toggle a period at the end ──
            current_headline = headline_textarea.get_attribute("value") or ""

            if current_headline.endswith("."):
                new_headline = current_headline[:-1]
            else:
                new_headline = current_headline + "."

            headline_textarea.clear()
            headline_textarea.send_keys(new_headline)
            time.sleep(1)

            # ── 4. Click Save ──
            save_selectors = [
                config.SELECTORS["save_headline_btn"],  # .resumeHeadlineEdit button.btn-dark-ot
                ".resumeHeadlineEdit button[type='submit']",
                "button.btn-dark-ot",
                ".resumeHeadlineEdit button",
                "//button[contains(text(),'Save')]",
            ]
            save_btn = self.find_element_with_fallback(save_selectors, "headline save button")
            if not save_btn:
                try:
                    save_btn = self.wait.until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, ".resumeHeadlineEdit button.btn-dark-ot, button.btn-dark-ot")
                        )
                    )
                except Exception:
                    pass

            if not save_btn:
                logger.warning("Could not find headline save button")
                self.take_screenshot("no_headline_save_btn")
                return False

            save_btn.click()
            time.sleep(2)
            self.take_screenshot("headline_saved")

            logger.info(f"Headline updated: '{current_headline}' -> '{new_headline}'")
            return True

        except Exception as e:
            logger.warning(f"Could not update headline (non-critical): {e}")
            self.take_screenshot("headline_update_error")
            return False

    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")

    def run(self, mode: str = "all") -> bool:
        """Run the update process.

        Args:
            mode: One of 'all', 'resume', or 'profile'.
                  - 'resume' : only uploads the resume file.
                  - 'profile': only toggles the headline.
                  - 'all'    : does both (default).
        """
        logger.info("=" * 50)
        logger.info(f"Starting Naukri Profile Update  [mode={mode}]")
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
        selenium_failed = False

        try:
            # Setup browser
            self.setup_driver()

            # Try cookie-based authentication first (bypasses login)
            if config.use_cookie_auth():
                logger.info("Cookie authentication is available, trying it...")
                logged_in = self.load_cookies()
                if not logged_in:
                    logger.warning("Cookie authentication via Selenium failed!")
                    selenium_failed = True
            elif config.NAUKRI_EMAIL and config.NAUKRI_PASSWORD:
                logger.info("Attempting password-based login...")
                if not self.login():
                    logger.error("Login failed, aborting...")
                    return False
                logged_in = True
            else:
                logger.error("No valid authentication method available! Provide cookies or credentials.")
                return False

            if logged_in:
                # Ensure we're on the profile page
                if not self.navigate_to_profile():
                    logger.warning("Failed to navigate to profile via Selenium")
                    selenium_failed = True
                else:
                    # ---- Resume update (daily) ----
                    if mode in ("all", "resume"):
                        if self.update_resume():
                            success = True
                            logger.info("Resume update completed successfully!")
                        else:
                            logger.error("Resume update failed")

                    # ---- Profile / headline update (hourly) ----
                    if mode in ("all", "profile"):
                        if self.update_headline():
                            success = True
                            logger.info("Profile headline update completed successfully!")
                        else:
                            logger.warning("Profile headline update failed (non-critical)")

        except WebDriverException as e:
            logger.error(f"WebDriver error: {e}")
            self.take_screenshot("webdriver_error")
            selenium_failed = True
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.take_screenshot("unexpected_error")
            selenium_failed = True
        finally:
            self.cleanup()

        # ── API Fallback ──
        # If Selenium failed (e.g. Access Denied from Akamai on datacenter IPs),
        # try direct HTTP API calls with TLS impersonation.
        if selenium_failed and not success:
            logger.info("=" * 50)
            logger.info("Selenium approach failed — trying API fallback with curl_cffi...")
            logger.info("=" * 50)
            try:
                from .api_client import NaukriAPIClient
                api_client = NaukriAPIClient()
                success = api_client.run(mode=mode)
            except ImportError:
                logger.error("curl_cffi is not installed. Cannot use API fallback.")
                logger.error("Install it with: pip install curl_cffi")
            except Exception as e:
                logger.error(f"API fallback also failed: {e}")

        logger.info("=" * 50)
        logger.info(f"Update completed. Mode: {mode} | Success: {success}")
        logger.info("=" * 50)

        return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Naukri Profile Automation Tool")
    parser.add_argument(
        "--mode", 
        choices=["all", "resume", "profile"], 
        default="all",
        help="Update mode: 'resume', 'profile', or 'all' (default)"
    )
    args = parser.parse_args()

    updater = NaukriUpdater()
    success = updater.run(mode=args.mode)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
