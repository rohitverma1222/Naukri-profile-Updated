"""
Scheduler for Naukri Profile Updater - Railway Deployment

Schedule:
  • Resume upload  → once per day at 7:00 AM IST (+ random 1-15 min delay)
  • Profile update → every 1 hour (+ random 1-15 min delay)

Runs only Monday–Saturday, 6 AM – 6 PM IST.
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
END_HOUR = 18    # 6 PM IST

# Morning hour for the daily resume upload
RESUME_UPLOAD_TIME = "07:00"  # 7 AM IST

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
        logger.info(f"Skipping: Current IST time {now_ist.strftime('%H:%M')} is outside 6 AM – 6 PM window.")
        return False
    return True


def _run_with_delay(mode: str):
    """Common helper: add a random delay, then run the updater in the given mode."""
    if not is_within_allowed_window():
        return

    # Random delay between 1 and 15 minutes to avoid detection patterns
    delay_minutes = random.randint(1, 15)
    delay_seconds = delay_minutes * 60
    logger.info(f"[{mode}] Adding random delay of {delay_minutes} minute(s) before running...")
    time.sleep(delay_seconds)

    # Re-check window after the delay (in case we drifted past 8 PM)
    if not is_within_allowed_window():
        return

    try:
        now_ist = datetime.now(IST)
        logger.info("=" * 60)
        logger.info(f"Starting scheduled update [{mode}] at {now_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info("=" * 60)

        from naukri_updater.main import NaukriUpdater

        updater = NaukriUpdater()
        success = updater.run(mode=mode)

        if success:
            logger.info(f"[{mode}] Update completed successfully!")
        else:
            logger.warning(f"[{mode}] Update finished with errors.")

    except Exception as e:
        logger.error(f"[{mode}] Update failed with exception: {e}", exc_info=True)


def run_resume_update():
    """Scheduled job: upload resume (runs once daily in the morning)."""
    logger.info(">>> Triggered DAILY resume upload job")
    _run_with_delay("resume")
    logger.info(f"Next resume upload at: {schedule.next_run()}")


def run_profile_update():
    """Scheduled job: toggle headline (runs every hour)."""
    logger.info(">>> Triggered HOURLY profile update job")
    _run_with_delay("profile")
    logger.info(f"Next profile update at: {schedule.next_run()}")


def main():
    """Main scheduler entry point."""
    now_ist = datetime.now(IST)
    logger.info("=" * 60)
    logger.info("Naukri Profile Updater - Railway Scheduler")
    logger.info(f"  Resume upload : daily at {RESUME_UPLOAD_TIME} IST (+ random 1-15 min delay)")
    logger.info("  Profile update: every 1 hour (+ random 1-15 min delay)")
    logger.info("  Window        : Mon–Sat, 6 AM – 6 PM IST")
    logger.info(f"  Started at    : {now_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info("=" * 60)

    # ── Daily job: resume upload at 7 AM IST ──
    schedule.every().day.at(RESUME_UPLOAD_TIME).do(run_resume_update)

    # ── Hourly job: profile / headline update ──
    schedule.every(1).hours.do(run_profile_update)

    # Run an initial profile update on startup (if within window)
    logger.info("Running initial profile update on startup...")
    run_profile_update()

    # Keep running forever
    logger.info("Scheduler is now running. Waiting for next scheduled job...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every 60 seconds


if __name__ == "__main__":
    main()
