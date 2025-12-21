import tidalapi
import auth_manager
import sys

session = auth_manager.get_session()
if not session:
    print("No session loaded.")
    sys.exit(0)

print(f"Session loaded for user {session.user.id}")

# Try to fetch a recent track
try:
    favorites = session.user.favorites.tracks(limit=1)
    if not favorites:
        print("No favorites found.")
        sys.exit(0)
        
    track = favorites[0]
    print(f"Inspecting track: {track.name} ({track.id})")
    
    # Dump attributes
    print("Attributes:")
    for d in dir(track):
        if not d.startswith('_'):
            print(f"- {d}")
            
    # Check for audio features specifically
    if hasattr(track, 'audio_features'):
        print(f"Has .audio_features: {track.audio_features}")
    elif hasattr(session, 'get_audio_features'):
        print("Session has .get_audio_features")
    else:
        print("No obvious audio_features found.")

except Exception as e:
    print(f"Error: {e}")
