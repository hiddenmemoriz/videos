import os
import json
from ytmusicapi import YTMusic, OAuthCredentials

def get_ytm_client():
    # 1. Reconstruct secrets
    oauth_raw = os.environ.get("YTM_OAUTH_JSON")
    client_id = os.environ.get("YTM_CLIENT_ID")
    client_secret = os.environ.get("YTM_CLIENT_SECRET")
    
    with open("oauth.json", "w") as f:
        f.write(oauth_raw)

    # 2. Setup Credentials Object
    auth_keys = OAuthCredentials(
        client_id=client_id,
        client_secret=client_secret
    )

    # 3. Initialize
    # Try it first without brand_id; if it fails, add brand_id=...
    return YTMusic("oauth.json", oauth_credentials=auth_keys)

def main():
    yt = get_ytm_client()
    
    # Use the clean ID from your URL
    playlist_id = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"
    
    print(f"Checking access to private playlist...")
    try:
        # For private playlists, sometimes 'limit' helps the server process the request
        playlist = yt.get_playlist(playlist_id, limit=None)
        
        print(f"--- SUCCESS! Found Private Playlist: {playlist['title']} ---")
        
        for track in playlist['tracks']:
            # Log the IDs - useful for your FFmpeg/Reels automation
            print(f"ID: {track['videoId']} | Title: {track['title']}")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        print("Check if: 1. Your app is 'Published' in Google Cloud.")
        print("2. The Client ID is 'TVs and Limited Input devices'.")

if __name__ == "__main__":
    main()
