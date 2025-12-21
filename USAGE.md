# Usage Guide

**Tidal Fusion** is a CLI tool to generate dynamic playlists on Tidal.

## Basic Usage
Running the command without arguments will perform the default action: **Reset & Fill Playlist using Basic Mode**.
```bash
tidal-fusion
```

## Global Arguments
| Argument | Description |
| :--- | :--- |
| `-h`, `--help` | Show context-aware help. |
| `--login` | Start the Tidal OAuth authentication flow. |
| `-c`, `--config` | Open the configuration menu. |

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

## Modes
Choose **how** tracks are selected.

### Basic Mode (`--mode basic`) [Default]
Selects tracks randomly from your configured sources:
- **My Daily Discovery**
- **My New Arrivals**
- **My Mix 1-8**

Configuration:
```bash
tidal-fusion -c --mode basic
```

### Fusion Mode (`--mode fusion`)
Intelligent algorithm designed to blend tracks for the perfect listening session. Interleaves tracks from three buckets:
1.  **Comfort (40%)**: Favorites (> 6 months old).
2.  **Habit (30%)**: Recent history.
3.  **Adventure (30%)**: Discovery mixes.

**Features**:
- **BPM Smoothing**: Swaps tracks to prevent jarring tempo jumps (>30 BPM).
- **Date Filtering**: Prioritizes older favorites for nostalgia.

**Options**:
- `-m`, `--limit <N>`: Set the total number of tracks (Default: 200).

**Example**:
```bash
tidal-fusion --mode fusion -n --limit 100
```
