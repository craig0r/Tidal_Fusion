
import tidalapi
import auth_manager

def debug():
    session = auth_manager.get_session()
    if not session:
        print("Login failed")
        return

    user = session.user
    print(f"User: {user.id}")

    print("\n--- Favorites Playlists ---")
    favs = user.favorites.playlists()
    for pl in favs:
        print(f"Name: '{pl.name}', ID: {pl.id}")
        if pl.name == "Tidal Fusion":
            print("  -> FOUND in Favorites")

    print("\n--- Created Playlists (if method exists) ---")
    if hasattr(user, 'playlists'):
        try:
            created = user.playlists()
            for pl in created:
                print(f"Name: '{pl.name}', ID: {pl.id}")
                if pl.name == "Tidal Fusion":
                    print("  -> FOUND in Created")
        except Exception as e:
            print(f"Error calling user.playlists(): {e}")
    else:
        print("user.playlists() method does NOT exist.")

if __name__ == "__main__":
    debug()
