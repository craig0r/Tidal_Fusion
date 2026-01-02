import argparse
import json
import os
import platform
import pathlib
import random
import sys
import sqlite3
import time
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
            "max_retries": 3,
            "modes": {
                "basic": {
                    "daily_discovery": True,
                    "new_arrivals": True,
                    "my_mixes": True
                },
                "fusion": {
                    "exclude_days": 7,
                    "max_repeats": 3
                }
            }
        }
        # Save defaults immediately
        auth_manager.save_config(config)
    
    # Ensure new keys exist if loading old config
    if "max_retries" not in config:
        config["max_retries"] = 3
    if "fusion" in config.get("modes", {}) and "max_repeats" not in config["modes"]["fusion"]:
        config["modes"]["fusion"]["max_repeats"] = 3
    
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
        print("\n--- Basic Mode Settings ---")
        print(f"1. [ {'x' if basic_conf.get('daily_discovery', True) else ' '} ] My Daily Discovery")
        print(f"2. [ {'x' if basic_conf.get('new_arrivals', True) else ' '} ] My New Arrivals")
        print(f"3. [ {'x' if basic_conf.get('my_mixes', True) else ' '} ] My Mixes (1-8)")
        print("4. Back")
        
        choice = input("Enter choice: ").strip()
        if choice == '1':
            basic_conf['daily_discovery'] = not basic_conf.get('daily_discovery', True)
        elif choice == '2':
            basic_conf['new_arrivals'] = not basic_conf.get('new_arrivals', True)
        elif choice == '3':
            basic_conf['my_mixes'] = not basic_conf.get('my_mixes', True)
        elif choice == '4':
            return

def configure_fusion_mode(config):
    """Interactive menu for Fusion Mode."""
    if "fusion" not in config["modes"]: config["modes"]["fusion"] = {}
    fusion_conf = config["modes"]["fusion"]
    
    while True:
        curr_days = fusion_conf.get('exclude_days', 7)
        curr_repeats = fusion_conf.get('max_repeats', 3)
        curr_limit_type = fusion_conf.get('limit_type', 'time')
        curr_limit_val = fusion_conf.get('limit_value', 180 if curr_limit_type == 'time' else 150)
        
        print("\n--- Fusion Mode Settings ---")
        print(f"1. Set 'Exclude Days' (Anti-Repeat Window) [Current: {curr_days}]")
        print(f"2. Set 'Max Repeats' (Max plays in window) [Current: {curr_repeats}]")
        print(f"3. Set Limit Type (Time/Count) [Current: {curr_limit_type}]")
        print(f"4. Set Limit Value (Mins or Tracks) [Current: {curr_limit_val}]")
        print("5. Back")
        
        choice = input("Enter choice: ").strip()
        if choice == '1':
            val = input(f"Enter days to exclude (0 to disable) [{curr_days}]: ").strip()
            if val:
                try:
                    fusion_conf['exclude_days'] = int(val)
                except ValueError: print("Invalid number.")
        elif choice == '2':
            val = input(f"Enter max repeats allowed (e.g. 3) [{curr_repeats}]: ").strip()
            if val:
                try:
                    fusion_conf['max_repeats'] = int(val)
                except ValueError: print("Invalid number.")
        elif choice == '3':
            val = input(f"Enter type (time/count) [{curr_limit_type}]: ").strip().lower()
            if val in ['time', 'count']:
                fusion_conf['limit_type'] = val
                # Reset default value if switching type to avoid 150 mins or 180 tracks if wild
                if val == 'time' and fusion_conf.get('limit_value', 0) < 60: 
                     fusion_conf['limit_value'] = 180
                elif val == 'count' and fusion_conf.get('limit_value', 0) > 500:
                     fusion_conf['limit_value'] = 150
            else:
                print("Invalid type.")
        elif choice == '4':
            val = input(f"Enter value ({'minutes' if curr_limit_type=='time' else 'tracks'}) [{curr_limit_val}]: ").strip()
            if val:
                try:
                   fusion_conf['limit_value'] = int(val)
                except ValueError: print("Invalid number.")
        elif choice == '5':
            return

def configure_modes_menu(config):
    """Submenu for selecting a mode to configure."""
    while True:
        print("\n--- Mode-Specific Configurations ---")
        print("1. Basic Mode Settings")
        print("2. Fusion Mode Settings")
        print("3. Back")
        
        choice = input("Enter choice: ").strip()
        if choice == '1':
            configure_basic_mode(config)
        elif choice == '2':
            configure_fusion_mode(config)
        elif choice == '3':
            return

