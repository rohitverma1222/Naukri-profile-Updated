# Naukri Profile Automation Tool 🚀

Automatically keep your Naukri.com profile active and visible to recruiters — runs on Railway (or locally) with zero manual effort.

## Features

- ✅ **Daily Resume Upload**: Re-uploads your resume once every morning (7 AM IST)
- ✅ **Hourly Profile Refresh**: Toggles resume headline every hour to bump your profile timestamp
- ✅ **Cookie-Based Auth**: Uses browser cookies to bypass OTP (no CAPTCHA headaches)
- ✅ **Auto OTP via Email**: Falls back to email-based OTP reading if cookies expire
- ✅ **Anti-Detection**: Random delays (1–15 min), realistic user-agent, stealth mode
- ✅ **Smart Scheduling**: Mon–Sat only, 6 AM – 6 PM IST window
- ✅ **Error Handling**: Comprehensive logging and debug screenshots
- ✅ **Cloud-Ready**: Deploys to Railway with one click

## Schedule

| Job              | Frequency           | Window                     |
|------------------|---------------------|----------------------------|
| Resume Upload    | Once daily at 7 AM  | Mon–Sat, 6 AM – 6 PM IST  |
| Profile Update   | Every 1 hour        | Mon–Sat, 6 AM – 6 PM IST  |

Both jobs include a random **1–15 minute delay** to avoid detection patterns.

## Project Structure

```
bbk/
├── scheduler.py                # Entry point — schedules daily & hourly jobs
├── naukri_updater/
│   ├── __init__.py
│   ├── main.py                 # NaukriUpdater class (login, resume, headline)
│   ├── config.py               # URLs, selectors, env-var config
│   └── email_otp.py            # Email-based OTP reader
├── resume/
│   └── Rohit_Resume_2025.pdf   # Your resume file
├── export_cookies.py           # Helper to export browser cookies
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Railway deployment
├── railway.json                # Railway config
└── .env.example                # Environment variable template
```

## Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` and fill in your values:

```bash
cp .env.example .env
```

| Variable             | Required | Description                              |
|----------------------|----------|------------------------------------------|
| `NAUKRI_COOKIES`     | ✅       | JSON array of browser cookies (preferred)|
| `NAUKRI_EMAIL`       | Fallback | Naukri login email                       |
| `NAUKRI_PASSWORD`    | Fallback | Naukri login password                    |
| `EMAIL_ADDRESS`      | Optional | Gmail for OTP reading                    |
| `EMAIL_APP_PASSWORD` | Optional | Gmail app password for OTP               |

### 3. Export Cookies (Recommended)

```bash
python export_cookies.py
```

This exports your Naukri session cookies to bypass login/OTP entirely.

### 4. Run Locally

```bash
python scheduler.py
```

### 5. Deploy to Railway

Push to GitHub and connect your repo to [Railway](https://railway.app). Set the environment variables in Railway dashboard.

## How It Works

1. **Scheduler** (`scheduler.py`) runs two independent jobs:
   - **Daily 7 AM**: Uploads resume → triggers "profile updated" on Naukri
   - **Every hour**: Toggles a period (`.`) at the end of your resume headline → bumps profile timestamp

2. **Authentication** tries cookie-based login first, then falls back to email/password + OTP.

3. Both jobs skip Sundays and hours outside 6 AM – 6 PM IST.

## Customization

Edit `scheduler.py` to change:

```python
RESUME_UPLOAD_TIME = "07:00"  # Change daily upload time
START_HOUR = 6                # Window start
END_HOUR = 18                 # Window end
ALLOWED_DAYS = {0, 1, 2, 3, 4, 5}  # 0=Mon, 6=Sun
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Login fails | Re-export cookies with `export_cookies.py` |
| OTP needed | Set `EMAIL_ADDRESS` and `EMAIL_APP_PASSWORD` |
| Resume upload fails | Ensure resume < 300 KB, format: PDF/DOC/DOCX |
| Headline update fails | Check debug screenshots in `screenshots/` |

## ⚠️ Disclaimer

This tool is for educational purposes. Automated profile updates may violate Naukri.com's Terms of Service. Use at your own risk.

## License

MIT License

---

Made with ❤️ to help job seekers stay visible to recruiters!
