# Tidal Fusion

**Tidal Fusion** is a powerful CLI utility to aggregate, filter, and generate playlists on Tidal. It allows you to merge your "Daily Discovery", "My Mix" playlists, and more into a single "Tidal Fusion" playlist, with advanced modes for intelligent flow generation.

## Features
- **Modes**:
    - **Basic**: Aggregates tracks from your Daily Discovery and Mixes.
    - **Fusion**: A sophisticated algorithm blending **Comfort** (Old Favorites), **Habit** (Recent History), and **Adventure** (New Discoveries) with BPM smoothing.
- **Smart Management**: updates your playlist without deleting it (preserving external IDs).
- **Anti-Repeat**: Logic to prevent track repetition over a configurable period.
- **Data Persistence**: Uses a local SQLite database for history and configuration.
- **Cross-Platform**: Runs on Linux, macOS, and Windows.

## Getting Started

1. **Install**: Follow the [Installation Guide](INSTALL.md).
2. **Authenticate**:
   ```bash
   tidal-fusion -c
   ```
   Select **Run Authentication** from the menu.
3. **Run**:
   ```bash
   tidal-fusion --mode fusion
   ```

## Documentation
- [Installation Guide](INSTALL.md)
- [Usage Guide](USAGE.md)
