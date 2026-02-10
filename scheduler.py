"""
Scheduler for Naukri Profile Updater - Railway Deployment

Runs the Naukri profile updater every hour with a random delay (1-15 min),
only on Monday to Saturday, between 6 AM and 8 PM IST.
This is the entry point for Railway deployment.
"""

import logging
import random
import sys
import time
from datetime import datetime

import pytz
import schedule

IST = pytz.timezone("Asia/Kolkata")

# Allowed days: Monday(0) to Saturday(5)
ALLOWED_DAYS = {0, 1, 2, 3, 4, 5}
START_HOUR = 6   # 6 AM IST
END_HOUR = 20    # 8 PM IST

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def is_within_allowed_window():
    """Check if current IST time is within the allowed day/time window."""
    now_ist = datetime.now(IST)
    if now_ist.weekday() not in ALLOWED_DAYS:
        logger.info(f"Skipping: Today is {now_ist.strftime('%A')} (Sunday) — not a scheduled day.")
        return False
    if not (START_HOUR <= now_ist.hour < END_HOUR):
        logger.info(f"Skipping: Current IST time {now_ist.strftime('%H:%M')} is outside 6 AM – 8 PM window.")
        return False
    return True


def run_updater():
    """Run the Naukri profile updater with a random delay."""
    if not is_within_allowed_window():
        return

    # Random delay between 1 and 15 minutes to avoid detection patterns
    delay_minutes = random.randint(1, 15)
    delay_seconds = delay_minutes * 60
    logger.info(f"Adding random delay of {delay_minutes} minute(s) before running...")
    time.sleep(delay_seconds)

    # Re-check window after the delay (in case we drifted past 8 PM)
    if not is_within_allowed_window():
        return

    try:
        now_ist = datetime.now(IST)
        logger.info("=" * 60)
        logger.info(f"Starting scheduled update at {now_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info("=" * 60)

        from naukri_updater.main import NaukriUpdater

        updater = NaukriUpdater()
        success = updater.run()

        if success:
            logger.info("Profile update completed successfully!")
        else:
            logger.warning("Profile update finished with errors.")

    except Exception as e:
        logger.error(f"Update failed with exception: {e}", exc_info=True)

    logger.info(f"Next run scheduled at: {schedule.next_run()}")


def main():
    """Main scheduler entry point."""
    now_ist = datetime.now(IST)
    logger.info("=" * 60)
    logger.info("Naukri Profile Updater - Railway Scheduler")
    logger.info("Schedule: Every 1 hour (+ random 1-15 min delay)")
    logger.info("Window : Mon–Sat, 6 AM – 8 PM IST")
    logger.info(f"Started at: {now_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info("=" * 60)

    # Schedule the job every 1 hour
    schedule.every(1).hours.do(run_updater)

    # Run immediately on startup (if within window)
    logger.info("Running initial update on startup...")
    run_updater()

    # Keep running forever
    logger.info("Scheduler is now running. Waiting for next scheduled job...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every 60 seconds


if __name__ == "__main__":
    main()
