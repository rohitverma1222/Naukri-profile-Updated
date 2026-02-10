"""
Scheduler for Naukri Profile Updater - Railway Deployment

Runs the Naukri profile updater every 30 minutes as a long-lived process.
This is the entry point for Railway deployment.
"""

import logging
import sys
import time
from datetime import datetime

import schedule

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_updater():
    """Run the Naukri profile updater."""
    try:
        logger.info("=" * 60)
        logger.info(f"Starting scheduled update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
    logger.info("=" * 60)
    logger.info("Naukri Profile Updater - Railway Scheduler")
    logger.info("Schedule: Every 30 minutes")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # Schedule the job every 30 minutes
    schedule.every(30).minutes.do(run_updater)

    # Run immediately on startup
    logger.info("Running initial update on startup...")
    run_updater()

    # Keep running forever
    logger.info("Scheduler is now running. Waiting for next scheduled job...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every 60 seconds


if __name__ == "__main__":
    main()
