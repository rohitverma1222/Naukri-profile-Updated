import os
import sys
from pathlib import Path

# Mock required env vars
os.environ["NAUKRI_EMAIL"] = "test@example.com"
os.environ["NAUKRI_PASSWORD"] = "password"

# Add the project directory to sys.path
sys.path.append("/home/rohit/Desktop/Project/bbk")

from naukri_updater import config

def test_config():
    print(f"Default SCREENSHOTS_ENABLED: {config.SCREENSHOTS_ENABLED}")
    
    # Reload config with different env vars
    import importlib
    
    print("\nSetting ENV=production")
    os.environ["ENV"] = "production"
    # Need to clear ENABLE_SCREENSHOTS if it was set
    if "ENABLE_SCREENSHOTS" in os.environ:
        del os.environ["ENABLE_SCREENSHOTS"]
    importlib.reload(config)
    print(f"SCREENSHOTS_ENABLED in production: {config.SCREENSHOTS_ENABLED}")
    
    print("\nSetting RENDER=true")
    os.environ["ENV"] = ""
    os.environ["RENDER"] = "true"
    importlib.reload(config)
    print(f"SCREENSHOTS_ENABLED on Render: {config.SCREENSHOTS_ENABLED}")
    
    print("\nSetting ENABLE_SCREENSHOTS=true in production")
    os.environ["ENV"] = "production"
    os.environ["ENABLE_SCREENSHOTS"] = "true"
    importlib.reload(config)
    print(f"SCREENSHOTS_ENABLED (overridden): {config.SCREENSHOTS_ENABLED}")

if __name__ == "__main__":
    test_config()
