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
DEFAULT_PLAYLIST_NAME = "Tidal Fusion"
MIX_NAMES_GENERATED = [f"My Mix {i}" for i in range(1, 9)]

TIDAL_COMPLIANCE_HEADER = (
    "----------------------------------------------------------------------\n"
    "Data provided by TIDAL. https://www.tidal.com\n"
    "This application is not endorsed by TIDAL or any TIDAL Artist.\n"
    "----------------------------------------------------------------------"
)

# --- Logger ---
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

def setup_logging():
    """Setup TeeLogger to capture all output."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_dir = auth_manager.get_log_dir()
    log_file = log_dir / f"fusion-log-{timestamp}.txt"
    
    # Preserve original stdout/stderr just in case, though we act as a tee
    # sys.stdout = TeeLogger(log_file)
    # We want to capture everything from now on.
    try:
        tee = TeeLogger(log_file)
        sys.stdout = tee
        # sys.stderr = tee # Optional: capture errors too? Yes, good for debugging.
        
        print(f"Logging initialized: {log_file}")
        print(TIDAL_COMPLIANCE_HEADER)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return log_file
    except Exception as e:
        print(f"Failed to setup logging: {e}")
        return None

# --- Configuration ---

def load_config():
    """Load configuration from database via auth_manager."""
    config = auth_manager.get_config()
    
    # Default Config Structure if empty or legacy
    if not config:
        config = {
            "exclude_days": 7,
            "max_repeats": 3,
            "max_retries": 3,
            "limit_type": "time",
            "limit_value": 180
        }
        # Save defaults immediately
        auth_manager.save_config(config)
    
    # Migration/Normalization: If "modes" exists (Legacy), flatten it
    if "modes" in config:
        print("Migrating legacy configuration...")
        fusion_conf = config["modes"].get("fusion", {})
        
        if "exclude_days" not in config:
             config["exclude_days"] = fusion_conf.get("exclude_days", 7)
        if "max_repeats" not in config:
             config["max_repeats"] = fusion_conf.get("max_repeats", 3)
        if "limit_type" not in config:
             config["limit_type"] = fusion_conf.get("limit_type", "time")
        if "limit_value" not in config:
             config["limit_value"] = fusion_conf.get("limit_value", 180)
             
        del config["modes"]
        if "default_mode" in config:
            del config["default_mode"]
            
        auth_manager.save_config(config)
        
    return config

def save_config(config):
    """Save configuration to database via auth_manager."""
    auth_manager.save_config(config)
    print("Configuration saved.")

def configure_advanced_settings(config):
    """Interactive menu for Advanced / Fusion Settings."""
    while True:
        curr_days = config.get('exclude_days', 7)
        curr_repeats = config.get('max_repeats', 3)
        curr_limit_type = config.get('limit_type', 'time')
        curr_limit_val = config.get('limit_value', 180 if curr_limit_type == 'time' else 150)
        curr_retries = config.get('max_retries', 3)
        
        print("\n--- Advanced Settings ---")
        print(f"1. Set 'Exclude Days' (Anti-Repeat Window) [Current: {curr_days}]")
        print(f"2. Set 'Max Repeats' (Max plays in window) [Current: {curr_repeats}]")
        print(f"3. Set Limit Type (Time/Count) [Current: {curr_limit_type}]")
        print(f"4. Set Limit Value (Mins or Tracks) [Current: {curr_limit_val}]")
        print(f"5. Set Max API Retries [Current: {curr_retries}]")
        print("6. Back")
        
        choice = input("Enter choice: ").strip()
        if choice == '1':
            val = input(f"Enter days to exclude (0 to disable) [{curr_days}]: ").strip()
            if val:
                try:
                    config['exclude_days'] = int(val)
                except ValueError: print("Invalid number.")
        elif choice == '2':
            val = input(f"Enter max repeats allowed (e.g. 3) [{curr_repeats}]: ").strip()
            if val:
                try:
                    config['max_repeats'] = int(val)
                except ValueError: print("Invalid number.")
        elif choice == '3':
            val = input(f"Enter type (time/count) [{curr_limit_type}]: ").strip().lower()
            if val in ['time', 'count']:
                config['limit_type'] = val
                config['limit_value'] = 180 if val == 'time' else 150
            else:
                print("Invalid type.")
        elif choice == '4':
            val = input(f"Enter value ({'minutes' if curr_limit_type=='time' else 'tracks'}) [{curr_limit_val}]: ").strip()
            if val:
                try:
                   config['limit_value'] = int(val)
                except ValueError: print("Invalid number.")
        elif choice == '5':
            val = input(f"Enter max retries: ").strip()
            if val:
                try:
                    config['max_retries'] = int(val)
                except ValueError: print("Invalid number.")
        elif choice == '6':
            return

def configure_main(config):
    """Main Configuration Menu Entry Point."""
    while True:
        print("\n--- Tidal Fusion Configuration ---")
        print(TIDAL_COMPLIANCE_HEADER)
        print("1. Advanced Settings")
        print("2. Run Authentication")
        print("3. Clear Authentication Data (Manual)")
        print("4. Save and Exit")
        print("5. Exit without Saving")
        
        choice = input("Enter choice: ").strip()
        
        if choice == '1':
            configure_advanced_settings(config)
        elif choice == '2':
            auth_manager.login()
        elif choice == '3':
            print("Please delete 'fusion.db' or tokens manually for now.")
        elif choice == '4':
            save_config(config)
            return
        elif choice == '5':
            return
        
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
            
            # Get Source
            source = getattr(t, 'fusion_source_mix', 'Unknown')
            
            c.execute('''
                INSERT INTO history (track_id, track_name, artist_name, timestamp, bpm, style, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(t.id),
                getattr(t, 'name', 'Unknown'),
                artist_name,
                now.isoformat(),
                getattr(t, 'bpm', None),
                None, # Style not available
                source
            ))
            count += 1
        except Exception as e:
            # duplicate entries or db errors
            pass
            
    conn.commit()
    conn.close()
    if count > 0:
        print(f"Logged {count} tracks to history.")

def history_show(limit=20):
    """Print table of recent history."""
    conn = auth_manager.get_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT track_name, artist_name, timestamp, source FROM history ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        
        print(f"\nLast {limit} Tracks Generated:")
        print(f"{'Timestamp':<16} | {'Artist':<25} | {'Track':<30} | {'Source':<20}")
        print("-" * 100)
        for r in rows:
            ts_str = r[2]
            try:
                ts_display = str(ts_str)[:16].replace('T', ' ')
            except:
                ts_display = str(ts_str)[:16]
            
            source = r[3] if len(r) > 3 and r[3] else "Unknown"
            
            print(f"{ts_display:<16} | {r[1][:23]:<25} | {r[0][:28]:<30} | {source:<20}")
    except Exception as e:
        print(f"Error reading history: {e}")
    finally:
        conn.close()
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
        return {}
    finally:
        conn.close()

def db_get_yesterday_context():
    """
    Get tracks included in the last 30 hours.
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
    """Search for a mix/playlist by partial name."""
    # 1. Check Favorites
    try:
        for pl in session.user.favorites.playlists():
            if name_substr.lower() in pl.name.lower():
                return pl
    except:
        pass
    # 2. Check Mixes
    try:
        if hasattr(session, 'mixes'):
            mixes = session.mixes()
            for mix in mixes:
                title = getattr(mix, 'title', getattr(mix, 'name', ''))
                if title and name_substr.lower() in title.lower():
                    return mix
    except Exception as e:
        print(f"  - Error checking mixes: {e}")
    return None