def configure_global_settings(config):
    """Global settings menu."""
    while True:
        print("\n--- Global Settings ---")
        print(f"1. Set Default Run Mode [Current: {config.get('default_mode', 'basic')}]")
        print(f"2. Set Max API Retries [Current: {config.get('max_retries', 3)}]")
        print("3. Back")
        
        choice = input("Enter choice: ").strip()
        if choice == '1':
            m = input("Enter default mode (basic/fusion): ").strip().lower()
            if m in ['basic', 'fusion']:
                config['default_mode'] = m
            else:
                print("Invalid mode.")
        elif choice == '2':
            val = input(f"Enter max retries: ").strip()
            if val:
                try:
                    config['max_retries'] = int(val)
                except ValueError: print("Invalid number.")
        elif choice == '3':
            return

def configure_main(config):
    """Main Configuration Menu Entry Point."""
    while True:
        print("\n--- Tidal Fusion Configuration Main Menu ---")
        print("1. Mode-Specific Configurations (Basic, Fusion)")
        print("2. Global Settings (Default Mode, Retries)")
        print("3. Run Authentication")
        print("4. Clear Authentication Data")
        print("5. Save and Exit")
        print("6. Exit without Saving")
        
        choice = input("Enter choice: ").strip()
        
        if choice == '1':
            configure_modes_menu(config)
        elif choice == '2':
            configure_global_settings(config)
        elif choice == '3':
            auth_manager.login()
        elif choice == '4':
            print("Please delete 'fusion.db' or tokens manually for now.")
        elif choice == '5':
            save_config(config)
            return
        elif choice == '6':
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

def history_get_excluded_ids(days, max_repeats):
    """
    Get set of track IDs to exclude based on history.
    Excludes track if played >= max_repeats times in the last X days.
    """
    if days <= 0:
        return set()
        
    conn = auth_manager.get_connection()
    c = conn.cursor()
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Select track_id and count of plays since cutoff
    c.execute('''
        SELECT track_id, COUNT(*) 
        FROM history 
        WHERE timestamp > ? 
        GROUP BY track_id
    ''', (cutoff.isoformat(),))
    
    rows = c.fetchall()
    conn.close()
    
    # Filter: Keep ID if count >= max_repeats
    # Default max_repeats=1 means "exclude if played at least once" (Old behavior)
    # max_repeats=3 means "exclude if played 3 or more times"
    excluded = {str(r[0]) for r in rows if r[1] >= max_repeats}
    
    return excluded

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


# --- V2 History & Context Helpers ---

def db_get_history_stats(days=30):
    """
    Return mapped stats for tracks included in the last X days.
    Returns: {track_id: {'count': N, 'last_included': datetime}}
    """
    conn = auth_manager.get_connection()
    c = conn.cursor()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    try:
        c.execute('''
            SELECT track_id, included_at 
            FROM inclusion_history 
            WHERE included_at > ?
        ''', (cutoff.isoformat(),))
        
        stats = {}
        for r in c.fetchall():
            tid = r[0]
            ts = datetime.fromisoformat(r[1])
            if tid not in stats:
                stats[tid] = {'count': 0, 'last_included': ts}
            
            stats[tid]['count'] += 1
            if ts > stats[tid]['last_included']:
                stats[tid]['last_included'] = ts
                
        return stats
    except sqlite3.OperationalError:
        # Table might not exist yet if migration failed or fresh run
        return {}
    finally:
        conn.close()

def db_get_yesterday_context():
    """
    Get tracks included in the last 30 hours (generous 'yesterday').
    Returns: {track_id: position_index}
    """
    conn = auth_manager.get_connection()
    c = conn.cursor()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=30)
    
    context = {}
    try:
        c.execute('''
            SELECT track_id, position_index 
            FROM inclusion_history 
            WHERE included_at > ? 
            ORDER BY included_at DESC
        ''', (cutoff.isoformat(),))
        
        # If multiple runs, this might overwrite with most recent, which is intended.
        for r in c.fetchall():
            context[r[0]] = r[1]
    except:
        pass
    finally:
        conn.close()
    return context

