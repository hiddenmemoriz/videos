import os
import requests
import json
import sys
import yt_dlp

# Constants
NOTION_DB_ID = "31fb4e9c9ef68068b8edc379332d974f" 
PHONKSTAX_PAGE_ID = "320b4e9c9ef680f3afaaee8b0450203a"
WORKDIR = "/tmp/reels_phonkstax"

def get_yt_token():
    url = "https://oauth2.googleapis.com/token"
    oauth_data = json.loads(os.environ['YTM_OAUTH_JSON'])
    payload = {
        "client_id": os.environ['YTM_CLIENT_ID'],
        "client_secret": os.environ['YTM_CLIENT_SECRET'],
        "refresh_token": oauth_data['refresh_token'],
        "grant_type": "refresh_token"
    }
    return requests.post(url, data=payload).json().get('access_token')

def get_first_item(token):
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {"part": "snippet,contentDetails", "playlistId": "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur", "maxResults": 1}
    r = requests.get(url, params=params, headers={"Authorization": f"Bearer {token}"}).json()
    return r.get('items', [])[0] if r.get('items') else None

def check_notion_entry(video_id):
    url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
    payload = {
        "filter": {
            "and": [
                {"property": "Video ID", "rich_text": {"equals": video_id.strip()}},
                {"property": "Type", "select": {"equals": "Reel"}},
                {"property": "Channel", "relation": {"contains": PHONKSTAX_PAGE_ID}}
            ]
        }
    }
    headers = {"Authorization": f"Bearer {os.environ['NOTION_TOKEN']}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
    res = requests.post(url, json=payload, headers=headers).json()
    return len(res.get("results", [])) > 0

def download_media(video_id, token):
    print(f"📡 Requesting Cobalt bridge for {video_id}...")
    os.makedirs(WORKDIR, exist_ok=True)
    
    # Public Cobalt instance API
    API_URL = "https://cobalt.tools/api/json" 
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": youtube_url,
        "downloadMode": "audio",
        "audioFormat": "mp3",
        "audioBitrate": "192"
    }

    try:
        # 1. Get the download link from Cobalt
        response = requests.post(API_URL, json=payload, headers=headers)
        result = response.json()

        if response.status_code == 200 and result.get("status") in ["stream", "redirect", "tunnel"]:
            download_url = result.get("url")
            print(f"✅ Bridge opened: {download_url}")
            
            # 2. Download the MP3
            print("⏳ Downloading MP3...")
            audio_data = requests.get(download_url, stream=True)
            with open(f"{WORKDIR}/audio.mp3", "wb") as f:
                for chunk in audio_data.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 3. Get the high-res Thumbnail (since Cobalt is primarily audio/video)
            # We use the standard YouTube i3.ytimg link which is rarely IP blocked
            print("🖼️ Fetching Thumbnail...")
            thumb_url = f"https://i3.ytimg.com/vi/{video_id}/maxresdefault.jpg"
            thumb_data = requests.get(thumb_url)
            with open(f"{WORKDIR}/audio.jpg", "wb") as f:
                f.write(thumb_data.content)
                
            print("🎉 Media download complete.")
            return True
        else:
            print(f"❌ Cobalt Error: {result.get('text', 'Unknown error')}")
            sys.exit(1)

    except Exception as e:
        print(f"💥 Cobalt Request failed: {e}")
        sys.exit(1)

def main():
    token = get_yt_token()
    item = get_first_item(token)
    if not item:
        print("Playlist empty.")
        sys.exit(0)

    v_id = item['contentDetails']['videoId']
    title = item['snippet']['title']
    item_id = item['id']

    print(f"Checking Item: {title} ({v_id})")
    print(f"Playlist Item ID: {item_id}")

    if check_notion_entry(v_id):
        print("MATCH FOUND: Skipping render.")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write("exists=true\n")
    else:
        print("NEW ENTRY: Starting download...")
        download_media(v_id, token)
        
        with open('video_data.json', 'w') as f:
            json.dump({"video_id": v_id, "title": title, "item_id": item_id}, f)
            
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"exists=false\nvideo_id={v_id}\ntitle={title}\n")

if __name__ == "__main__":
    main()
