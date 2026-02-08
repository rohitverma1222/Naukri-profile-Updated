"""
Cookie Export Utility for Naukri Automation

This script helps you export cookies from your browser after logging into Naukri.
Run this script locally, then copy the output to use as a GitHub secret.

Method 1: Using browser extension (Recommended)
1. Install "Cookie-Editor" extension in Chrome/Firefox
2. Log in to Naukri.com
3. Click the Cookie-Editor icon
4. Click "Export" -> "Export as JSON"
5. Save the JSON and add it as NAUKRI_COOKIES secret in GitHub

Method 2: Using this script with Selenium (Interactive)
1. Run: python export_cookies.py
2. A browser will open - log in to Naukri manually (with OTP)
3. After login, press Enter in the terminal
4. Cookies will be saved and printed for you to copy
"""

import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


def export_cookies():
    """Open browser, let user login, then export cookies."""
    print("=" * 60)
    print("Naukri Cookie Export Utility")
    print("=" * 60)
    print()
    print("A Chrome browser will open. Please:")
    print("1. Log in to Naukri.com (complete OTP verification)")
    print("2. Once logged in, come back here and press Enter")
    print()
    
    # Setup Chrome (visible, not headless)
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Navigate to Naukri
        driver.get("https://www.naukri.com/nlogin/login")
        
        print("Browser opened. Please log in to Naukri.com...")
        print()
        input("Press ENTER after you have successfully logged in...")
        
        # Give a moment for any final redirects
        time.sleep(2)
        
        # Get all cookies
        cookies = driver.get_cookies()
        
        # Save to file
        cookies_file = Path("naukri_cookies.json")
        with open(cookies_file, "w") as f:
            json.dump(cookies, f, indent=2)
        
        # Also print the JSON for easy copying
        cookies_json = json.dumps(cookies)
        
        print()
        print("=" * 60)
        print("SUCCESS! Cookies exported.")
        print("=" * 60)
        print()
        print(f"Cookies saved to: {cookies_file.absolute()}")
        print()
        print("=" * 60)
        print("COPY THE FOLLOWING JSON (for GitHub secret NAUKRI_COOKIES):")
        print("=" * 60)
        print()
        print(cookies_json)
        print()
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Go to your GitHub repo -> Settings -> Secrets -> Actions")
        print("2. Create a new secret named: NAUKRI_COOKIES")
        print("3. Paste the JSON above as the value")
        print("4. Run the workflow again!")
        print()
        
    finally:
        driver.quit()


if __name__ == "__main__":
    export_cookies()
