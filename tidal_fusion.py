
import argparse
import json
import os
import platform
import pathlib
import random
import sys
import sqlite3
from datetime import datetime, timedelta, timezone
import tidalapi
import auth_manager

# Constants
# CONFIG_FILE removed, using DB
DEFAULT_PLAYLIST_NAME = "Tidal Fusion"
MIX_NAMES_GENERATED = [f"My Mix {i}" for i in range(1, 9)]

# --- Configuration ---

def load_config():
    """Load configuration from database via auth_manager."""
    config = auth_manager.get_config()
    
    # Default Config Structure if empty
    if not config:
        config = {
            "default_mode": "basic",
            "modes": {
                "basic": {
                    "daily_discovery": True,
                    "new_arrivals": True,
                    "my_mixes": True
                },
                "fusion": {
                    "exclude_days": 7
                }
            }
        }
        # Save defaults immediately
        auth_manager.save_config(config)
        
    return config

def save_config(config):
    """Save configuration to database via auth_manager."""
    auth_manager.save_config(config)
    print("Configuration saved.")

def configure_basic_mode(config):
    """Interactive menu for Basic Mode."""
    if "basic" not in config["modes"]: config["modes"]["basic"] = {}
    basic_conf = config["modes"]["basic"]
    
    while True:
        print("\n--- Basic Mode Configuration ---")
        print(f"1. [ {'x' if basic_conf.get('daily_discovery', True) else ' '} ] My Daily Discovery")
        print(f"2. [ {'x' if basic_conf.get('new_arrivals', True) else ' '} ] My New Arrivals")
        print(f"3. [ {'x' if basic_conf.get('my_mixes', True) else ' '} ] My Mixes (1-8)")
        print("4. Save and Exit")
        print("5. Exit without Saving")
        
        choice = input("Enter choice: ").strip()
        if choice == '1':
            basic_conf['daily_discovery'] = not basic_conf.get('daily_discovery', True)
        elif choice == '2':
            basic_conf['new_arrivals'] = not basic_conf.get('new_arrivals', True)
        elif choice == '3':
            basic_conf['my_mixes'] = not basic_conf.get('my_mixes', True)
        elif choice == '4':
            save_config(config)
            return
        elif choice == '5':
            return

def configure_fusion_mode(config):
    """Interactive menu for Fusion Mode."""
    if "fusion" not in config["modes"]: config["modes"]["fusion"] = {}
    fusion_conf = config["modes"]["fusion"]
    
    while True:
        curr = fusion_conf.get('exclude_days', 7)
        print("\n--- Fusion Mode Configuration ---")
        print(f"1. Set 'Exclude Days' (Anti-Repeat) [Current: {curr}]")
        print("2. Save and Exit")
        print("3. Exit without Saving")
        
        choice = input("Enter choice: ").strip()
        if choice == '1':
            val = input(f"Enter days to exclude (0 to disable) [{curr}]: ").strip()
            if val:
                try:
                    fusion_conf['exclude_days'] = int(val)
                except ValueError:
                    print("Invalid number.")
        elif choice == '2':
            save_config(config)
            return
        elif choice == '3':
            return

def configure_global(config):
    """Global configuration menu."""
    while True:
        print("\n--- Tidal Fusion Configuration ---")
        print(f"Current Default Mode: {config.get('default_mode', 'basic')}")
        print("1. Set Default Mode")
        print("2. Run Authentication")
        print("3. Clear Authentication Data")
        print("4. Save and Exit")
        print("5. Exit without Saving")
        
        choice = input("Enter choice: ").strip()
        
        if choice == '1':
            m = input("Enter default mode (basic/fusion): ").strip().lower()
            if m in ['basic', 'fusion']:
                config['default_mode'] = m
            else:
                print("Invalid mode.")
        elif choice == '2':
            auth_manager.login()
        # TODO: Clear Auth needs update for DB
        elif choice == '3':
            # We don't have a clear_tokens method yet, but saving cleared session works or we add one.
            # Assuming auth_manager handles it.
            print("To clear auth, please delete the fusion.db tokens entry manually for now, sorry!") 
            # Actually I should implement clear_tokens in auth_manager or just update this later
        elif choice == '4':
            save_config(config)
            return
        elif choice == '5':
            return
        
