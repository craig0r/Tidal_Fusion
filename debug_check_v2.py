
import tidalapi
import auth_manager
import sys

def debug():
    with open('debug_output.txt', 'w') as f:
        try:
            session = auth_manager.get_session()
            if not session:
                f.write("Login failed\n")
                return

            user = session.user
            f.write(f"User: {user.id}\n")

            f.write("\n--- Favorites Playlists ---\n")
            try:
                favs = user.favorites.playlists()
                for pl in favs:
                    f.write(f"Name: '{pl.name}', ID: {pl.id}\n")
            except Exception as e:
                f.write(f"Error fetching favorites: {e}\n")

            f.write("\n--- Created Playlists (user.playlists()) ---\n")
            if hasattr(user, 'playlists'):
                try:
                    # Note: user.playlists() usually returns the created playlists
                    created = user.playlists()
                    for pl in created:
                        f.write(f"Name: '{pl.name}', ID: {pl.id}\n")
                except Exception as e:
                    f.write(f"Error calling user.playlists(): {e}\n")
            else:
                f.write("user.playlists() method does NOT exist.\n")

        except Exception as e:
            f.write(f"CRITICAL ERROR: {e}\n")

if __name__ == "__main__":
    debug()
