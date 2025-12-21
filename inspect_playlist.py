import tidalapi
import auth_manager
import sys

session = auth_manager.get_session()
if not session:
    print("No session loaded.")
    sys.exit(0)

print(f"Session loaded for user {session.user.id}")

try:
    # Get a playlist (first one or create dummy)
    playlists = session.user.favorites.playlists()
    if not playlists:
        print("No playlists found to inspect.")
        sys.exit(0)
    
    pl = playlists[0]
    print(f"Inspecting Playlist: {pl.name} (type: {type(pl)})")
    
    print("Methods/Attributes:")
    for d in dir(pl):
        if not d.startswith('_'):
            print(f"- {d}")
            
except Exception as e:
    print(f"Error: {e}")
