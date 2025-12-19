# Tidal Fusion

A Python CLI application that aggregates your personalized Tidal mixes ("My Daily Discovery", "My New Arrivals", "My Mix 1-8") into a single "Tidal Fusion" playlist.

## Features
- **Smart Aggregation**: Scrapes tracks from your daily and weekly generated mixes.
- **Configurable**: Choose which mixes to include via simple CLI menu.
- **Cross-Platform**: Works on Linux, macOS, and Windows.
- **Secure**: Saves authentication tokens locally with appropriate file permissions.

## Installation

1. Clone or download this repository.
2. Create and activate a virtual environment (recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # .venv\Scripts\activate   # Windows
   ```
3. Install dependencies:
   ```bash
   pip install tidalapi
   ```

## Usage

### 1. Authentication
First, log in to your Tidal account:
```bash
python3 tidal_fusion.py --newlogin
```
Follow the on-screen instructions to authorize via your browser.

### 2. Configuration (Optional)
Select which mixes you want to include (defaults to all):
```bash
python3 tidal_fusion.py --config
```

### 3. Generate Tidal Fusion
Create a new playlist (or overwrite "Tidal Fusion"):
```bash
python3 tidal_fusion.py --new
```
Append tracks to the existing playlist:
```bash
python3 tidal_fusion.py --append
```

### Custom Playlist Names
```bash
python3 tidal_fusion.py --new --playlistname "My Weekly Jam"
```

## Automating (Daily Schedule)
To keep your playlist fresh, you can schedule the script to run automatically every day.

### Linux / macOS (via Cron)
1. Open your crontab:
   ```bash
   crontab -e
   ```
2. Add the following line to run at 6:00 AM daily:
   ```bash
   # m h  dom mon dow   command
   0 6 * * * /path/to/virtualenv/bin/python /path/to/tidal_fusion.py --new
   ```
   *(Replace `/path/to/...` with your actual full paths. Run `pwd` in your project folder to find the path).*
   
   **Note for macOS:** Ensure `tidal_tokens.json` path is handled correctly. The script expects the token file in the same directory. You may need to create a simple wrapper shell script that `cd`s into the directory first.
   
   *Example wrapper.sh:*
   ```bash
   #!/bin/bash
   cd /Users/username/dev/Tidal_Fusion
   source .venv/bin/activate
   python3 tidal_fusion.py --new
   ```

### Windows (Task Scheduler)
1. Open **Task Scheduler**.
2. Click **Create Basic Task**.
3. Name it "Tidal Fusion Update".
4. Trigger: **Daily** -> Set time (e.g., 6:00 AM).
5. Action: **Start a program**.
6. Program/script: Propagate path to your Python executable in the venv (e.g., `C:\Users\You\dev\Tidal_Fusion\.venv\Scripts\python.exe`).
7. Add arguments: `tidal_fusion.py --new`.
8. **Start in (Optional)**: Enter the full path to your project folder (Important so it finds `tidal_tokens.json`).
9. Finish.
