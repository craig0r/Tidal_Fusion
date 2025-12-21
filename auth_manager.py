import json
import os
import pathlib
import platform
import sys
import webbrowser
import tidalapi

# Constants
TOKEN_FILE = pathlib.Path('tidal_tokens.json')

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
