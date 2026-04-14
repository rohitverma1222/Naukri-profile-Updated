import logging
import random
import sys
import time
import threading
from datetime import datetime

import pytz
import schedule
from flask import Flask, jsonify

IST = pytz.timezone("Asia/Kolkata")

# Allowed days: Monday(0) to Saturday(5)
ALLOWED_DAYS = {0, 1, 2, 3, 4, 5, 6}
START_HOUR = 6   # 6 AM IST
END_HOUR = 22    # 10 PM IST

# Morning hour for the daily resume upload
RESUME_UPLOAD_TIME = "07:00"  # 7 AM IST

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Flask App for Health Checks
app = Flask(__name__)

@app.route("/")
@app.route("/health")
def health_check():
    """Health check endpoint for Render."""
    return jsonify({"status": "ok", "time_ist": datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')}), 200


def run_manual_update(mode: str):
    """Helper to run the updater immediately in a separate thread."""
    try:
        logger.info(f"[MANUAL] Starting {mode} update via API...")
        from naukri_updater.main import NaukriUpdater
        updater = NaukriUpdater()
        updater.run(mode=mode)
        logger.info(f"[MANUAL] {mode} update triggered via API completed.")
    except Exception as e:
        logger.error(f"[MANUAL] {mode} update failed: {e}")


@app.route("/update-resume")
def update_resume_manual():
    """Endpoint to manually trigger resume update."""
    threading.Thread(target=run_manual_update, args=("resume",), daemon=True).start()
    return jsonify({
        "status": "triggered",
        "mode": "resume",
        "message": "Resume update started in background"
    }), 202


@app.route("/update-profile")
def update_profile_manual():
    """Endpoint to manually trigger profile update."""
    threading.Thread(target=run_manual_update, args=("profile",), daemon=True).start()
    return jsonify({
        "status": "triggered",
        "mode": "profile",
        "message": "Profile update started in background"
    }), 202


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

    # Re-check window after the delay
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


def run_scheduler():
    """Main scheduler loop to be run in a background thread."""
    now_ist = datetime.now(IST)
    logger.info("=" * 60)
    logger.info("Naukri Profile Updater - Scheduler Thread")
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
        time.sleep(60)


if __name__ == "__main__":
    # Start the scheduler in a background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Start the Flask web server (blocks the main thread)
    # Render provides the PORT environment variable
    import os
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting Flask web server on port {port}...")
    app.run(host="0.0.0.0", port=port)