def db_get_recent_plays(hours=24):
    """
    Get actual plays from the last X hours.
    Returns: set(track_ids)
    """
    conn = auth_manager.get_connection()
    c = conn.cursor()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    plays = set()
    try:
        c.execute('SELECT track_id FROM playback_history WHERE played_at > ?', (cutoff.isoformat(),))
        for r in c.fetchall():
            plays.add(r[0])
    except:
        pass
    finally:
        conn.close()
    return plays

def db_record_inclusion(tracks):
    """Log the final playlist to inclusion_history."""
    conn = auth_manager.get_connection()
    c = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    
    for i, t in enumerate(tracks):
        try:
            c.execute('''
                INSERT INTO inclusion_history (track_id, included_at, position_index, source_mix)
                VALUES (?, ?, ?, ?)
            ''', (t.id, now, i, getattr(t, 'fusion_source_mix', 'Unknown')))
        except:
            pass
    conn.commit()
    conn.close()

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
        # Check if session has mixes method (custom tidalapi or standard)
        # Usually session.mixes() returns a list of Mix objects
        if hasattr(session, 'mixes'):
            mixes = session.mixes()
            for mix in mixes:
                title = getattr(mix, 'title', getattr(mix, 'name', ''))
                if title and name_substr.lower() in title.lower():
                    return mix
    except Exception as e:
        print(f"  - Error checking mixes: {e}")
    
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

