import os
import json
from ytmusicapi import YTMusic, OAuthCredentials

def get_ytm_client():
    oauth_raw = os.environ.get("YTM_OAUTH_JSON")
    client_id = os.environ.get("YTM_CLIENT_ID")
    client_secret = os.environ.get("YTM_CLIENT_SECRET")
    
    with open("oauth.json", "w") as f:
        f.write(oauth_raw)

    auth_keys = OAuthCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    return YTMusic("oauth.json", oauth_credentials=auth_keys)

def main():
    yt = get_ytm_client()
    
    playlist_id = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"
    target_video_id = "-oIMyMEvMLI" # From your URL

    print(f"Finding track in playlist...")
    try:
        playlist = yt.get_playlist(playlist_id)
        
        # Find the track object to get the 'setVideoId'
        track_to_remove = next(
            (t for t in playlist['tracks'] if t['videoId'] == target_video_id), 
            None
        )

        if track_to_remove:
            print(f"Found: {track_to_remove['title']}. Removing...")
            # remove_playlist_items requires the playlistId and a list of track objects
            response = yt.remove_playlist_items(playlist_id, [track_to_remove])
            print(f"Server Response: {response}")
        else:
            print("Track not found in this playlist.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
