import os
import requests
import json
import sys
import re
 
# --- CONFIGURATION (Environment Variables) ---
NOTION_DB_ID = os.environ.get('NOTION_DB_ID')
NOTION_PAGE_ID = os.environ.get('NOTION_PAGE_ID')
YT_PLAYLIST_ID = os.environ.get('YT_PLAYLIST_ID')
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')

# --- CLEAN FUNCTION ---
def clean_name(text):
    text = text or ""

    # Remove YouTube noise
    text = re.sub(r'\s*[-–—]\s*Topic\s*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^Release\s*[-–—]?\s*', '', text, flags=re.IGNORECASE)

    # Remove invalid filename characters
    text = re.sub(r'[\\/*?:"<>|]', '', text)

    # 🚨 FIX: remove leading dots (prevents hidden files)
    text = re.sub(r'^\.+', '', text)

    return text.strip()


# --- YOUTUBE AUTH ---
def get_yt_token():
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
        res.raise_for_status()
        return res.json().get('access_token')
    except Exception as e:
        print(f"❌ YouTube Auth Error: {e}")
        return None


# --- DELETE PLAYLIST ITEM ---
def delete_playlist_item(token, playlist_item_id):
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"id": playlist_item_id}
    
    print(f"🗑️ Deleting playlist item: {playlist_item_id}...")
    try:
        response = requests.delete(url, headers=headers, params=params)
        if response.status_code == 204:
            print("✅ Deleted from playlist")
        else:
            print(f"⚠️ Delete failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Delete error: {e}")


# --- CHECK NOTION ---
def check_notion_entry(video_id):
    if not NOTION_DB_ID or not NOTION_PAGE_ID or not NOTION_TOKEN:
        print("❌ Missing Notion config")
        return False

    url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    payload = {
        "filter": {
            "and": [
                {"property": "Video ID", "rich_text": {"equals": video_id.strip()}},
                {"property": "Type", "select": {"equals": "Video"}},
                {"property": "Channel", "relation": {"contains": NOTION_PAGE_ID}}
            ]
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        res_data = response.json()
        return len(res_data.get("results", [])) > 0
    except Exception as e:
        print(f"⚠️ Notion check failed: {e}")
        return False


# --- MAIN ---
def main():
    if not YT_PLAYLIST_ID:
        print("❌ Missing playlist ID")
        sys.exit(1)

    token = get_yt_token()
    if not token:
        sys.exit(1)

    # Fetch playlist items
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "snippet,contentDetails",
        "playlistId": YT_PLAYLIST_ID,
        "maxResults": 2
    }

    r = requests.get(url, params=params, headers={"Authorization": f"Bearer {token}"}).json()
    items = r.get('items', [])

    if not items:
        print("❌ Playlist empty")
        sys.exit(1)

    # Active item
    active_item = items[0]
    playlist_item_id = active_item.get('id')
    vid_id = active_item['contentDetails']['videoId']

    # Check Notion
    if check_notion_entry(vid_id):
        print(f"🚩 Duplicate found: {vid_id}")
        delete_playlist_item(token, playlist_item_id)
        sys.exit(1)

    # Prefetch next
    prefetch_urls = []
    if len(items) > 1:
        next_vid_id = items[1]['contentDetails']['videoId']
        prefetch_urls.append(f"https://www.youtube.com/watch?v={next_vid_id}")
        print(f"⚡ Prefetch queued: {next_vid_id}")

    # --- FIXED NAME HANDLING ---
    raw_artist = active_item['snippet'].get('videoOwnerChannelTitle', '')
    raw_track = active_item['snippet'].get('title', '')

    artist = clean_name(raw_artist) or "Unknown"
    track = clean_name(raw_track) or "Track"

    # Metadata
    metadata = {
        "title": f"{artist} - {track}",
        "artist": artist,
        "track": track,
        "video_id": vid_id,
        "playlist_item_id": playlist_item_id,
        "yt_url": f"https://www.youtube.com/watch?v={vid_id}",
        "prefetch_urls": prefetch_urls
    }

    with open("metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)

    print("-" * 40)
    print(f"✅ READY: {artist} - {track}")
    print(f"🚀 Prefetch: {'Yes' if prefetch_urls else 'No'}")
    print("-" * 40)


if __name__ == "__main__":
    main()