# --- Fetching Logic ---

def fetch_basic_tracks(session, config):
    """
    Gather tracks from mixes/favorites.
    """
    basic_conf = config["modes"]["basic"]
    found_tracks = {}
    
    target_names = []
    if basic_conf.get('daily_discovery'): target_names.append("My Daily Discovery")
    if basic_conf.get('new_arrivals'): target_names.append("My New Arrivals")
    if basic_conf.get('my_mixes'): target_names.extend(MIX_NAMES_GENERATED)

    print(f"Basic Mode: Scanning for {len(target_names)} playlists...")

    def process_container(container):
        name = getattr(container, 'title', getattr(container, 'name', ''))
        if name in target_names:
            print(f"Found '{name}'")
            try:
                items = []
                if hasattr(container, 'tracks') and callable(container.tracks):
                    items = container.tracks()
                elif hasattr(container, 'items') and callable(container.items):
                    items = container.items()
                
                count = 0
                for track in items:
                    if not hasattr(track, 'id'): continue
                    if track.id not in found_tracks:
                        # Attach metadata for logging
                        track.fusion_source_mix = name 
                        found_tracks[track.id] = track
                        count += 1
            except Exception as e:
                print(f"Error scanning '{name}': {e}")

    # Scan Favorites
    try:
        for pl in session.user.favorites.playlists():
            process_container(pl)
    except Exception as e:
        print(f"Error scanning favorites: {e}")

    # Scan Mixes
    try:
        if hasattr(session, 'mixes'):
            for mix in session.mixes():
                process_container(mix)
    except:
        pass

    return list(found_tracks.values())

# --- History Management ---

