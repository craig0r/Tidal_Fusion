# Usage Guide

**Tidal Fusion** is a CLI tool to generate dynamic playlists on Tidal.

## Basic Usage
Running the command without arguments will perform the default action: **Reset & Fill Playlist using Basic Mode** (or your configured default mode).
```bash
tidal-fusion
```

## Global Arguments
| Argument | Description |
| :--- | :--- |
| `-h`, `--help` | Show context-aware help. |
| `-c`, `--config` | Open the interactive configuration menu. |
| `-d`, `--debug` | Enable debug logging to console and file. |

## Authentication
Tidal Fusion requires a valid Tidal session. To authenticate:
1. Run `tidal-fusion -c` to open the configuration menu.
2. Select **Run Authentication** (Option 3).
3. Follow the link to log in via your browser.
4. Tokens are securely stored in the local SQLite database.

## Configuration
The configuration menu (`-c`) is now a unified hub for all settings:

1.  **Mode-Specific Configurations**:
    *   **Basic Mode**: Toggle sources (Daily Discovery, New Arrivals, My Mixes).
    *   **Fusion Mode**: Configure `exclude_days` and `max_repeats`.
2.  **Global Settings**:
    *   **Default Mode**: Set the mode to run when no `--mode` argument is provided.
    *   **Max Retries**: Set the number of API retry attempts (Default: 3).

## Actions (Mutually Exclusive)
Choose **one** of the following to determine *what* the tool does with the playlist.

### New Playlist (`-n`, `--new`) [Default]
Resets the target playlist ("Tidal Fusion") by emptying it and filling it with newly generated tracks.
```bash
tidal-fusion -n
```

### Append (`-a`, `--append`)
Adds the generated tracks to the end of the existing playlist instead of overwriting it.
```bash
tidal-fusion -a
```

### History Management
Manage your local playback history to fine-tune anti-repeat logic.
*   `--show-history [N]`: View the last N generated tracks (Default: 20).
*   `--clear-history`: Wipe the database history.

## Modes
Choose **how** tracks are selected.

### Basic Mode (`--mode basic`)
Selects tracks randomly from your configured sources.
Configuration: `tidal-fusion -c` -> Mode-Specific -> Basic.

### Fusion Mode (`--mode fusion`)
Intelligent algorithm blending tracks for a balanced listening session.
*   **Composition**: 40% Comfort (Old Favorites), 30% Habit (Recent History), 30% Adventure (Discovery).
*   **Vibe Check**: Smooths transitions by BPM preventing jumps >30.
*   **Anti-Repeat**: Excludes tracks played too frequently.

**Fusion Options**:
| Option | Description | Default |
| :--- | :--- | :--- |
| `-m`, `--limit <N>` | Total number of tracks to generate. | 150 |
| `--exclude-days <N>` | Look back N days for repeat checking. | 7 |
| `--max-repeats <N>` | Max allowed plays in the look-back window. | 3 |

**Example**:
Generate 100 tracks, avoiding any track played twice in the last 3 days:
```bash
tidal-fusion --mode fusion --limit 100 --exclude-days 3 --max-repeats 2
```
