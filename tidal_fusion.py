
import argparse
import json
import os
import pathlib
import platform
import random
import sys
import time
import webbrowser
import tidalapi

# Constants
TOKEN_FILE = pathlib.Path('tidal_tokens.json')
CONFIG_FILE = pathlib.Path('tidal_config.json')

MIX_NAMES_GENERATED = [f"My Mix {i}" for i in range(1, 9)]

DEFAULT_PLAYLIST_NAME = "Tidal Fusion"

# Configuration Keys
KEY_DAILY = "daily_discovery"
KEY_NEW = "new_arrivals"
KEY_MIXES = "my_mixes"

DEFAULT_CONFIG = {
    KEY_DAILY: True,
    KEY_NEW: True,
    KEY_MIXES: True
}

def load_config():
    """Load config from disk or return default."""
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config, using defaults: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save config to disk."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        print(f"Error saving config: {e}")

def configure_mixes(current_config):
    """Interactive menu to configure mixes."""
    config = current_config.copy()
    
    while True:
        print("\n--- Tidal Fusion Configuration ---")
        print("Select mixes to include:")
        print(f"1. [ {'x' if config.get(KEY_DAILY) else ' '} ] My Daily Discovery")
        print(f"2. [ {'x' if config.get(KEY_NEW) else ' '} ] My New Arrivals")
        print(f"3. [ {'x' if config.get(KEY_MIXES) else ' '} ] My Mixes (1-8)")
        print("4. Save and Exit")
        print("5. Cancel (Exit without saving)")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            config[KEY_DAILY] = not config.get(KEY_DAILY, True)
        elif choice == '2':
            config[KEY_NEW] = not config.get(KEY_NEW, True)
        elif choice == '3':
            config[KEY_MIXES] = not config.get(KEY_MIXES, True)
        elif choice == '4':
            save_config(config)
            return config
        elif choice == '5':
            print("Configuration cancelled.")
            sys.exit(0)
        else:
            print("Invalid choice, please try again.")

def save_tokens(session):
    """Save session tokens to a local file with secure permissions."""
    data = {
        'token_type': session.token_type,
        'access_token': session.access_token,
        'refresh_token': session.refresh_token,
        'expiry_time': session.expiry_time.timestamp() if session.expiry_time else None
    }
    
    with open(TOKEN_FILE, 'w') as f:
        json.dump(data, f)
    
    # Set file permissions to read/write only for owner on POSIX systems
    if platform.system() != 'Windows':
        try:
            os.chmod(TOKEN_FILE, 0o600)
        except Exception as e:
            print(f"Warning: Could not set secure file permissions: {e}", file=sys.stderr)
    
    print(f"Session saved to {TOKEN_FILE}")

def load_tokens(session):
    """Load session tokens from local file."""
    if not TOKEN_FILE.exists():
        return False
    
    try:
        with open(TOKEN_FILE, 'r') as f:
            data = json.load(f)
            
        # Check if we have the necessary fields
        if not all(k in data for k in ['token_type', 'access_token', 'refresh_token']):
            return False

        session.load_oauth_session(
            data['token_type'],
            data['access_token'],
            data['refresh_token'],
            data.get('expiry_time')
        )
        return True
    except Exception as e:
        print(f"Error loading tokens: {e}", file=sys.stderr)
        return False

def authenticate(args, session):
    """Handle authentication via file or new login."""
    if args.newlogin:
        print("Starting new login flow...")
        
        try:
            # Modern tidalapi
            login, future = session.login_oauth()
            uri = login.verification_uri_complete
            
            print(f"\nPlease visit this URL to authorize: {uri}")
            
            # Auto-open
            print("Attempting to open browser...")
            try:
                webbrowser.open(uri)
            except Exception as e:
                print(f"Could not open browser: {e}")
            
            print("Waiting for authorization...")
            future.result() # Wait for completion
            
            if session.check_login():
                print("Login successful!")
                save_tokens(session)
            else:
                print("Login failed.")
                sys.exit(1)
                
        except AttributeError:
            # Fallback
            print("Standard login_oauth() flow not found, trying login_oauth_simple()...")
            session.login_oauth_simple()
            if session.check_login():
                save_tokens(session)
            else:
                sys.exit(1)

    else:
        # Load existing tokens
        if load_tokens(session):
            if session.check_login():
                print(f"Loaded session for user: {session.user.id if hasattr(session, 'user') else 'Unknown'}")
            else:
                print("Session expired or invalid. Attempting refresh/login...")
                print("Please run with --newlogin to re-authenticate.")
                sys.exit(1)
        else:
            print("No saved session found. Please run with --newlogin")
            sys.exit(1)

