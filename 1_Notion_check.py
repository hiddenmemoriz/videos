import os
import requests
import json
import sys
import re

# Constants
NOTION_DB_ID = "31fb4e9c9ef68068b8edc379332d974f" 
NOTION_PAGE_ID = "320b4e9c9ef680f3afaaee8b0450203a"
PLAYLIST_ID = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"

def get_yt_token():
    """Refreshes the YouTube OAuth2 token."""
    url = "https://oauth2.googleapis.com/token"
    try:
        oauth_data = json.loads(os.environ['YTM_OAUTH_JSON'])
        payload = {
            "client_id": os.environ['YTM_CLIENT_ID'],
            "client_secret": os.environ['YTM_CLIENT_SECRET'],
            "refresh_token": oauth_data['refresh_token'],
            "grant_type": "refresh_token"
        }
        res = requests.post(url, data=payload)
        return res.json().get('access_token')
    except Exception as e:
        print(f"❌ OAuth Refresh Failed: {e}")
        return None

def check_notion_entry(video_id):
    """Checks if the video already exists in the Notion DB."""
    url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
    payload = {
        "filter": {
            "and": [
                {"property": "Video ID", "rich_text": {"equals": video_id.strip()}},
                {"property": "Type", "select": {"equals": "Reel"}},
                {"property": "Channel", "relation": {"contains": NOTION_PAGE_ID}}
            ]
        }
    }
    headers = {
        "Authorization": f"Bearer {os.environ['NOTION_TOKEN']}", 
        "Notion-Version": "2022-06-28", 
        "Content-Type": "application/json"
    }
    res = requests.post(url, json=payload, headers=headers).json()
    return len(res.get("results", [])) > 0

def clean_title(artist, track):
    """Removes 'Topic' and formats as 'Artist - Track'."""
    # Remove " - Topic" from the artist name
    clean_artist = re.sub(r'\s*-\s*Topic\s*$', '', artist, flags=re.IGNORECASE).strip()
    return f"{clean_artist} - {track.strip()}"

def main():
    token = get_yt_token()
    if not token:
        print("❌ Could not generate YouTube Access Token.")
        sys.exit(1)

    # Fetch first playlist item
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
    
    # Logic to get Artist and Track name separately
    raw_artist = item['snippet'].get('videoOwnerChannelTitle', 'Unknown Artist')
    raw_track = item['snippet'].get('title', 'Unknown Track')
    
    final_title = clean_title(raw_artist, raw_track)

    if check_notion_entry(vid_id):
        print(f"⏩ {vid_id} ({final_title}) already exists in Notion. Skipping.")
        sys.exit(0)

    # Prepare metadata for Step 2
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
