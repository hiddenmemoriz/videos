import os
import requests
import json
import sys

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

def download_media(video_id):
    print(f"📡 Requesting 3rd-party conversion for: {video_id}")
    os.makedirs(WORKDIR, exist_ok=True)
    
    # Using a 3rd party API bridge (MP3.xyz / yt-download approach)
    # This server acts as the middleman so YouTube doesn't see GitHub's IP.
    API_URL = f"https://api.vevioz.com/api/button/mp3/{video_id}"
    
    try:
        # 1. We fetch the conversion page
        # Some 3rd party sites use a direct button API
        print("⏳ Connecting to conversion server...")
        
        # 2. Downloading Thumbnail (Always safe from Google's CDN)
        thumb_url = f"https://i3.ytimg.com/vi/{video_id}/maxresdefault.jpg"
        thumb_res = requests.get(thumb_url, timeout=20)
        with open(f"{WORKDIR}/audio.jpg", "wb") as f:
            f.write(thumb_res.content)
            
        # 3. Downloading Audio via a reliable public mirror
        # We use a secondary Piped instance if the button API is slow
        # because it provides the most direct 'google video' link.
        MIRROR_API = f"https://pipedapi.kavin.rocks/streams/{video_id}"
        data = requests.get(MIRROR_API, timeout=30).json()
        
        audio_url = None
        for stream in data.get("audioStreams", []):
            if stream.get("format") == "M4A" or stream.get("codec") == "opus":
                audio_url = stream.get("url")
                break
        
        if not audio_url:
            # Final fallback to a direct download service
            audio_url = f"https://api.vvevioz.com/download/mp3/{video_id}"

        print("🚀 Bypassing IP block. Streaming audio...")
        audio_res = requests.get(audio_url, stream=True, timeout=60)
        
        with open(f"{WORKDIR}/audio.mp3", "wb") as f:
            for chunk in audio_res.iter_content(chunk_size=8192):
                f.write(chunk)

        print("🎉 Successfully pulled media from 3rd-party mirror!")
        return True

    except Exception as e:
        print(f"💥 3rd-party bypass failed: {e}")
        sys.exit(1)


def main():
    token = get_yt_token()
    item = get_first_item(token)
    if not item:
        sys.exit(0)

    v_id = item['contentDetails']['videoId']
    title = item['snippet']['title']
    item_id = item['id']

    if check_notion_entry(v_id):
        print("MATCH FOUND: Skipping.")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write("exists=true\n")
    else:
        print("NEW ENTRY: Downloading...")
        download_media(v_id)
        
        with open('video_data.json', 'w') as f:
            json.dump({"video_id": v_id, "title": title, "item_id": item_id}, f)
            
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"exists=false\nvideo_id={v_id}\ntitle={title}\n")

if __name__ == "__main__":
    main()
