import os
import json
from ytmusicapi import YTMusic

def get_ytm_client():
    # 1. Grab the JSON from GitHub Secrets
    oauth_raw = os.environ.get("YTM_OAUTH_JSON")
    if not oauth_raw:
        raise ValueError("YTM_OAUTH_JSON secret is missing!")
    
    # 2. Write it to a temporary file
    with open("oauth.json", "w") as f:
        f.write(oauth_raw)

    try:
        # 3. For Main Accounts, simple initialization is usually best.
        # The library reads the 'oauth.json' to set the internal headers.
        return YTMusic("oauth.json")
    except Exception as e:
        print(f"Init Error: {e}")
        return None

def main():
    yt = get_ytm_client()
    if not yt: return

    # Your private playlist ID
    playlist_id = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"
    
    print(f"Accessing Main Account Playlist: {playlist_id}")
    try:
        # We fetch without 'limit=None' first to see if a standard request works
        playlist = yt.get_playlist(playlist_id)
        print(f"--- SUCCESS! Found: {playlist['title']} ---")
        
        for track in playlist['tracks']:
            print(f"ID: {track['videoId']} | {track['title']}")
            
    except Exception as e:
        print(f"Fetch Error: {e}")
        # If it still fails, the token might need more permissions
        print("Tip: Check Google Cloud Console -> APIs & Services -> Library -> YouTube Data API v3 is ENABLED.")

if __name__ == "__main__":
    main()
