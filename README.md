# 🌊 Tidal Fusion

**Tidal Fusion** is a powerful CLI utility to aggregate, filter, and generate dynamic playlists on Tidal. It seamlessly blends your "Daily Discovery", "New Arrivals", and "My Mix" playlists into a single, cohesive listening experience using advanced algorithms.

## ✨ Features

- **🚀 Smart Fusion Engine**: A sophisticated algorithm blending **Comfort** (Old Favorites), **Habit** (Recent History), and **Adventure** (New Discoveries) into one perfect mix.
- **⏱️ Smart Duration Control**: Generate playlists by **Time** (e.g., "3 hours of music") or **Track Count**.
- **🔄 Anti-Repeat**: Intelligent filtering prevents track repetition over configurable windows (e.g., "Don't play songs heard in the last 7 days").
- **💾 Data Persistence**: Uses a local SQLite database for history, tokens, and configuration.
- **🖥️ Cross-Platform**: Runs on Linux, macOS, and Windows.

---

## 📦 Installation

### Option A: Download Latest Release (Recommended)
1. Go to the [Releases Page](https://github.com/craig0r/Tidal_Fusion/releases).
2. Download the installer for your OS:
   - **Linux/macOS**: `install.sh`
   - **Windows**: `install.bat`
3. Run the script to download and install the latest binary.

### Option B: Build from Source
If you are a developer or the scripts fail:
1. Clone the repo:
   ```bash
   git clone https://github.com/craig0r/Tidal_Fusion.git
   cd Tidal_Fusion
   ```
2. Run the build script (creates a venv and builds locally):
   - **Linux/macOS**: `./build_install.sh`
   - **Windows**: `build_install.bat`

---

## 🚀 Getting Started

### 1. Authenticate
Before your first run, you must log in to Tidal.
```bash
tidal-fusion -c
```
Select **2. Run Authentication** and follow the browser prompts.

### 2. Generate Playlist
Generate your Fusion playlist (Defaults: ~3 Hours of music):
```bash
tidal-fusion
```

---

## 📖 Usage Guide

```bash
tidal-fusion [options]
```

### 🎛️ How It Works
The Fusion engine pulls tracks from three sources:
- **Comfort**: Your personal "Favorites" collection.
- **Adventure**: "Daily Discovery" and "New Arrivals" mixes.
- **Habit**: Your various "My Mix" history.

It prioritizes fresh tracks, filters out songs you've heard too recently (based on your config), and ensures a good variety.

### 🎮 Actions
By default, Tidal Fusion **Resets** (overwrites) the target playlist ("Tidal Fusion"). You can change this behavior:

- `-n`, `--new`: **Overwrite** playlist (Default).
- `-a`, `--append`: **Add** tracks to the end of the existing playlist.

### 🎛️ Options
- `-c`, `--config`: Open the configuration menu.
- `--limit <N>`: Override default limit.
  - If Config is **Time-based**: `N` = Minutes (e.g., 60 for 1 hour).
  - If Config is **Count-based**: `N` = Number of tracks (e.g., 100).
- `--exclude-days <N>`: Don't play tracks heard in the last N days.

**Example**:
```bash
# Generate a 2-hour mix, excluding songs played in the last 3 days
tidal-fusion --limit 120 --exclude-days 3
```

### 🛠️ Configuration (`-c`)
Run `tidal-fusion -c` to access the interactive menu:

1. **Advanced Settings**:
   - Set **Duration Type** (Time vs Count).
   - Set **Limit Value** (default 180 mins).
   - Set **Anti-Repeat** window (days) and Max Repeats.
   - Set **API Retries**.
2. **Authentication**: Manage your Tidal login.

### 📜 History & Logging
- **Logs**:
   - Automatically saved to your log directory.
   - **Linux/macOS**: `~/.config/tidal_fusion/` or `/var/log/tidal_fusion/`
   - **Windows**: `%ProgramData%\TidalFusion\` or `%AppData%\TidalFusion\`
   - Logs include full output and track source information.
- **Playback History**:
  - View last 20 generated tracks: `tidal-fusion --show-history`
  - Clear history: `tidal-fusion --clear-history`

---

## 🙋 FAQ

**Q: Where is my data stored?**
A: `fusion.db` (tokens, history, config) is stored in your user configuration directory (`~/.config/tidal_fusion` or `%AppData%\TidalFusion`). Using the configuration menu, you can back up or clear this data.
