# Naukri Profile Automation Tool 🚀

Automatically update your Naukri.com profile resume multiple times per day using GitHub Actions. Keep your profile active and visible to recruiters—even when your laptop is off!

## Features

- ✅ **Automatic Resume Updates**: Re-uploads your resume 3 times daily
- ✅ **Cloud-Based**: Runs on GitHub Actions (100% free)
- ✅ **Zero Maintenance**: Set it and forget it
- ✅ **Error Handling**: Comprehensive logging and debug screenshots
- ✅ **Secure**: Credentials stored as GitHub Secrets

## Schedule

The automation runs at:
| Time (IST) | Time (UTC) |
|------------|------------|
| 9:00 AM    | 3:30 AM    |
| 2:00 PM    | 8:30 AM    |
| 8:00 PM    | 2:30 PM    |

## Quick Setup Guide

### 1. Create a GitHub Repository

1. Go to [GitHub](https://github.com) and create a new repository
2. Name it something like `naukri-updater` (can be private)

### 2. Add Your Secrets

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add:

| Secret Name | Value |
|-------------|-------|
| `NAUKRI_EMAIL` | Your Naukri.com login email |
| `NAUKRI_PASSWORD` | Your Naukri.com password |

⚠️ **Important**: Make sure there are no extra spaces in your credentials!

### 3. Update Your Resume

Replace the file in `resume/resume.pdf` with your latest resume:
- Supported formats: PDF, DOC, DOCX, RTF
- Maximum size: 300 KB

### 4. Push to GitHub

```bash
cd /home/rohit/Desktop/Project/bbk

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Naukri profile automation"

# Add your remote (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/naukri-updater.git

# Push
git push -u origin main
```

### 5. Verify It Works

1. Go to your repository on GitHub
2. Click the **Actions** tab
3. Select **Update Naukri Profile** workflow
4. Click **Run workflow** → **Run workflow** (green button)
5. Watch the job execute and check the logs

## Project Structure

```
bbk/
├── .github/
│   └── workflows/
│       └── naukri_update.yml   # GitHub Actions workflow
├── naukri_updater/
│   ├── __init__.py             # Package init
│   ├── main.py                 # Main automation script
│   └── config.py               # Configuration settings
├── resume/
│   └── resume.pdf              # Your resume file
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Local Testing

You can test the script locally before pushing:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export NAUKRI_EMAIL="your-email@example.com"
export NAUKRI_PASSWORD="your-password"

# Run the script
python -m naukri_updater.main
```

## Troubleshooting

### Login Failed
- Verify your email and password are correct
- Check if Naukri has added CAPTCHA (may need manual intervention)
- Look at the screenshots in the GitHub Actions artifacts

### Resume Upload Failed
- Ensure your resume is under 300 KB
- Ensure it's in a supported format (PDF, DOC, DOCX, RTF)
- Check the debug screenshots

### Workflow Not Running
- Go to Actions tab and ensure workflows are enabled
- Check if your repository is public or if you have Actions enabled for private repos

### Viewing Debug Screenshots
1. Go to GitHub Actions
2. Click on a failed workflow run
3. Scroll down to "Artifacts"
4. Download `debug-screenshots`

## Customization

### Change Schedule
Edit `.github/workflows/naukri_update.yml` and modify the cron expressions:

```yaml
schedule:
  - cron: '30 3 * * *'   # 9:00 AM IST
  - cron: '30 8 * * *'   # 2:00 PM IST
  - cron: '30 14 * * *'  # 8:00 PM IST
```

Use [crontab.guru](https://crontab.guru/) to generate cron expressions.

### Enable Headline Toggle
To also update your resume headline (adds/removes a period for visibility boost), edit `naukri_updater/main.py` and uncomment line ~280:

```python
# Optionally update headline (uncomment if desired)
self.update_headline()  # ← Uncomment this line
```

## ⚠️ Disclaimer

This tool is for educational purposes. Automated profile updates may violate Naukri.com's Terms of Service. Use at your own risk and discretion.

## License

MIT License - Feel free to modify and use as needed.

---

Made with ❤️ to help job seekers stay visible to recruiters!