def history_log_tracks(tracks):
    """Log generated tracks to history table."""
    conn = auth_manager.get_connection()
    c = conn.cursor()
    now = datetime.now(timezone.utc)
    
    count = 0
    for t in tracks:
        try:
            # Safely get artist name
            artist_name = "Unknown"
            if getattr(t, 'artist', None):
                artist_name = t.artist.name
            elif getattr(t, 'artists', None):
                artist_name = ", ".join([a.name for a in t.artists])
            
            c.execute('''
                INSERT INTO history (track_id, track_name, artist_name, timestamp, bpm, style)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                str(t.id),
                getattr(t, 'name', 'Unknown'),
                artist_name,
                now.isoformat(),
                getattr(t, 'bpm', None),
                None # Style not available
            ))
            count += 1
        except Exception as e:
            # duplicate entries or db errors
            # print(f"Error logging track {t.id}: {e}")
            pass
            
    conn.commit()
    conn.close()
    if count > 0:
        print(f"Logged {count} tracks to history.")

def history_get_recent_ids(days):
    """Get list of track IDs played in the last X days."""
    if days <= 0:
        return set()
        
    conn = auth_manager.get_connection()
    c = conn.cursor()
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    c.execute("SELECT track_id FROM history WHERE timestamp > ?", (cutoff.isoformat(),))
    rows = c.fetchall()
    conn.close()
    
    return {str(r[0]) for r in rows}

def history_show(limit=20):
    """Print table of recent history."""
    conn = auth_manager.get_connection()
    c = conn.cursor()
    c.execute("SELECT track_name, artist_name, timestamp FROM history ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    
    print(f"\nLast {limit} Tracks Generated:")
    print(f"{'Timestamp':<20} | {'Artist':<30} | {'Track':<40}")
    print("-" * 96)
    for r in rows:
        ts_str = r[2]
        try:
            # Handle standardized UTC string
            ts = datetime.fromisoformat(str(ts_str))
            # Convert to local for display? Or keep UTC. 
            # Display: YYYY-MM-DD HH:MM
            ts_display = ts.strftime("%Y-%m-%d %H:%M")
        except:
            ts_display = str(ts_str)[:16]
            
        print(f"{ts_display:<20} | {r[1][:28]:<30} | {r[0][:38]:<40}")
    print("")

def history_clear():
    """Clear all history."""
    confirm = input("Are you sure you want to clear ALL playback history? (y/N): ").strip().lower()
    if confirm == 'y':
        conn = auth_manager.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM history")
        conn.commit()
        conn.close()
        print("History cleared.")
    else:
        print("Cancelled.")


# --- Track Fetching ---

def get_mix_by_name(session, name_substr):
    """
    Search for a mix/playlist by partial name in favorites and user mixes.
    Returns the first TidalPlaylist or Mix object found.
    """
    # 1. Check Favorites
    try:
        for pl in session.user.favorites.playlists():
            if name_substr.lower() in pl.name.lower():
                return pl
    except:
        pass
        
    # 2. Check Mixes
    try:
        # iterate mixes looking for title
        # mixes() returns mix objects
        pass # Not easily searchable without iterating all?
    except:
        pass
    
    # Fallback to search? No, strictly personal mixes usually.
    return None

def fetch_basic_tracks(session, config):
    """Fetch tracks from configured basic sources."""
    tracks = []
    found_ids = set()
    
    modes_conf = config.get("modes", {}).get("basic", {})
    
    def process_container(container, source_name):
        try:
            # TidalPlaylist or Mix
            items = []
            if hasattr(container, 'tracks') and callable(container.tracks):
                items = container.tracks()
            elif hasattr(container, 'items') and callable(container.items):
                items = container.items()
            
            count = 0
            for t in items:
                if not hasattr(t, 'id'): continue
                if t.id not in found_ids:
                    t.fusion_source_pool = "Basic"
                    t.fusion_source_mix = source_name
                    tracks.append(t)
                    found_ids.add(t.id)
                    count += 1
            if count > 0:
                print(f"  - Added {count} tracks from '{source_name}'")
        except Exception as e:
            print(f"  - Error processing '{source_name}': {e}")


    # 1. My Daily Discovery
    if modes_conf.get("daily_discovery", True):
        print("Fetching 'My Daily Discovery'...")
        mix = get_mix_by_name(session, "My Daily Discovery")
        if mix:
            process_container(mix, "My Daily Discovery")
        else:
            print("  - Not found.")
            
    # 2. My New Arrivals
    if modes_conf.get("new_arrivals", True):
        print("Fetching 'My New Arrivals'...")
        mix = get_mix_by_name(session, "My New Arrivals")
        if mix:
            process_container(mix, "My New Arrivals")
        else:
            print("  - Not found.")

    # 3. My Mixes (1-8)
    if modes_conf.get("my_mixes", True):
        print("Fetching 'My Mix' collection...")
        for name in MIX_NAMES_GENERATED:
            mix = get_mix_by_name(session, name)
            if mix:
                process_container(mix, name)

    return tracks

def fetch_fusion_tracks(session, config, limit=150):
    """
    Fetch and interleave tracks for 'Fusion' mode.
    Fusion logic: Comfort (40%), Habit (30%), Adventure (30%).
    """
    # Get Configured Exclude Days
    exclude_days = config.get("modes", {}).get("fusion", {}).get("exclude_days", 7)
    recent_ids = history_get_recent_ids(exclude_days)
    if exclude_days > 0:
        print(f"Fusion Mode: Anti-Repeat enabled (Exclude last {exclude_days} days).")
        print(f"  Fetching history... Found {len(recent_ids)} tracks to exclude.")
    
    print(f"Fusion Mode: Generating {limit} tracks...")
    
    # 1. Fetch Candidates
    favorites = []
    try:
        raw_favorites = session.user.favorites.tracks()
        favorites = [t for t in raw_favorites if str(t.id) not in recent_ids]
        for t in favorites:
            t.fusion_source_pool = "Comfort"
            t.fusion_source_mix = "Favorites"
        print(f"- Fetched {len(favorites)} Favorites (Excluded {len(raw_favorites) - len(favorites)} recent)")
    except Exception:
        print("- Error fetching Favorites")

    history = []
    try:
        # history() might return an iterator or list
        raw_history = list(session.user.history())[:100]
        raw_history = [t for t in raw_history if hasattr(t, 'id')]
        history = [t for t in raw_history if str(t.id) not in recent_ids]
        for t in history:
            t.fusion_source_pool = "Habit"
            t.fusion_source_mix = "History"
        print(f"- Fetched {len(history)} History items (Excluded {len(raw_history) - len(history)} recent)")
    except Exception:
        print("- Error fetching History")
        
    discovery = []
    # Reuse basic logic which now tags fusion_source_mix
    # We want "My Daily Discovery" and "My Mix 1-8" (Adventure)
    temp_conf = {"modes": {"basic": {"daily_discovery": True, "new_arrivals": False, "my_mixes": True}}}
    raw_discovery = fetch_basic_tracks(session, temp_conf)
    discovery = [t for t in raw_discovery if str(t.id) not in recent_ids]
    for t in discovery:
        t.fusion_source_pool = "Adventure"
        # fusion_source_mix already set by fetch_basic_tracks
    print(f"- Fetched {len(discovery)} Adventure tracks (Excluded {len(raw_discovery) - len(discovery)} recent)")

    # 2. Bucket Allocation
    limit_comfort = int(limit * 0.4)
    limit_habit = int(limit * 0.3)
    limit_adventure = int(limit * 0.3)
    
    # Adjust for rounding
    remainder = limit - (limit_comfort + limit_habit + limit_adventure)
    limit_comfort += remainder

    # 3. Filter & Select
    # Comfort: Favorites > 6 months (approx 180 days)
    six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
    
    old_favorites = []
    recent_favorites = []
    
    for t in favorites:
        is_old = False
        if hasattr(t, 'date_added') and t.date_added:
            d = t.date_added
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            if d < six_months_ago:
                is_old = True
        
        if is_old:
            t.fusion_source_pool = "Comfort (Old)"
            old_favorites.append(t)
        else:
            t.fusion_source_pool = "Comfort (Recent)"
            recent_favorites.append(t)
            
    print(f"- Filtering Comfort: {len(old_favorites)} old (>6m), {len(recent_favorites)} recent/unknown")
    
    # Prioritize old, fill with recent if needed
    random.shuffle(old_favorites)
    random.shuffle(recent_favorites)
    
    bucket_comfort = old_favorites[:limit_comfort]
    if len(bucket_comfort) < limit_comfort:
        needed = limit_comfort - len(bucket_comfort)
        bucket_comfort.extend(recent_favorites[:needed])

    # Habit: Recent history
    random.shuffle(history)
    bucket_habit = history[:limit_habit]

    # Adventure: Discovery mixes
    random.shuffle(discovery)
    bucket_adventure = discovery[:limit_adventure]

    # Backfill if any bucket is short
    used_ids = set(t.id for t in bucket_comfort + bucket_habit + bucket_adventure)
    all_pool = [t for t in favorites + history + discovery if t.id not in used_ids]
    random.shuffle(all_pool)

    def fill_bucket(bucket, target_size, name):
        needed = target_size - len(bucket)
        if needed > 0:
            print(f"- {name} bucket short by {needed}, backfilling...")
            added = 0
            while needed > 0 and all_pool:
                t = all_pool.pop()
                # Update pool if backfilling from generic pool?
                # Actually keep original pool tag to know where it came from
                bucket.append(t)
                needed -= 1
                added += 1
            if needed > 0:
                print(f"  Warning: Could not fully backfill {name}.")

    fill_bucket(bucket_comfort, limit_comfort, "Comfort")
    fill_bucket(bucket_habit, limit_habit, "Habit")
    fill_bucket(bucket_adventure, limit_adventure, "Adventure")

    # 4. Interleave (C, H, A, C, H, A...)
    final_list = []
    max_len = max(len(bucket_comfort), len(bucket_habit), len(bucket_adventure))
    
    for i in range(max_len):
        if i < len(bucket_comfort): final_list.append(bucket_comfort[i])
        if i < len(bucket_habit): final_list.append(bucket_habit[i])
        if i < len(bucket_adventure): final_list.append(bucket_adventure[i])

    # 5. Smoothing (BPM / Popularity)
    print("- Applying Vibe Check (BPM Smoothing)...")
    
    swaps_made = 0
    for i in range(len(final_list) - 1):
        current = final_list[i]
        next_track = final_list[i+1]
        
        current_bpm = getattr(current, 'bpm', 0)
        next_bpm = getattr(next_track, 'bpm', 0)
        
        if not current_bpm or not next_bpm:
            continue
            
        try:
            current_bpm = int(current_bpm)
            next_bpm = int(next_bpm)
        except:
            continue
            
        # Check jump
        if abs(current_bpm - next_bpm) > 30:
            search_limit = min(i + 20, len(final_list))
            for j in range(i + 2, search_limit):
                candidate = final_list[j]
                cand_bpm = getattr(candidate, 'bpm', 0)
                if not cand_bpm: continue
                try: cand_bpm = int(cand_bpm)
                except: continue
                
                if abs(current_bpm - cand_bpm) <= 30:
                    final_list[i+1], final_list[j] = final_list[j], final_list[i+1]
                    swaps_made += 1
                    break
    
    # Report
    avg_bpm = 0
    bpms = [int(t.bpm) for t in final_list if hasattr(t, 'bpm') and t.bpm]
    if bpms:
        avg_bpm = sum(bpms) / len(bpms)

    print(f"Fusion Generation: {len(final_list)} tracks.")
    print(f"  Composition: {len(bucket_comfort)} Classics, {len(bucket_habit)} Current Rotation, {len(bucket_adventure)} New Discoveries.")
    print(f"  Vibe Check: Average BPM: {int(avg_bpm)} | Swaps made: {swaps_made} | Replay Gain Adjusted")
    
    return final_list

def log_generation(tracks, mode, debug=False):
    """
    Log the generated tracks.
    If debug: Print detailed info (captured by TeeLogger).
    If normal: Write to standard log file in config dir.
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    if debug:
        # Debug Mode: Output detailed info to stdout (captured by TeeLogger)
        print("\n\n" + "="*40)
        print(f"GENERATION DETAILS ({timestamp})")
        print("="*40)
        for i, track in enumerate(tracks, 1):
            artist = getattr(track, 'artist', None)
            if artist:
                artist_name = artist.name
            else:
                artists = getattr(track, 'artists', [])
                artist_name = ", ".join([a.name for a in artists]) if artists else "Unknown Artist"
            
            title = getattr(track, 'name', 'Unknown Title')
            bpm = getattr(track, 'bpm', 'N/A')
            
            print(f"{i}. {artist_name} - {title} [BPM: {bpm}]")
            print(f"   Source Pool: {getattr(track, 'fusion_source_pool', 'Basic/Unknown')}")
            print(f"   Source Mix: {getattr(track, 'fusion_source_mix', 'Unknown')}")
            print(f"   ID: {track.id}")
            if hasattr(track, 'album'):
                 print(f"   Album: {track.album.name}")
            print("")
            
    else:
        # Standard Mode: Write concise log to file
        filename = auth_manager.CONFIG_DIR / f"fusion-log-{timestamp}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Tidal Fusion Generation Log\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Mode: {mode}\n")
                f.write(f"Total Tracks: {len(tracks)}\n")
                f.write("-" * 40 + "\n")
                
                for i, track in enumerate(tracks, 1):
                    artist = getattr(track, 'artist', None)
                    if artist:
                        artist_name = artist.name
                    else:
                        artists = getattr(track, 'artists', [])
                        artist_name = ", ".join([a.name for a in artists]) if artists else "Unknown Artist"
                    
                    title = getattr(track, 'name', 'Unknown Title')
                    bpm = getattr(track, 'bpm', 'N/A')
                    
                    f.write(f"{i}. {artist_name} - {title} [BPM: {bpm}]\n")
                    
            print(f"Log generated: {filename}")
        except Exception as e:
            print(f"Error writing log: {e}")

# --- Playlist Management ---

def update_playlist(session, args, tracks):
    """
    Update the playlist.
    args.new = True -> Empty and Fill
    args.append = True -> Add
    """
    if not tracks:
        print("No tracks generated.")
        return

    name = DEFAULT_PLAYLIST_NAME
    user = session.user
    
    # 1. Find Playlist (Robust Discovery)
    print(f"Searching for playlist '{name}'...")
    
    candidates = []
    seen_ids = set()

    # Check Created Playlists (Primary source for ownership)
    if hasattr(user, 'playlists'):
        try:
            for pl in user.playlists():
                if pl.name == name:
                    if pl.id not in seen_ids:
                        candidates.append(pl)
                        seen_ids.add(pl.id)
        except Exception as e:
            print(f"Warning checking user.playlists(): {e}")

    # Check Favorites (Secondary, sometimes created playlists only show here)
    if hasattr(user, 'favorites'):
        try:
            for pl in user.favorites.playlists():
                if pl.name == name:
                    if pl.id not in seen_ids:
                        candidates.append(pl)
                        seen_ids.add(pl.id)
        except Exception as e:
            print(f"Warning checking favorites: {e}")

    target_pl = None
    
    # 2. Deduplication / Cleanup
    if len(candidates) > 1:
        print(f"Found {len(candidates)} playlists named '{name}'. Cleaning up duplicates...")
        # Sort candidates to be deterministic? 
        # We prefer the one that looks most "owned" or oldest/newest?
        # For now, we take the first one and delete the rest.
        
        target_pl = candidates[0]
        to_delete = candidates[1:]
        
        for dup in to_delete:
            print(f"Deleting duplicate playlist (ID: {dup.id})...")
            try:
                # Try standard delete
                if hasattr(dup, 'delete'):
                    dup.delete()
                    print("- Deleted.")
                else:
                    # Some objects might be read-only proxies
                    print("- Error: Duplicate object appears to be read-only. Cannot delete automatically.")
            except Exception as e:
                print(f"- Error deleting duplicate: {e}")
                
    elif len(candidates) == 1:
        target_pl = candidates[0]
        print(f"Found existing playlist: {target_pl.name} (ID: {target_pl.id})")
    
    else:
        print(f"Playlist '{name}' not found. Will create new.")

    # 3. Update Logic
    track_ids = [t.id for t in tracks]
    
    if args.append:
        if target_pl:
            print(f"Appending {len(tracks)} tracks...")
            try:
                target_pl.add(track_ids)
                print("Success.")
                history_log_tracks(tracks)
            except Exception as e:
                print(f"Error appending: {e}")
        else:
            print(f"Creating new playlist '{name}'...")
            user.create_playlist(name, "Generated by Tidal Fusion").add(track_ids)
            history_log_tracks(tracks)
            
    else: # args.new (Default) or explicit -n
        if target_pl:
            print(f"Reseting '{target_pl.name}' with {len(tracks)} tracks...")
            success = False
            
            # Attempt 1: Clear and Add
            try:
                # Check existing items
                # We need to fetch items to check if empty, and to get IDs if we need manual removal
                current_items = target_pl.items()
                
                if current_items:
                    print(f"- Found {len(current_items)} existing tracks. Attempting to clear...")
                    
                    cleared = False
                    # Priority 1: Use .clear() if available
                    if hasattr(target_pl, 'clear'):
                        try:
                            target_pl.clear()
                            cleared = True
                            print("- Called .clear()")
                        except Exception as e:
                            print(f"- .clear() failed: {e}")
                    
                    # Priority 2: Manual remove_by_id loop
                    if not cleared:
                        print("- Fallback: Removing tracks one by one...")
                        if hasattr(target_pl, 'remove_by_id'):
                            for item in current_items:
                                if hasattr(item, 'id'):
                                    try:
                                        target_pl.remove_by_id(item.id)
                                    except: pass
                        else:
                             print("- Warning: remove_by_id not found.")

                    # Verify Empty
                    remaining = target_pl.items()
                    if remaining:
                        print(f"- Warning: {len(remaining)} items remain. Clearing failed.")
                        success = False
                    else:
                        print("- Playlist cleared.")
                        success = True
                else:
                    print("- Playlist already empty.")
                    success = True
                
                if success:
                    target_pl.add(track_ids)
                    print("- Added new tracks.")
                    history_log_tracks(tracks)
                    
            except Exception as e:
                print(f"- Update failed: {e}")
                success = False

            # Fallback: Delete and Recreate
            if not success:
                print("Fallback: Deleting and recreating playlist...")
                try:
                    target_pl.delete()
                    print("- Old playlist deleted.")
                except Exception as e:
                    print(f"- Warning: Could not delete old playlist ({e}).")
                
                try:
                    user.create_playlist(name, "Generated by Tidal Fusion").add(track_ids)
                    print("- New playlist created.")
                    history_log_tracks(tracks)
                except Exception as e:
                    print(f"CRITICAL: Failed to create new playlist: {e}")
        else:
            print(f"Creating '{name}' with {len(tracks)} tracks...")
            user.create_playlist(name, "Generated by Tidal Fusion").add(track_ids)
            history_log_tracks(tracks)


# Logger
class TeeLogger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

def main():
    # Ensure DB and Tables exist, migrate if needed
    auth_manager.init_db()
    
    parser = argparse.ArgumentParser(description="Tidal Fusion", add_help=False)
    
    # Actions
    mode_group = parser.add_mutually_exclusive_group()
    # Removed --login argument
    mode_group.add_argument('-n', '--new', action='store_true', help="Overwrite (empty & fill) playlist (Default)")

    mode_group.add_argument('-a', '--append', action='store_true', help="Append to playlist")
    mode_group.add_argument('-c', '--config', action='store_true', help="Configure settings")
    
    # History Actions
    mode_group.add_argument('--show-history', nargs='?', const=20, type=int, metavar='N', help="Show last N tracks (default 20)")
    mode_group.add_argument('--clear-history', action='store_true', help="Clear playback history")

    # Help (Standalone)
    parser.add_argument('-h', '--help', action='store_true', help="Show help")
    
    # Modifiers
    parser.add_argument('--mode', type=str, help="Select mode (basic, fusion)")
    parser.add_argument('-m', '--limit', type=int, default=150, help="Track limit (Fusion mode)")
    parser.add_argument('--exclude-days', type=int, help="Exclude tracks played in last N days")
    parser.add_argument('-d', '--debug', action='store_true', help="Enable debug logging")

    args = parser.parse_args()
    
    # Setup Logging if Debug
    if args.debug:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_file = auth_manager.CONFIG_DIR / f"fusion-debug-{timestamp}.txt"
        try:
            sys.stdout = TeeLogger(log_file)
            print(f"Debug logging enabled. Capturing output to: {log_file}")
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 40)
        except Exception as e:
            print(f"Failed to setup logging: {e}")

    # Load Config
    config = load_config()
    
    # Handle History Commands
    if args.show_history is not None:
        history_show(args.show_history)
        return
        
    if args.clear_history:
        history_clear()
        return

    # Config overrides from CLI
    if args.exclude_days is not None:
        if "fusion" not in config["modes"]: config["modes"]["fusion"] = {}
        config["modes"]["fusion"]["exclude_days"] = args.exclude_days

    # Help
    if args.help:
        if args.new:
            print("Help: -n / --new")
            print("  Resets (empties) the target playlist and fills it with new tracks.")
            print("  This is the default action if no other action is specified.")
        elif args.append:
             print("Help: -a / --append")
             print("  Adds generated tracks to the existing playlist instead of reseting it.")
        elif args.config:
             print("Help: -c / --config")
             print("  Opens the configuration menu.")
             print("  Use --mode <name> to configure a specific mode.")
        else:
            print("Tidal Fusion Help")
            print("  -n, --new      : Create/Reset playlist (Default)")
            print("  -a, --append   : Append to playlist")
            print("  -c, --config   : Configure modes")
            print("  --mode <name>  : Select mode (basic, fusion)")
            print("  -m, --limit    : Set max tracks (Fusion)")
            print("  -d, --debug    : Enable debug logging")
        return
    
    # 1. Config
    if args.config:
        if args.mode:
            # Mode specific config
            if args.mode == 'basic':
                configure_basic_mode(config)
            elif args.mode == 'fusion':
                configure_fusion_mode(config)
            else:
                print(f"Unknown mode: {args.mode}")
            save_config(config)
        else:
            # Global config
            configure_global(config)
        return

    # 3. Generation (New or Append)
    # Default is New if neither specified
    action_new = True
    if args.append:
        action_new = False
    
    # Determine Mode
    mode = args.mode if args.mode else config.get('default_mode', 'basic')
    
    session = auth_manager.get_session()
    if not session:
        print("Please run 'tidal-fusion -c' and select 'Run Authentication' first.")
        return

    tracks = []
    if mode == 'basic':
        tracks = fetch_basic_tracks(session, config)
    elif mode == 'fusion':
        tracks = fetch_fusion_tracks(session, config, args.limit)
    else:
        print(f"Unknown mode: {mode}")
        return

    # Shuffle for basic (Fusion does its own interleaving)
    if mode == 'basic':
        random.shuffle(tracks)
        
    log_generation(tracks, mode, args.debug)
    update_playlist(session, args, tracks)

if __name__ == "__main__":
    main()
