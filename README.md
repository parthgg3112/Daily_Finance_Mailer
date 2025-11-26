# Vibecoded AI Finance Tutor 🇮🇳 💰

> A fully automated, "Zero Cost" pipeline that emails you a sequential, beginner-friendly finance lesson every morning at 7:00 AM IST.



## 🚀 What is this?

This is a **serverless automation pipeline** that acts as your personal finance mentor. Instead of random facts, it follows a structured "Zero to Hero" curriculum specifically tailored for the **Indian context** (using ₹, Nifty, Indian Tax Laws, etc.).

It runs entirely on the cloud using **GitHub Actions**, costs **$0** to run, and lands in your inbox before you wake up.

## 🧠 How it Works

1.  **Trigger:** GitHub Actions wakes up daily at **7:00 AM IST** (1:30 AM UTC).
2.  **Context Check:** The script reads `history.json` to see what you learned yesterday.
3.  **Curriculum Logic:** It determines the *next* logical topic (e.g., if you learned "Savings Accounts" yesterday, today covers "Fixed Deposits").
4.  **Generation:** Google Gemini (AI) generates a beginner-friendly article + chart data.
5.  **Visualization:** QuickChart.io renders the chart into an image.
6.  **Delivery:** Gmail SMTP sends the formatted HTML email to you (and your friends via BCC).
7.  **Memory:** The script commits the new topic back to `history.json` so it never repeats itself.

## 🛠️ Tech Stack

* **Logic:** Python 3.11
* **AI Model:** Google Gemini 1.5 Flash (Free Tier)
* **Automation:** GitHub Actions (Cron Job)
* **Visuals:** QuickChart.io API
* **Email:** Gmail SMTP

## ⚡ Setup Guide (5 Minutes)

### 1. Fork this Repository
Click the **Fork** button at the top right of this page to copy this code to your own GitHub account.

### 2. Get Your Credentials
* **Gemini API Key:** Get a free key from [Google AI Studio](https://aistudio.google.com/).
* **Gmail App Password:**
    1.  Go to your Google Account > Security.
    2.  Enable **2-Factor Authentication**.
    3.  Search for "App Passwords" and create one. Copy the 16-character code. (Do NOT use your regular email password).

### 3. Add Secrets to GitHub
Go to your repository **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**. Add these four:

| Secret Name | Value |
| :--- | :--- |
| `GEMINI_API_KEY` | Your Google API Key |
| `EMAIL_SENDER` | Your Gmail address (e.g., `me@gmail.com`) |
| `EMAIL_PASSWORD` | The 16-character App Password |
| `EMAIL_RECIPIENT` | Comma-separated list of emails (e.g., `me@gmail.com,friend@yahoo.com`) |

### 4. Enable Permissions (Crucial!)
To allow the bot to save your progress (`history.json`):
1.  Go to **Settings** -> **Actions** -> **General**.
2.  Scroll to **Workflow permissions**.
3.  Select **Read and write permissions**.
4.  Click **Save**.

### 5. Run it!
Go to the **Actions** tab, select **Daily Finance Email**, and click **Run workflow**.

## 📚 Curriculum Logic
The AI is instructed to follow this loose path to ensure sequential learning:
1.  **Foundations** (Inflation, Compounding, Assets vs Liabilities)
2.  **Banking** (Savings, FD, RD, UPI Safety)
3.  **Schemes** (PPF, EPF, Sukanya Samriddhi)
4.  **Insurance** (Term vs Endowment, Health)
5.  **Taxes** (Old vs New Regime, 80C, TDS)
6.  **Mutual Funds** (SIP, NAV, Equity vs Debt)
7.  **Stocks** (Nifty, Sensex, Demat, IPOs)
