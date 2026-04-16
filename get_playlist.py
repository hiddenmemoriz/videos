import os
from ytmusicapi import YTMusic, OAuthCredentials

def get_ytm_client():
    auth_keys = OAuthCredentials(
        client_id=os.environ.get("YTM_CLIENT_ID"),
        client_secret=os.environ.get("YTM_CLIENT_SECRET")
    )
    with open("oauth.json", "w") as f:
        f.write(os.environ.get("YTM_OAUTH_JSON"))
    return YTMusic("oauth.json", oauth_credentials=auth_keys)

def main():
    yt = get_ytm_client()
    playlist_id = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"
    
    # TEST 1: Authentication
    try:
        print(f"DEBUG 1: Logged in as: {yt.get_account_info()['name']}")
    except:
        print("DEBUG 1 FAILED: OAuth is invalid.")
        return

    # TEST 2: Read Access
    try:
        playlist = yt.get_playlist(playlist_id)
        print(f"DEBUG 2: SUCCESS. Found {len(playlist['tracks'])} tracks.")
    except:
        print("DEBUG 2 FAILED: Cannot see playlist.")
        return

    # TEST 3: Write Access (The likely failure)
    print("DEBUG 3: Testing REMOVE permission...")
    if playlist['tracks']:
        try:
            track = playlist['tracks'][0]
            # Try removing the first item to test permission
            res = yt.remove_playlist_items(playlist_id, [track])
            print(f"DEBUG 3: SUCCESS! Item removed: {res}")
        except Exception as e:
            print(f"DEBUG 3 FAILED: {e}")
            print("REASON: Your token is 'Read-Only'. You must re-login and CHECK THE BOX.")
