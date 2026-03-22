# 📲 WhatsApp Marketing Scheduler

> Automate your WhatsApp group marketing — schedule product banners with custom captions, set send times, and let the bot handle everything while you focus on your business.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?style=flat-square&logo=streamlit)
![Selenium](https://img.shields.io/badge/Selenium-Automation-green?style=flat-square&logo=selenium)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightgrey?style=flat-square&logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## ✨ Features

- 📅 **Schedule campaigns** — set any send time in HH:MM format
- 🖼️ **Multi-post campaigns** — upload multiple images, each with its own custom caption
- 💬 **Emoji-safe captions** — full emoji support in captions (🔥 💯 ✅)
- 👥 **Multi-group targeting** — send to multiple WhatsApp groups at once
- 🔁 **Flexible repeat** — once, daily, or weekly on specific days
- 🚦 **Daily send limit** — configurable max sends per group per day (resets at midnight)
- 📊 **Streamlit dashboard** — manage everything from a clean web UI
- 📜 **Send logs** — full history of every send attempt with success/fail status
- 💾 **Session saved** — scan QR code only once, session persists

---

## 🖥️ Dashboard Preview

| Page | Description |
|------|-------------|
| 🏠 Dashboard | Stats overview + active campaigns + recent activity |
| 👥 Groups | Add and manage your WhatsApp groups |
| 📢 Campaigns | View, pause, resume, delete campaigns |
| ➕ New Campaign | Create campaign with multi-image posts |
| 📜 Logs | Full send history with success rate |
| 🤖 Bot Control | Manual test sends + live scheduler log |

---

## 🏗️ Architecture

```
┌─────────────────────────┐       ┌──────────────────────────┐
│   Streamlit Dashboard   │       │   scheduler_worker.py    │
│   streamlit run app.py  │       │   python scheduler_...   │
│                         │       │                          │
│  Add groups & campaigns │       │  Checks DB every 30s     │
│  Upload banners         │◄─────►│  Fires at scheduled time │
│  View logs & stats      │       │  Selenium sends image    │
│  Manual test sends      │       │  Logs result to DB       │
└────────────┬────────────┘       └──────────────────────────┘
             │
        campaigns.db (SQLite)
```

---

## 📁 Project Structure

```
wa_system/
├── app.py                  # Streamlit dashboard (UI)
├── whatsapp_bot.py         # Selenium WhatsApp Web automation
├── scheduler_worker.py     # Background scheduler process
├── database.py             # SQLite database models & queries
├── requirements.txt        # Python dependencies
├── banners/                # ← Put your banner images here
├── wa_session/             # Auto-created: saves WhatsApp login session
├── campaigns.db            # Auto-created: SQLite database
└── scheduler.log           # Auto-created: scheduler activity log
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.10+
- Google Chrome browser installed
- WhatsApp account

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/whatsapp-marketing-scheduler.git
cd whatsapp-marketing-scheduler

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create banners folder and add your images
mkdir banners
# Copy your JPG/PNG banner images into ./banners/
```

---

## 🚀 Running the System

You need **two terminals** open at the same time, both inside the project folder.

**Terminal 1 — Launch the Dashboard**
```bash
streamlit run app.py
```
Opens at: **http://localhost:8501**

**Terminal 2 — Start the Scheduler Bot**
```bash
python scheduler_worker.py
```
Chrome will open → **scan the QR code** with your phone once → session is saved permanently.

---

## 📖 Usage Guide

### Step 1 — Add Your Groups
Go to **👥 Groups** in the dashboard and add your WhatsApp group names exactly as they appear in WhatsApp (including any emojis in the name).

### Step 2 — Create a Campaign
Go to **➕ New Campaign** and fill in:
- **Title** — name for this campaign
- **Send Time** — type any time e.g. `09:00`, `14:30`, `20:15`
- **Repeat** — `once`, `daily`, or `weekly`
- **Days** — leave empty for every day, or pick specific days
- **Target Groups** — select which groups to send to

### Step 3 — Add Posts
After creating the campaign, add your image+caption pairs:
- Upload a banner image (JPG/PNG/WebP)
- Write the custom caption for that specific image
- Add as many posts as needed

### Step 4 — Watch It Run
The scheduler fires automatically at your set time. Monitor it in **📜 Logs** or watch Terminal 2.

> **Quick test:** Go to **🤖 Bot Control** → **Send Now** to fire a campaign immediately without waiting.

---

## ⚙️ Configuration

To change the daily send limit per group, open `scheduler_worker.py` and edit line 9:

```python
DAILY_SEND_LIMIT = 2   # change to any number
```

The limit resets automatically at midnight every day.

---

## ⚠️ Important Notes

| Topic | Detail |
|-------|--------|
| **WhatsApp ToS** | This uses unofficial automation. Use responsibly. |
| **Account safety** | Add delays between sends — built-in 5s gap between groups |
| **Group membership** | You must be a member (ideally admin) of target groups |
| **QR Login** | Required once — session saved in `wa_session/` folder |
| **Chrome window** | Keep it open while the scheduler is running |
| **Time format** | Use 24-hour format — `09:00`, `17:30`, `20:15` |

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| [Streamlit](https://streamlit.io) | Web dashboard UI |
| [Selenium](https://selenium.dev) | WhatsApp Web browser automation |
| [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager) | Auto ChromeDriver version matching |
| [pyperclip](https://github.com/asweigart/pyperclip) | Clipboard paste for emoji support |
| SQLite | Local database (no setup needed) |
| Python 3.10+ | Core language |

---

## 📄 License

MIT License — free to use, modify and distribute.

---

> Built with Python, Streamlit & Selenium. Designed for small business owners who want to automate their WhatsApp marketing without expensive third-party tools.