def fetch_discovery_tracks(session):
    """Fetch tracks from discovery sources (Adventure pool)."""
    tracks = []
    found_ids = set()
    
    # Discovery Sources
    targets = ["My Daily Discovery", "My New Arrivals"] + MIX_NAMES_GENERATED
    
    print(f"Fetching discovery/adventure tracks from {len(targets)} sources...")
    
    for name in targets:
        try:
            mix = get_mix_by_name(session, name)
            if mix:
                items = []
                if hasattr(mix, 'tracks') and callable(mix.tracks):
                    items = mix.tracks()
                elif hasattr(mix, 'items') and callable(mix.items):
                    items = mix.items()
                
                count = 0
                for t in items:
                    if not hasattr(t, 'id'): continue
                    if t.id not in found_ids:
                        t.fusion_source_pool = "Adventure"
                        t.fusion_source_mix = name # Preserve specific mix name
                        tracks.append(t)
                        found_ids.add(t.id)
                        count += 1
                if count > 0:
                    print(f"  - Added {count} tracks from '{name}'")
        except Exception as e:
            print(f"  - Error scanning '{name}': {e}")
            
    return tracks

import re

def deduplicate_remasters(tracks):
    """Deduplicate remasters. Returns filtered list."""
    if not tracks: return []
    
    remaster_regex = re.compile(r"[\(\[\-]\s*(?:(\d{4})?\s*)?(?:Digital|Digitally|24-Bit|20\d\d)?\s*Remaster(?:ed)?\s*(?:(\d{4})?)[\)\]]?", re.IGNORECASE)
    
    groups = {}
    
    for t in tracks:
        title = getattr(t, 'name', '')
        artist = "Unknown"
        if getattr(t, 'artist', None): artist = t.artist.name
        elif getattr(t, 'artists', None): artist = t.artists[0].name
        
        match = remaster_regex.search(title)
        base_title = title
        year_score = 0
        is_remaster = False
        
        if match:
            base_title = remaster_regex.sub("", title).strip()
            is_remaster = True
            y1, y2 = match.groups()
            if y1: year_score = int(y1)
            elif y2: year_score = int(y2)
            else: year_score = 1
            
        key = (artist.lower(), base_title.lower())
        
        if key not in groups: groups[key] = []
        groups[key].append({
            'track': t,
            'is_remaster': is_remaster,
            'year': year_score,
            'title': title
        })
        
    final_list = []
    removed_count = 0
    
    for key, candidates in groups.items():
        if len(candidates) == 1:
            final_list.append(candidates[0]['track'])
            continue
            
        candidates.sort(key=lambda x: (x['is_remaster'], x['year']), reverse=True)
        winner = candidates[0]
        final_list.append(winner['track'])
        removed_count += (len(candidates) - 1)

    if removed_count > 0:
        print(f"- Remaster Dedup: Removed {removed_count} older/duplicate versions.")
        
    return final_list