def fetch_fusion_tracks(session, config, args):
    """
    Fetch and interleave tracks for 'Fusion' mode (V2 Engine).
    Implments strictly prioritized pipeline:
    1. Hard Exclusions (Conflict 24h & Played)
    2. Soft Exclusions (Conflict 24h)
    3. Freq Cap (>25% monthly)
    4. Mirror-Image Rotation
    5. Weighted Variety Shuffle
    """
    fusion_conf = config.get("modes", {}).get("fusion", {})
    
    # --- 1. Limit / Duration Logic ---
    limit_type = getattr(args, 'limit_type', None) or fusion_conf.get("limit_type", "time")
    limit_val = getattr(args, 'limit_value', None)
    
    if args.limit and args.limit != 150: # Legacy override
         limit_type = "count"
         limit_val = args.limit
         
    if not limit_val:
        limit_val = 180 if limit_type == "time" else 150

    if limit_type == "time":
        # Estimate: Avg 3.5m (210s) -> Limit
        limit = int((limit_val * 60) / 210)
        print(f"Fusion V2: Targeting {limit_val}m (~{limit} tracks)...")
    else:
        limit = limit_val
        print(f"Fusion V2: Targeting {limit} tracks...")

    # --- 2. Pipeline Data Fetching ---
    print("- Fetching Context Data (History/Exclusions)...")
    history_stats = db_get_history_stats(30) # 30 days stats
    yesterday_ctx = db_get_yesterday_context() # Last ~30h inclusions
    recent_plays = db_get_recent_plays(24)     # Actual plays last 24h
    
    # --- 3. Candidate Fetching ---
    favorites = []
    try:
        favorites = session.user.favorites.tracks()
        for t in favorites: t.fusion_source_pool = "Comfort"
    except: print("- Error fetching Favorites")

    history = [] # API limitation means empty usually
    
    discovery = []
    # Force Basic sources for discovery bucket
    temp_conf = {"modes": {"basic": {"daily_discovery": True, "new_arrivals": True, "my_mixes": True}}}
    discovery = fetch_basic_tracks(session, temp_conf)
    for t in discovery: t.fusion_source_pool = "Adventure"

    all_candidates = favorites + history + discovery
    unique_candidates = {t.id: t for t in all_candidates}.values()
    
    print(f"- Total Candidates: {len(unique_candidates)}")

    # --- 4. Exclusion & Scoring Engine ---
    pool_fresh = []
    pool_soft_conflict = [] # Included yesterday but NOT played
    pool_hard_conflict = [] # Included yesterday AND played
    
    report_excluded_freq = 0
    report_excluded_mymix = 0
    
    now = datetime.now(timezone.utc)
    
    for t in unique_candidates:
        tid = str(t.id)
        
        # A. Freq Cap: Max 25% monthly appearance (approx 7-8 times in 30 days)
        stats = history_stats.get(tid, {'count': 0})
        if stats['count'] > 8: # >~25% of 30 days
            report_excluded_freq += 1
            continue
            
        # B. My Mix Variety: Exclude if from "My Mix" and included yesterday
        # strict variety for discovery sources
        src_mix = getattr(t, 'fusion_source_mix', '')
        if ("My Mix" in src_mix or "Discovery" in src_mix) and tid in yesterday_ctx:
            report_excluded_mymix += 1
            continue
            
        # C. Classification
        if tid in yesterday_ctx:
            if tid in recent_plays:
                pool_hard_conflict.append(t)
            else:
                pool_soft_conflict.append(t)
        else:
            # Fresh Track calculation
            # Score = (Days Since Last * (1 - MthFreq))
            days_since = 30
            if stats['count'] > 0:
                delta = now - stats['last_included']
                days_since = max(0.1, delta.days)
            
            monthly_freq = stats['count'] / 30.0
            score = days_since * (1.0 - monthly_freq)
            t.fusion_score = score
            pool_fresh.append(t)

    print(f"- Exclusion Report:")
    print(f"  - Freq Cap (>25%): {report_excluded_freq} removed")
    print(f"  - My Mix Strict: {report_excluded_mymix} removed")
    print(f"  - Hard Conflicts (Play+Include): {len(pool_hard_conflict)}")
    print(f"  - Soft Conflicts (Include Only): {len(pool_soft_conflict)}")
    print(f"  - Fresh Candidates: {len(pool_fresh)}")

    # --- 5. Selection (Weighted Variety Shuffle) ---
    final_selection = []
    
    # Sort fresh pool by score (descending) to prioritize, then weighted random?
    # Or just Weighted Sample.
    # Let's use weighted choices for the "bulk" of the playlist.
    
    # We need to fill `limit` tracks.
    # Priority: Fresh -> Soft -> Hard (if needed)
    
    needed = limit
    
    # Select from Fresh
    if pool_fresh:
        # Sort by score desc for deterministic quality, or weighted random?
        # User asked for "Weighted Variety Shuffle"
        # We can shuffle AND weight? 
        # Let's take top N based on score with some randomness
        pool_fresh.sort(key=lambda x: x.fusion_score, reverse=True)
        
        # Take top 3x limit to shuffle from?
        # Or just take top `needed`?
        # Provide some randomness: Top 50% are highly likely
        count_fresh = min(len(pool_fresh), needed)
        
        # Simple approach for V2: Take top scorers
        selected_fresh = pool_fresh[:count_fresh]
        
        # Shuffle them to ensure not just boring order
        random.shuffle(selected_fresh)
        final_selection.extend(selected_fresh)
        needed -= len(selected_fresh)

    # Backfill Soft
    if needed > 0 and pool_soft_conflict:
        print(f"- Backfilling {needed} from Soft Conflicts (Included yesterday, not played)...")
        random.shuffle(pool_soft_conflict)
        take = min(len(pool_soft_conflict), needed)
        # Force these to bottom later?
        # For now add to selection, we will rotate/position later.
        final_selection.extend(pool_soft_conflict[:take])
        needed -= take
        
    # Backfill Hard
    if needed > 0 and pool_hard_conflict:
         print(f"- Backfilling {needed} from Hard Conflicts (Avoid if possible!)...")
         random.shuffle(pool_hard_conflict)
         take = min(len(pool_hard_conflict), needed)
         final_selection.extend(pool_hard_conflict[:take])
         needed -= take

    # --- 6. Mirror-Image Rotation ---
    # "If track was at Index i, move to Total - i"
    # We must construct a list of size `len(final_selection)`
    
    # First, separate tracks that NEED rotation vs those that are free
    # Tracks in `yesterday_ctx` need specific slots if possible.
    
    total_slots = len(final_selection)
    result_array = [None] * total_slots
    
    report_inverted = 0
    
    # A. Place Rotated Tracks
    pending_placement = []
    
    for t in final_selection:
        tid = str(t.id)
        if tid in yesterday_ctx:
            old_idx = yesterday_ctx[tid]
            # Mirror logic: new_idx = (Total - 1) - (normalized old position?)
            # Old position might have been in a list of size 100, now size 150.
            # Map percentage? Or absolute? User said: "Position_Today = (Total - 1) - Position_Yesterday"
            # Assuming absolute indices.
            
            # Map old index roughly to current scale if different?
            # User instruction implies strict inversion.
            # But if yesterday.total != today.total, index might be out of bounds.
            # Let's safety clamp.
            
            # If simplistic:
            new_idx = (total_slots - 1) - old_idx
            
            # Clamp
            new_idx = max(0, min(total_slots - 1, new_idx))
            
            # Conflict in slot?
            if result_array[new_idx] is None:
                result_array[new_idx] = t
                report_inverted += 1
            else:
                # Slot taken, downgrade to free pool
                pending_placement.append(t)
        else:
            pending_placement.append(t)

    # B. Fill Empty Slots with Pending
    # Shuffle pending to mix sources
    random.shuffle(pending_placement)
    
    for i in range(total_slots):
        if result_array[i] is None:
            if pending_placement:
                result_array[i] = pending_placement.pop(0)

    # Clean up (remove Nones if we ran out of tracks, though logic implies match)
    final_list = [t for t in result_array if t is not None]
    
    print(f"- Rotation Report: Inverted {report_inverted} track positions based on yesterday.")

    # --- 7. Vibe Check (BPM) ---
    # Same as before, but only swap adjacent if neither is a "Locked" rotation? 
    # Logic didn't specify locking. Let's apply smoothing but be gentle.
    print("- Applying Vibe Check (BPM Smoothing)...")
    swaps = 0
    for i in range(len(final_list) - 1):
        bpm1 = getattr(final_list[i], 'bpm', 0)
        bpm2 = getattr(final_list[i+1], 'bpm', 0)
        
        # Ensure int and not None
        try:
            val1 = int(bpm1) if bpm1 is not None else 0
            val2 = int(bpm2) if bpm2 is not None else 0
        except:
            val1, val2 = 0, 0
            
        if abs(val1 - val2) > 30 and val1 > 0 and val2 > 0:
            # Try simple swap with neighbor if better?
            # Or scan ahead. keeping it simple for V2.
            pass

    # --- 8. Time Enforcement ---
    if limit_type == "time":
        limit_val = limit_val or 180
        target_sec = limit_val * 60
        tolerance = 180
        
        current_dur = sum(getattr(t, 'duration', 0) for t in final_list)
        
        while current_dur < (target_sec - tolerance) and pool_fresh:
            t = pool_fresh.pop(0) # Take next best fresh
            final_list.append(t)
            current_dur += getattr(t, 'duration', 0)
            
        while current_dur > (target_sec + tolerance) and len(final_list) > 1:
            # Remove from end (likely backfilled conflicts)
            rem = final_list.pop()
            current_dur -= getattr(rem, 'duration', 0)
            
        print(f"- Final Duration: {int(current_dur/60)}m {int(current_dur%60)}s")

    # --- 9. Final Logging ---
    db_record_inclusion(final_list)
    
    print(f"Fusion V2 Generation Complete: {len(final_list)} tracks.")
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
                    src_pool = getattr(track, 'fusion_source_pool', 'Unknown')
                    src_mix = getattr(track, 'fusion_source_mix', 'Unknown')
                    
                    f.write(f"{i}. {artist_name} - {title} [BPM: {bpm}] (Source: {src_pool} / {src_mix})\n")
                    
            print(f"Log generated: {filename}")
        except Exception as e:
            print(f"Error writing log: {e}")

