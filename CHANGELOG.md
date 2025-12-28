# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2025-12-27

### Added
- **Anti-Repeat System**:
    - **History Tracking**: Logs all generated tracks to a local SQLite database.
    - **Configurable Exclusion**: New arguments `--exclude-days` (lookback window) and `--max-repeats` (play threshold).
    - **Visualization**: `tidal-fusion --show-history` to view playback logs.
- **SQLite Database**:
    - Replaced JSON file storage with `fusion.db` for robust data management (Tokens, Config, History).
    - Automatic migration of existing JSON configuration files.
- **API Resilience**:
    - Added exponential backoff retry mechanism for Playlist API calls (`max_retries` configurable).
- **Configuration Menu Refactor**:
    - Unified `-c` menu with hierarchical structure (Mode-Specific vs Global settings).

### Changed
- **Defaults**: Playlist limit updated to 150 tracks.
- **CLI**: Removed `--login` (use `-c` menu instead).
- **Architecture**: `tidal_fusion.py` now relies on `auth_manager` for all DB interactions.

## [1.1.0] - 2025-12-20

### Added
- **Fusion Mode** (`--mode fusion`):
    - Implemented a new intelligent generation algorithm.
    - **Buckets**:
        - *Comfort*: Favorites older than 6 months (Nostalgia).
        - *Habit*: Recently played tracks (History).
        - *Adventure*: Tracks from "Daily Discovery" and "My Mixes".
    - **Logic**:
        - Balanced interleaving of buckets (Comfort -> Habit -> Adventure).
        - **Vibe Check**: BPM smoothing to prevent jarring tempo jumps (>30 BPM).
    - **Reporting**: Detailed console output showing composition percentages and average BPM.
- **CLI Overhaul**:
    - Introduced mutually exclusive actions: `-n` (New/Reset), `-a` (Append), `-c` (Config).
    - Added `--mode` argument to switch between `basic` and `fusion` generation.
    - Decoupled `-h/--help` for context-aware help messages.
- **Configuration Management**:
    - Centralized configuration and authentication storage.
        - Linux/macOS: `~/.config/tidal_fusion/`
        - Windows: `%APPDATA%\TidalFusion\`
    - Interactive configuration menus for Global and Mode-specific settings.
- **Installation Support**:
    - Added `install.sh` for Linux/macOS (non-root install with PyInstaller).
    - Added `install.bat` for Windows.
    - Full documentation suite: `INSTALL.md`, `USAGE.md`, `CONTRIBUTING.md`.

### Changed
- **Authentication**: Extracted logic to `auth_manager.py` for better modularity.
- **Playlist Management**:
    - Changed default behavior to **empty and refill** user-owned playlists instead of deleting/recreating them.
    - Improved robustness by explicitly searching for mutable `UserPlaylist` objects.
    - Added graceful fallback to create duplicate playlists if modification is forbidden (read-only).
- **Date Handling**: Fixed timezone-aware comparisons for track filtering.

### Fixed
- Resolved `AttributeError` issues when attempting to modify read-only playlists found in Favorites.
- Fixed installer caching issues where old code was prioritized during rebuilds.
- Fixed `TypeError` related to offset-naive vs offset-aware datetime comparisons.
