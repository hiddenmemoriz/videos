import os
import requests
import json
import sys
import re

# ... (Constants remain the same) ...

def clean_title(artist, track):
    # Remove "- Topic" from artist name
    clean_artist = re.sub(r'\s*-\s*Topic\s*$', '', artist, flags=re.IGNORECASE).strip()
    return f"{clean_artist} - {track.strip()}"

def main():
    token = get_yt_token()
    if not token: sys.exit(1)

    # Get first item
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "snippet,contentDetails", 
        "playlistId": PLAYLIST_ID, 
        "maxResults": 1
    }
    r = requests.get(url, params=params, headers={"Authorization": f"Bearer {token}"}).json()
    
    items = r.get('items', [])
    if not items:
        print("📭 Playlist is empty.")
        sys.exit(0)

    item = items[0]
    vid_id = item['snippet']['resourceId']['videoId']
    
    # NEW: Fetch both Artist (Channel) and Track (Title)
    raw_artist = item['snippet'].get('videoOwnerChannelTitle', 'Unknown Artist')
    raw_track = item['snippet'].get('title', 'Unknown Track')
    
    final_title = clean_title(raw_artist, raw_track)

    if check_notion_entry(vid_id):
        print(f"⏩ {vid_id} already exists in Notion. Skipping.")
        sys.exit(0)

    metadata = {
        "video_id": vid_id,
        "playlist_item_id": item['id'],
        "title": final_title,
        "yt_url": f"https://www.youtube.com/watch?v={vid_id}"
    }
    
    with open("metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)
    
    print(f"📝 Metadata saved: {final_title}")

if __name__ == "__main__":
    main()
