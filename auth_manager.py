import json
import os
import pathlib
from pathlib import Path
import platform
import sys
import webbrowser
import sqlite3
import tidalapi
from datetime import datetime

# Constants
def get_config_dir():
    """Returns the configuration directory based on OS."""
    if platform.system() == 'Windows':
        base = os.environ.get('APPDATA', os.path.expanduser('~\\AppData\\Roaming'))
        path = pathlib.Path(base) / 'TidalFusion'
    else:
        # XDG Standard or fallback to ~/.config
        base = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
        path = pathlib.Path(base) / 'tidal_fusion'
    
# Configuration Paths
if platform.system() == "Windows":
    CONFIG_DIR = Path(os.environ["APPDATA"]) / "TidalFusion"
    LOG_DIR = Path(os.environ["ProgramData"]) / "TidalFusion"
else:
    CONFIG_DIR = Path.home() / ".config" / "tidal_fusion"
    LOG_DIR = Path("/var/log/tidal_fusion")

# Ensure Config Dir Exists
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Helper to check write access for logging
def get_log_dir():
    """Return LOG_DIR if writable, else fallback to CONFIG_DIR."""
    try:
        if not LOG_DIR.exists():
            # managed by install script, but try creating if user owns /var/log/
            LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Test write access
        test_file = LOG_DIR / ".test_write"
        test_file.touch()
        test_file.unlink()
        return LOG_DIR
    except Exception:
        # Fallback to user config dir if permission denied
        return CONFIG_DIR

DB_FILE = CONFIG_DIR / 'fusion.db'
LEGACY_TOKEN_FILE = CONFIG_DIR / 'tidal_tokens.json'
LEGACY_CONFIG_FILE = CONFIG_DIR / 'tidal_config.json'

def get_connection():
    """Get a connection to the SQLite database."""
    return sqlite3.connect(DB_FILE)

def init_db():
    """Initialize the database schema."""
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Tokens Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            token_type TEXT,
            access_token TEXT,
            refresh_token TEXT,
            expiry_time REAL
        )
    ''')
    
    # 2. Config Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # 3. History Table (Legacy/General)
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id TEXT,
            track_name TEXT,
            artist_name TEXT,
            timestamp DATETIME,
            bpm INTEGER,
            style TEXT
        )
    ''')

    # 4. Playback History (Actual User Plays) - V2
    c.execute('''
        CREATE TABLE IF NOT EXISTS playback_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id TEXT,
            played_at DATETIME
        )
    ''')

    # 5. Inclusion History (Generated Playlist Content/Position) - V2
    c.execute('''
        CREATE TABLE IF NOT EXISTS inclusion_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id TEXT,
            included_at DATETIME,
            position_index INTEGER,
            source_mix TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Run Migration
    migrate_legacy_files()

def migrate_legacy_files():
    """Import legacy JSON files into DB and rename them to .bak."""
    conn = get_connection()
    c = conn.cursor()
    
    # Migrate Tokens
    if LEGACY_TOKEN_FILE.exists():
        try:
            print("Migrating legacy tokens to database...")
            with open(LEGACY_TOKEN_FILE, 'r') as f:
                data = json.load(f)
            
            c.execute('''
                INSERT OR REPLACE INTO tokens (id, token_type, access_token, refresh_token, expiry_time)
                VALUES (1, ?, ?, ?, ?)
            ''', (data.get('token_type'), data.get('access_token'), data.get('refresh_token'), data.get('expiry_time')))
            
            os.rename(LEGACY_TOKEN_FILE, LEGACY_TOKEN_FILE.with_suffix('.json.bak'))
            print("- Tokens migrated and file renamed.")
        except Exception as e:
            print(f"- Token migration failed: {e}")

    # Migrate Config
    if LEGACY_CONFIG_FILE.exists():
        try:
            print("Migrating legacy config to database...")
            with open(LEGACY_CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
            
            # Flatten or store as JSON blob? 
            # Storing entire JSON blob under 'main_config' key for simplicity and compatibility
            # Or flattening? The request said "table called config". Key-Value makes sense.
            # But the config structure is nested (modes -> basic -> ...).
            # Storing the whole JSON string under a single key 'app_config' is safest for now to avoid rewriting all access logic immediately.
            # However, "move tidal_config.json into a table... called config".
            # I will store the whole JSON string for the 'app_config' key.
            
            c.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', 
                      ('app_config', json.dumps(config_data)))
            
            os.rename(LEGACY_CONFIG_FILE, LEGACY_CONFIG_FILE.with_suffix('.json.bak'))
            print("- Config migrated and file renamed.")
        except Exception as e:
            print(f"- Config migration failed: {e}")

    conn.commit()
    conn.close()

def save_tokens(session):
    """Save session tokens to DB."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO tokens (id, token_type, access_token, refresh_token, expiry_time)
        VALUES (1, ?, ?, ?, ?)
    ''', (session.token_type, session.access_token, session.refresh_token, 
          session.expiry_time.timestamp() if session.expiry_time else None))
    conn.commit()
    conn.close()
    print("Session saved to database.")

def load_tokens(session):
    """Load session tokens from DB."""
    ensure_db_ready()
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT token_type, access_token, refresh_token, expiry_time FROM tokens WHERE id = 1')
    row = c.fetchone()
    conn.close()
    
    if not row:
        return False
        
    try:
        session.load_oauth_session(
            row[0], # token_type
            row[1], # access_token
            row[2], # refresh_token
            row[3]  # expiry_time
        )
        return True
    except Exception as e:
        print(f"Error loading tokens from DB: {e}", file=sys.stderr)
        return False

# Config Helpers
def get_config():
    """Load the full config object from DB."""
    ensure_db_ready()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE key = 'app_config'")
    row = c.fetchone()
    conn.close()
    
    if row:
        try:
            return json.loads(row[0])
        except:
            return {}
    return {}

def save_config(config_data):
    """Save the full config object to DB."""
    ensure_db_ready()
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', 
              ('app_config', json.dumps(config_data)))
    conn.commit()
    conn.close()

def ensure_db_ready():
    """Check if DB exists, if not init."""
    if not DB_FILE.exists():
        init_db()

def login(session=None):
    """
    Perform a new interactive login. 
    If session is provided, use it; otherwise create a new one.
    Returns the authenticated session or raises/exits on failure.
    """
    if session is None:
        session = tidalapi.Session()

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
            return session
        else:
            print("Login failed.")
            sys.exit(1)
            
    except AttributeError:
        # Fallback
        print("Standard login_oauth() flow not found, trying login_oauth_simple()...")
        session.login_oauth_simple()
        if session.check_login():
            save_tokens(session)
            return session
        else:
            sys.exit(1)

def get_session():
    """
    Attempt to load an existing session. 
    Returns a valid session object if successful, None otherwise.
    """
    session = tidalapi.Session()
    if load_tokens(session):
        if session.check_login():
            print(f"Loaded session for user: {session.user.id if hasattr(session, 'user') else 'Unknown'}")
            return session
        else:
            print("Session expired or invalid.")
            return None
    else:
        return None