def get_mix_tracks(session, config):
    """
    Search for mix playlists in Favorites and Mixes sections based on config.
    Returns a list of deduplicated Track objects.
    """
    found_tracks = {} # Map track_id -> track object (for deduplication)
    
    # Determine which names to look for
    target_names = []
    if config.get(KEY_DAILY, True):
        target_names.append("My Daily Discovery")
    if config.get(KEY_NEW, True):
        target_names.append("My New Arrivals")
    if config.get(KEY_MIXES, True):
        target_names.extend(MIX_NAMES_GENERATED)
        
    print(f"\nScanning for: {', '.join(target_names[:3])}{'...' if len(target_names) > 3 else ''}")

    # Helper to process a playlist/mix
    def process_container(container, source_type):
        name = getattr(container, 'title', getattr(container, 'name', ''))
        if name in target_names:
            print(f"Found '{name}' in {source_type}")
            try:
                # TidalAPI: .items() or .tracks() depending on object type
                # session.mixes() returns objects with .items()
                # user.favorites.playlists() returns objects with .tracks()
                
                # Try .tracks() first (Playlist)
                if hasattr(container, 'tracks') and callable(container.tracks):
                    items = container.tracks()
                # Then try .items() (Mix/generated)
                elif hasattr(container, 'items') and callable(container.items):
                    items = container.items()
                else:
                    items = []

                count = 0
                for track in items:
                    # Skip if it's not a track (sometimes videos etc)
                    if not hasattr(track, 'id'): 
                        continue
                        
                    if track.id not in found_tracks:
                        found_tracks[track.id] = track
                        count += 1
                print(f"  - Added {count} new tracks")
            except Exception as e:
                print(f"  - Error fetching tracks: {e}")

    # 1. Search in Favorites Playlists
    print("\nScanning user playlists...")
    try:
        user_playlists = session.user.favorites.playlists()
        for pl in user_playlists:
            process_container(pl, "Playlists")
    except Exception as e:
        print(f"Error accessing playlists: {e}")

    # 2. Search in Mixes (if available)
    print("Scanning Tidal Mixes...")
    try:
        if hasattr(session, 'mixes'):
            mixes = session.mixes()
            for mix in mixes:
                process_container(mix, "Mixes")
    except Exception as e:
        pass

    print(f"\nTotal uniques tracks found: {len(found_tracks)}")
    return list(found_tracks.values())

def update_playlist(session, args, tracks):
    """Create or update the target playlist."""
    if not tracks:
        print("No tracks to add. Exiting.")
        return

    target_name = args.playlistname or DEFAULT_PLAYLIST_NAME
    
    # Find existing playlist
    existing_playlist = None
    try:
        user_playlists = session.user.favorites.playlists()
        for pl in user_playlists:
            pl_name = getattr(pl, 'title', getattr(pl, 'name', None))
            if pl_name == target_name:
                existing_playlist = pl
                break
    except Exception as e:
        print(f"Error searching existing playlists: {e}")
    
    track_ids = [t.id for t in tracks]
    
    if args.new:
        print(f"Mode: --new. Recreating '{target_name}'...")
        if existing_playlist:
            try:
                existing_playlist.delete()
                print("Deleted existing playlist.")
            except Exception as e:
                print(f"Could not delete playlist: {e}")
        
        # Create new
        try:
            new_pl = session.user.create_playlist(target_name, "Generated by Tidal Fusion")
            new_pl.add(track_ids)
            print(f"Created '{target_name}' with {len(track_ids)} tracks.")
        except Exception as e:
            print(f"Error creating playlist: {e}")

    elif args.append:
        print(f"Mode: --append. Updating '{target_name}'...")
        if existing_playlist:
            # Append
            try:
                existing_playlist.add(track_ids)
                print(f"Appended {len(track_ids)} tracks to '{target_name}'.")
            except Exception as e:
                print(f"Error appending to playlist: {e}")
        else:
            # Create if missing
            try:
                new_pl = session.user.create_playlist(target_name, "Generated by Tidal Fusion")
                new_pl.add(track_ids)
                print(f"Playlist not found. Created '{target_name}' with {len(track_ids)} tracks.")
            except Exception as e:
                print(f"Error creating playlist: {e}")

def main():
    parser = argparse.ArgumentParser(description="Tidal Fusion Aggregator")
    parser.add_argument('-l', '--newlogin', action='store_true', help="Force new login")
    parser.add_argument('-n', '--new', action='store_true', help="Create new playlist (overwrite)")
    parser.add_argument('-a', '--append', action='store_true', help="Append to existing playlist")
    parser.add_argument('-c', '--config', action='store_true', help="Configure mix selection")
    parser.add_argument('--playlistname', type=str, help="Custom playlist name", default=DEFAULT_PLAYLIST_NAME)
    
    args = parser.parse_args()

    # Load Config
    config = load_config()

    # Handle Config Mode
    if args.config:
        config = configure_mixes(config)
        # We can continue or exit. Usually config matches imply just config.
        # But if they pass -c AND -n, maybe they want to config then run?
        # Let's assume yes.
    
    # Check if we have an action to perform
    if not (args.newlogin or args.new or args.append or args.config):
        parser.print_help()
        sys.exit(0)

    # Create Session
    session = tidalapi.Session()
    try:
        authenticate(args, session)
        
        # If we are just logging in or configuring without run flags, exit.
        if (args.newlogin or args.config) and not (args.new or args.append):
            print("Setup complete. Run with --new or --append to generate playlist.")
            return

        tracks = get_mix_tracks(session, config)
        
        # Shuffle
        random.shuffle(tracks)
        
        if args.new or args.append:
            update_playlist(session, args, tracks)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        # import traceback; traceback.print_exc()

if __name__ == "__main__":
    main()
