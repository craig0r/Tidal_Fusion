# 🌊 Tidal Fusion

**Tidal Fusion** is a powerful CLI utility to aggregate, filter, and generate dynamic playlists on Tidal. It seamlessly blends your "Daily Discovery", "New Arrivals", and "My Mix" playlists into a single, cohesive listening experience using advanced algorithms.

## ✨ Features

- **🚀 Two Powerful Modes**:
    - **Basic**: Aggregates tracks from your Daily Discovery and Mixes.
    - **Fusion**: A sophisticated algorithm blending **Comfort** (Old Favorites), **Habit** (Recent History), and **Adventure** (New Discoveries).
- **⏱️ Smart Duration Control**: Generate playlists by **Time** (e.g., "3 hours of music") or **Track Count**.
- **🔄 Anti-Repeat**: Intelligent filtering prevents track repetition over configurable windows (e.g., "Don't play songs heard in the last 7 days").
- **🌊 Vibe Check**: Smooths transitions by ensuring BPM jumps don't kill the mood.
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
Select **3. Run Authentication** and follow the browser prompts.

### 2. Run Fusion Mode
Generate your first Fusion playlist (Defaults: ~3 Hours of music):
```bash
tidal-fusion --mode fusion
```

---

## 📖 Usage Guide

Running the command without arguments performs the **Default Action** (configurable, usually Reset Playlist in Basic Mode).

```bash
tidal-fusion
```

### 🎛️ Modes

#### Fusion Mode (`--mode fusion`)
The flagship experience. It builds a playlist using a 40/30/30 split of Comfort/Habit/Adventure tracks, applies Anti-Repeat logic, and smooths BPM.

**Options**:
- `--limit <N>`: Override default limit.
  - If Config is **Time-based**: `N` = Minutes (e.g., 60 for 1 hour).
  - If Config is **Count-based**: `N` = Number of tracks (e.g., 100).
- `--exclude-days <N>`: Don't play tracks heard in the last N days.
- `--max-repeats <N>`: Allow a track to be played N times within the window before excluding.

**Example**:
```bash
# Generate a 2-hour mix, excluding songs played in the last 3 days
tidal-fusion --mode fusion --limit 120 --exclude-days 3
```

#### Basic Mode (`--mode basic`)
Simply aggregates tracks from your configured sources (Daily Discovery, Mixes) and shuffles them.

### 🎮 Actions
By default, Tidal Fusion **Resets** (overwrites) the target playlist. You can change this behavior:

- `-n`, `--new`: **Overwrite** playlist (Default).
- `-a`, `--append`: **Add** tracks to the end of the existing playlist.

### 🛠️ Configuration (`-c`)
Run `tidal-fusion -c` to access the interactive menu:

1. **Mode Settings**:
   - **Basic**: Toggle sources (Daily Discovery, New Arrivals, etc.).
   - **Fusion**: Set **Duration Type** (Time vs Count), **Limit Value** (default 180 mins), and default **Anti-Repeat** settings.
2. **Global Settings**: Change default run mode and API retries.

### 📜 History & Logging
- **Logs**:
  - **Linux/macOS**: `/var/log/tidal_fusion/`
  - **Windows**: `%ProgramData%\TidalFusion\`
  - Use `-d` / `--debug` to write verbose logs to these locations.
- **Playback History**:
  - View last 20 generated tracks: `tidal-fusion --show-history`
  - Clear history: `tidal-fusion --clear-history`

---

## 🙋 FAQ

**Q: Where is my data stored?**
A: `fusion.db` (tokens, history, config) is stored in your user configuration directory (`~/.config/tidal_fusion` or `%AppData%\TidalFusion`). Using the configuration menu, you can back up or clear this data.

**Q: I get a "Permission Denied" error on logs?**
A: The install scripts attempt to create the log directory with appropriate group permissions (`users`). If this fails, the app falls back to logging in your user config directory.