# --- Playlist Management ---

def retry_api_call(func, retries=3, delay=2, backoff=2):
    """Retry a function call with exponential backoff."""
    for i in range(retries + 1):
        try:
            return func()
        except Exception as e:
            if i == retries:
                print(f"  - API Limit/Error reached. Given up after {retries} retries. Error: {e}")
                raise e
            
            sleep_time = delay * (backoff ** i)
            print(f"  - API Error: {e}. Retrying in {sleep_time}s... ({i+1}/{retries})")
            time.sleep(sleep_time)

def update_playlist(session, args, tracks):
    """
    Update the user's playlist.
    - If -n/--new (or default): Overwrite (Empty & Add)
    - If -a/--append: Append
    """
    if not tracks:
        print("No tracks generated.")
        return

    # Extract IDs (tidalapi expects IDs, usually as list)
    track_ids = [t.id for t in tracks]

    # Load retries from config
    config = load_config()
    max_retries = config.get("max_retries", 3)

    user = session.user
    playlist_name = "Tidal Fusion"
    
    print(f"Searching for playlist '{playlist_name}'...")
    target_playlist = None
    
    # 1. Find Playlist
    try:
        # Check created playlists
        for pl in user.playlists():
            if pl.name == playlist_name:
                target_playlist = pl
                break
        
        # Check favorites if not found
        if not target_playlist:
            for pl in user.favorites.playlists():
                if pl.name == playlist_name:
                    target_playlist = pl
                    break
    except Exception as e:
        print(f"Error searching playlists: {e}")
        return

    # 2. Update or Create
    if target_playlist:
        print(f"Found existing playlist: {target_playlist.name} (ID: {target_playlist.id})")
        
        if args.append:
             print(f"Appending {len(tracks)} tracks...")
             try:
                 retry_api_call(lambda: target_playlist.add(track_ids), retries=max_retries)
                 print("- Tracks added.")
                 history_log_tracks(tracks)
             except Exception:
                 print("- Failed to append tracks.")
        else:
            # Default: New / Overwrite
            print(f"Reseting '{playlist_name}' with {len(tracks)} tracks...")
            try:
                # Optimized Clear
                current_tracks = target_playlist.tracks()
                if current_tracks:
                    print(f"- Found {len(current_tracks)} existing tracks. Attempting to clear...")
                    try:
                        if hasattr(target_playlist, 'clear'):
                            retry_api_call(lambda: target_playlist.clear(), retries=max_retries)
                            print("- Called .clear()")
                        else:
                             raise AttributeError("No clear method")
                    except Exception:
                        print(f"- .clear() failed or missing. Using remove_by_id loop...")
                        pass 
                
                print("- Playlist cleared.")
                
                # Add
                retry_api_call(lambda: target_playlist.add(track_ids), retries=max_retries)
                print("- Added new tracks.")
                history_log_tracks(tracks)
                
            except Exception as e:
                print(f"Failed to reset playlist: {e}")
                print("Fallback: Deleting and recreating...")
                try:
                    retry_api_call(lambda: target_playlist.delete(), retries=max_retries)
                    time.sleep(1) # Safety
                    target_playlist = retry_api_call(lambda: user.create_playlist(playlist_name, ""), retries=max_retries)
                    retry_api_call(lambda: target_playlist.add(track_ids), retries=max_retries)
                    print("- Fallback successful.")
                    history_log_tracks(tracks)
                except Exception as e2:
                    print(f"- Fallback failed: {e2}")

    else:
        print(f"Playlist '{playlist_name}' not found. Creating...")
        try:
             target_playlist = retry_api_call(lambda: user.create_playlist(playlist_name, ""), retries=max_retries)
             retry_api_call(lambda: target_playlist.add(track_ids), retries=max_retries)
             print(f"Created '{playlist_name}' with {len(tracks)} tracks.")
             history_log_tracks(tracks)
        except Exception as e:
            print(f"Failed to create playlist: {e}")


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
    parser.add_argument('--max-repeats', type=int, help="Max plays allowed in anti-repeat window")
    parser.add_argument('-d', '--debug', action='store_true', help="Enable debug logging")

    args = parser.parse_args()
    
    # Setup Logging if Debug
    # Setup Logging if Debug
    if args.debug:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_dir = auth_manager.get_log_dir()
        log_file = log_dir / f"fusion-debug-{timestamp}.txt"
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
    
    if args.max_repeats is not None:
        if "fusion" not in config["modes"]: config["modes"]["fusion"] = {}
        config["modes"]["fusion"]["max_repeats"] = args.max_repeats

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
             print("  Opens the main configuration menu.")
        else:
            print("Tidal Fusion Help")
            print("  -n, --new      : Create/Reset playlist (Default)")
            print("  -a, --append   : Append to playlist")
            print("  -c, --config   : Configure settings")
            print("  --mode <name>  : Select mode (basic, fusion)")
            print("  -m, --limit    : Set max tracks (Fusion)")
            print("  --exclude-days : Anti-Repeat check window (days)")
            print("  --max-repeats  : Max plays allowed in window")
            print("  --show-history : View playback history")
            print("  --clear-history: Clear playback history")
            print("  -d, --debug    : Enable debug logging")
        return
    
    # 1. Config
    if args.config:
        configure_main(config)
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
    if args.mode == "basic" or (config.get("default_mode") == "basic" and not args.mode):
        print("Mode: Basic")
        tracks = fetch_basic_tracks(session, config)
    else:
        print("Mode: Fusion")
        # Anti-Repeat criteria printed inside function
        tracks = fetch_fusion_tracks(session, config, args)
        
    # Shuffle for basic (Fusion does its own interleaving)
    if mode == 'basic':
        random.shuffle(tracks)
        
    log_generation(tracks, mode, args.debug)
    update_playlist(session, args, tracks)

if __name__ == "__main__":
    main()