def fetch_and_generate_playlist(session, config, args):
    """
    Main Fusion Generation Pipeline.
    """
    # --- 1. Limit / Duration Logic ---
    limit_type = config.get("limit_type", "time")
    limit_val = config.get("limit_value", 180)
    
    # CLI Overrides
    if args.limit: 
         limit_type = "count"
         limit_val = args.limit
         
    if limit_type == "time":
        limit = int((limit_val * 60) / 210) # Approx
        print(f"Fusion: Targeting {limit_val}m (~{limit} tracks)...")
    else:
        limit = limit_val
        print(f"Fusion: Targeting {limit} tracks...")

    # --- 2. Pipeline Data Fetching ---
    print("- Fetching Context Data (History/Exclusions)...")
    history_stats = db_get_history_stats(30)
    yesterday_ctx = db_get_yesterday_context()
    recent_plays = db_get_recent_plays(24)
    
    # --- 3. Candidate Fetching ---
    # --- 3. Candidate Fetching ---
    print("- Fetching Tracks...")
    
    # Favorites (Base for Comfort/Habit)
    favorites_map = {}
    try:
        favs = session.user.favorites.tracks()
        print(f"  - Found {len(favs)} Favorites")
        for t in favs:
            favorites_map[t.id] = t
    except Exception as e:
        print(f"- Error fetching Favorites: {e}")

    # Discovery (Adventure) - From Mixes
    adventure_candidates = fetch_discovery_tracks(session)
    
    # Deduplicate Adventure: Remove if in Favorites (Definition of Adventure = New/Discovery)
    final_adventure = []
    skipped_fav = 0
    for t in adventure_candidates:
        if t.id not in favorites_map:
            final_adventure.append(t)
        else:
            skipped_fav += 1
    
    print(f"  - Adventure: {len(final_adventure)} tracks (excluded {skipped_fav} already in favorites)")

    # Partition Favorites into Comfort vs Habit
    # Comfort: > 6 months old
    # Habit: <= 6 months old (Recent Favorites)
    
    comfort_candidates = []
    habit_candidates = []
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=180) # 6 months
    
    for t in favorites_map.values():
        val = getattr(t, 'user_date_added', None) or getattr(t, 'date_added', None)
        
        # Date Parsing
        added = None
        if val:
            if isinstance(val, datetime):
                added = val
            elif isinstance(val, str):
                try: 
                    added = datetime.fromisoformat(val.replace('Z', '+00:00'))
                except: 
                    pass
        
        is_habit = False # Default to Comfort if no date
        if added:
             if added.tzinfo is None:
                 added = added.replace(tzinfo=timezone.utc)
             if added > cutoff_date:
                 is_habit = True
        
        if is_habit:
            t.fusion_source_pool = "Habit"
            t.fusion_source_mix = "Recent Favorites"
            habit_candidates.append(t)
        else:
            t.fusion_source_pool = "Comfort"
            t.fusion_source_mix = "Favorites"
            comfort_candidates.append(t)
            
    print(f"  - Comfort (Fav > 6mo): {len(comfort_candidates)}")
    print(f"  - Habit (Fav < 6mo): {len(habit_candidates)}")

    # Deduplicate Remasters for each pool
    comfort_candidates = deduplicate_remasters(comfort_candidates)
    habit_candidates = deduplicate_remasters(habit_candidates)
    final_adventure = deduplicate_remasters(final_adventure)
    
    # --- 4. Exclusion & Scoring ---
    
    def filter_candidates(pool, pool_name):
        valid = []
        excluded_rpt = 0
        excluded_freq = 0
        
        for t in pool:
            tid = str(t.id)
            
            # 1. Global Exclude Days (Default 7)
            if tid in history_stats:
                last_inc = history_stats[tid]['last_included']
                if (datetime.now(timezone.utc) - last_inc).days < config.get("exclude_days", 7):
                    excluded_rpt += 1
                    continue
            
            # 2. Freq Cap: Max 8 times in 30 days
            stats = history_stats.get(tid, {'count': 0})
            if stats['count'] > 8:
                excluded_freq += 1
                continue
                
            # 3. Soft/Hard Conflict (Yesterday Context)
            if tid in yesterday_ctx:
                excluded_rpt += 1
                continue
                
            valid.append(t)
        
        # log details
        # print(f"  - {pool_name} details: {len(valid)} valid, {excluded_rpt} recent, {excluded_freq} freq")
        return valid

    print("- Filtering Candidates (Exclusions)...")
    comfort_valid = filter_candidates(comfort_candidates, "Comfort")
    habit_valid = filter_candidates(habit_candidates, "Habit")
    adventure_valid = filter_candidates(final_adventure, "Adventure")
    
    print(f"  - Valid Pools: Comfort={len(comfort_valid)}, Habit={len(habit_valid)}, Adventure={len(adventure_valid)}")

    # --- 5. Selection (40/30/30) ---
    final_selection = []
    
    target_total = limit
    target_comfort = int(target_total * 0.40)
    target_habit = int(target_total * 0.30)
    target_adventure = int(target_total * 0.30)
    
    # Adjust rounding
    diff = target_total - (target_comfort + target_habit + target_adventure)
    target_comfort += diff 
    
    print(f"- Selection Targets: Comfort={target_comfort}, Habit={target_habit}, Adventure={target_adventure}")

    # A. Select Comfort
    random.shuffle(comfort_valid)
    selected_comfort = comfort_valid[:target_comfort]
    
    # B. Select Habit
    random.shuffle(habit_valid)
    selected_habit = habit_valid[:target_habit]
    
    # C. Select Adventure
    # Logic: "My New Arrivals" max 1/7 total
    max_new_arrivals = int(target_total // 7)
    
    adv_new_arrivals = [t for t in adventure_valid if "My New Arrivals" in getattr(t, 'fusion_source_mix', '')]
    adv_others = [t for t in adventure_valid if "My New Arrivals" not in getattr(t, 'fusion_source_mix', '')]
    
    random.shuffle(adv_new_arrivals)
    selected_adv_new = adv_new_arrivals[:max_new_arrivals]
    
    rem_adv_slots = target_adventure - len(selected_adv_new) # e.g. 15 - 7 = 8
    
    random.shuffle(adv_others)
    if rem_adv_slots > 0:
        selected_adv_others = adv_others[:rem_adv_slots]
    else:
        selected_adv_others = []
    
    selected_adventure = selected_adv_new + selected_adv_others
    
    # D. Backfill
    current_selected = selected_comfort + selected_habit + selected_adventure
    if len(current_selected) < target_total:
        needed = target_total - len(current_selected)
        print(f"  - Underflow: need {needed} more. Backfilling...")
        
        used_ids = {t.id for t in current_selected}
        remaining = []
        for t in (comfort_valid + habit_valid + adventure_valid):
            if t.id not in used_ids:
                remaining.append(t)
        random.shuffle(remaining)
        current_selected.extend(remaining[:needed])
        
    final_selection = current_selected

    # --- 6. Mirror-Image Rotation ---
    total_slots = len(final_selection)
    result_array = [None] * total_slots
    report_inverted = 0
    
    pending_placement = []
    
    for t in final_selection:
        tid = str(t.id)
        if tid in yesterday_ctx:
            old_idx = yesterday_ctx[tid]
            new_idx = (total_slots - 1) - old_idx
            new_idx = max(0, min(total_slots - 1, new_idx))
            
            if result_array[new_idx] is None:
                result_array[new_idx] = t
                report_inverted += 1
            else:
                pending_placement.append(t)
        else:
            pending_placement.append(t)

    random.shuffle(pending_placement)
    for i in range(total_slots):
        if result_array[i] is None and pending_placement:
            result_array[i] = pending_placement.pop(0)

    final_list = [t for t in result_array if t is not None]
    print(f"- Rotation Report: Inverted {report_inverted} track positions.")

    # --- 7. Vibe Check (Skip for now to keep simple/fast) ---
    
    # --- 8. Time Enforcement ---
    if limit_type == "time":
        target_sec = limit_val * 60
        tolerance = 180
        current_dur = sum(getattr(t, 'duration', 0) for t in final_list)
        
        while current_dur < (target_sec - tolerance) and pool_fresh:
             t = pool_fresh.pop(0)
             final_list.append(t)
             current_dur += getattr(t, 'duration', 0)
             
        while current_dur > (target_sec + tolerance) and len(final_list) > 1:
             rem = final_list.pop()
             current_dur -= getattr(rem, 'duration', 0)
             
        print(f"- Final Duration: {int(current_dur/60)}m {int(current_dur%60)}s")

    # --- 9. Final Logging & DB ---
    db_record_inclusion(final_list)
    print(f"Generation Complete: {len(final_list)} tracks.")
    
    return final_list

def log_generation_result(tracks):
    """Log to console + file (handled by Tee)."""
    print("\n" + "="*40)
    print(f"GENERATION DETAILS ({datetime.now().strftime('%H:%M:%S')})")
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
        src_mix = getattr(track, 'fusion_source_mix', 'Unknown')
        
        print(f"{i}. {artist_name} - {title} [BPM: {bpm}]")
        print(f"   Source: {src_mix}")
        # print(f"   ID: {track.id}")
        print("")


# --- Playlist Management ---

def retry_api_call(func, retries=3, delay=2, backoff=2):
    """Retry a function call."""
    for i in range(retries + 1):
        try:
            return func()
        except Exception as e:
            if i == retries:
                print(f"  - API Error: {e}. Given up.")
                raise e
            sleep_time = delay * (backoff ** i)
            print(f"  - API Error: {e}. Retrying in {sleep_time}s...")
            time.sleep(sleep_time)

def update_playlist(session, args, tracks):
    """Update user playlist."""
    if not tracks:
        print("No tracks generated.")
        return

    track_ids = [t.id for t in tracks]
    config = load_config()
    max_retries = config.get("max_retries", 3)
    user = session.user
    playlist_name = DEFAULT_PLAYLIST_NAME
    
    print(f"Updating Playlist: '{playlist_name}'...")
    target_playlist = None
    
    try:
        for pl in user.playlists():
            if pl.name == playlist_name:
                target_playlist = pl
                break
        if not target_playlist:
            for pl in user.favorites.playlists():
                if pl.name == playlist_name:
                    target_playlist = pl
                    break
    except Exception as e:
        print(f"Error searching playlists: {e}")
        return

    if target_playlist:
        if args.append:
             print(f"Appending {len(tracks)} tracks...")
             try:
                 retry_api_call(lambda: target_playlist.add(track_ids), retries=max_retries)
                 print("- Tracks added.")
                 history_log_tracks(tracks)
             except Exception:
                 print("- Failed to append tracks.")
        else:
            print(f"Resetting playlist...")
            try:
                # Optimized Clear
                try:
                    retry_api_call(lambda: target_playlist.clear(), retries=max_retries)
                except:
                    # Fallback delete/recreate
                    target_playlist.delete()
                    time.sleep(1)
                    target_playlist = user.create_playlist(playlist_name, "")
                
                retry_api_call(lambda: target_playlist.add(track_ids), retries=max_retries)
                print("- Playlist updated.")
                history_log_tracks(tracks)
                
            except Exception as e:
                print(f"Failed to reset playlist: {e}")
    else:
        print(f"Creating new playlist '{playlist_name}'...")
        try:
             target_playlist = retry_api_call(lambda: user.create_playlist(playlist_name, ""), retries=max_retries)
             retry_api_call(lambda: target_playlist.add(track_ids), retries=max_retries)
             print(f"- Created with {len(tracks)} tracks.")
             history_log_tracks(tracks)
        except Exception as e:
            print(f"Failed to create playlist: {e}")

# --- Main ---

def main():
    auth_manager.init_db()
    
    # 1. Setup Logging (Immediate)
    log_file = setup_logging()
    
    parser = argparse.ArgumentParser(description="Tidal Fusion", add_help=False)
    
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('-n', '--new', action='store_true', help="Overwrite playlist (Default)")
    mode_group.add_argument('-a', '--append', action='store_true', help="Append to playlist")
    mode_group.add_argument('-c', '--config', action='store_true', help="Configure settings")
    
    mode_group.add_argument('--show-history', nargs='?', const=20, type=int, metavar='N', help="Show history")
    mode_group.add_argument('--clear-history', action='store_true', help="Clear history")

    parser.add_argument('-h', '--help', action='store_true', help="Show help")
    
    # Config Overrides
    parser.add_argument('-m', '--limit', type=int, help="Track limit override")
    parser.add_argument('--exclude-days', type=int, help="Override exclude days")
    
    # Note: --debug, --mode REMOVED
    
    args = parser.parse_args()
    config = load_config()

    # Apply overrides
    if args.exclude_days is not None: config["exclude_days"] = args.exclude_days
    
    if args.help:
        print("Tidal Fusion Help")
        print("  -n, --new      : Create/Reset playlist (Default)")
        print("  -a, --append   : Append to playlist")
        print("  -c, --config   : Configure settings")
        print("  -m, --limit    : Set max tracks limit")
        print("  --show-history : View playback history")
        return

    # Handle Actions
    if args.config:
        configure_main(config)
        return
        
    if args.show_history is not None:
        history_show(args.show_history)
        return
        
    if args.clear_history:
        history_clear()
        return

    # Default: Run Generation
    session = auth_manager.get_session()
    if not session:
        print("Please run 'tidal-fusion -c' and select 'Run Authentication' first.")
        return

    tracks = fetch_and_generate_playlist(session, config, args)
    
    log_generation_result(tracks)
    update_playlist(session, args, tracks)

if __name__ == "__main__":
    main()
