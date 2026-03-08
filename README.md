# 🎬 YouTube Downloader

A personal YouTube video downloader built with **Streamlit** and **yt-dlp**, self-hosted on a home PC and accessible from any device via **Ngrok**.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red?logo=streamlit)
![yt-dlp](https://img.shields.io/badge/yt--dlp-2026-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

- 🎥 Download YouTube videos in **144p → 4K** quality
- 🎵 Extract **audio-only** (MP3)
- 📋 **Playlist** support
- 🎨 **3 themes** — Dark, Light, Grey
- 📜 **Download history** (SQLite)
- 💾 **Browser save button** — works from phone/tablet
- 📧 **Email notification** with new URL on every reboot
- 🔄 **Auto-starts on boot** via systemd

---

## 🏗️ Architecture

```
Your PC (home)
│
├── Streamlit app  (port 8501)
│     └── yt-dlp + FFmpeg + Node.js
│
└── Ngrok tunnel ──► https://xxxx.ngrok-free.dev
                          │
                    Any device (tablet, phone, office)
```

> **Why not Streamlit Cloud?**  
> YouTube blocks requests from cloud server IPs (AWS/GCP) with 403 errors.  
> Self-hosting on a home PC bypasses this completely.

---

## 🚀 Local Setup

### 1. Clone the repo
```bash
git clone https://github.com/nyandajr/youtube-downloader-app.git
cd youtube-downloader-app
```

### 2. Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Install system dependencies
```bash
# FFmpeg (for merging video + audio)
sudo apt install ffmpeg

# Node.js (required by yt-dlp for full format list)
sudo apt install nodejs
```

### 4. Install & configure Ngrok
```bash
# Download from https://ngrok.com/download
sudo mv ngrok /usr/local/bin/
ngrok config add-authtoken YOUR_AUTHTOKEN
```

### 5. Run manually
```bash
bash start_app.sh
```

---

## 🔄 Auto-Start on Boot (systemd)

The app starts automatically when your PC boots:

```bash
sudo cp youtube-downloader.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable youtube-downloader.service
sudo systemctl start youtube-downloader.service
```

After each reboot:
- ✅ Streamlit starts on port 8501
- ✅ Ngrok creates a public tunnel
- 📧 You receive an email with the new URL
- 🔔 Desktop notification pops up
- 📄 URL saved to `current_url.txt`

---

## 📧 Email Notifications

Edit `notify_url.py` with your Gmail credentials:

```python
SMTP_USER     = "you@gmail.com"
SMTP_PASSWORD = "your-app-password"   # https://myaccount.google.com/apppasswords
TO_EMAIL      = "you@protonmail.com"
```

> Requires **2-Step Verification** enabled on your Gmail account and an **App Password** (not your regular password).

---

## 📁 Project Structure

```
youtube-downloader-app/
├── src/
│   └── app.py                      # Main Streamlit app
├── requirements.txt                # Python dependencies
├── README.md
│
# In parent folder:
├── start_app.sh                    # Startup script (Streamlit + Ngrok + email)
├── notify_url.py                   # Email notification script
├── youtube-downloader.service      # systemd service file
├── current_url.txt                 # Latest Ngrok URL (auto-updated)
└── logs/
    ├── streamlit.log
    └── ngrok.log
```

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| [Streamlit](https://streamlit.io) | Web UI framework |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | YouTube download engine |
| [FFmpeg](https://ffmpeg.org) | Video/audio merging |
| [Node.js](https://nodejs.org) | JS runtime for yt-dlp format extraction |
| [Ngrok](https://ngrok.com) | Public HTTPS tunnel to home PC |
| SQLite | Download history database |

---

## ⚠️ Disclaimer

This tool is for **personal use only**. Only download videos you have the right to download. Respect YouTube's [Terms of Service](https://www.youtube.com/t/terms) and content creators' rights.

---

## 👤 Author

**Freddy Nyanda**  
GitHub: [@nyandajr](https://github.com/nyandajr)

## Project Structure

```
youtube-downloader-app
├── src
│   ├── app.py          # Main entry point of the Streamlit application
│   ├── downloader.py   # Logic for downloading YouTube videos
│   └── utils.py        # Utility functions for the application
├── requirements.txt     # List of dependencies
└── README.md            # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd youtube-downloader-app
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit application:
   ```
   streamlit run src/app.py
   ```

2. Open your web browser and navigate to `http://localhost:8501`.

3. Enter the YouTube video link in the provided input field.

4. Select the desired format from the available options.

5. Click the download button to start downloading the video.

## Dependencies

- Streamlit
- Pytube
- TQDM

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.