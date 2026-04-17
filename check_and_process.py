import os
import requests
import json
import sys
from urllib.parse import urlencode

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

def download_thumbnail(video_id):
    """Download thumbnail with multiple quality fallbacks"""
    print("📸 Downloading Thumbnail...")
    thumbnail_urls = [
        f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{video_id}/sddefault.jpg",
        f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
    ]
    
    for thumb_url in thumbnail_urls:
        try:
            res = requests.get(thumb_url, timeout=10)
            if res.status_code == 200:
                with open(f"{WORKDIR}/audio.jpg", "wb") as f:
                    f.write(res.content)
                print(f"✅ Thumbnail saved from {thumb_url}")
                return True
        except Exception as e:
            print(f"⚠️ Thumbnail URL {thumb_url} failed: {e}")
    
    print("⚠️ Could not download thumbnail")
    return False

def download_with_pytube(video_id):
    """Download using pytube (pure Python, no external tools needed)"""
    print("🔗 Attempting pytube download...")
    try:
        from pytube import YouTube
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        yt = YouTube(url, use_oauth=False, allow_oauth_cache=False)
        
        # Get highest quality audio stream
        audio_stream = yt.streams.filter(only_audio=True).first()
        
        if audio_stream is None:
            print("❌ No audio stream found with pytube")
            return False
        
        print(f"⏳ Downloading audio (bitrate: {audio_stream.abr})...")
        audio_stream.download(output_path=WORKDIR, filename="audio.mp3")
        
        # Verify file exists
        if os.path.exists(f"{WORKDIR}/audio.mp3"):
            size_mb = os.path.getsize(f"{WORKDIR}/audio.mp3") / (1024*1024)
            print(f"✅ Downloaded {size_mb:.2f} MB")
            return True
        else:
            print("❌ File was not saved properly")
            return False
            
    except ImportError:
        print("⚠️ pytube not installed. Skipping...")
        return False
    except Exception as e:
        print(f"⚠️ pytube failed: {e}")
        return False

def download_with_direct_api(video_id):
    """Download using direct YouTube Data API with fallback"""
    print("🔗 Attempting direct YouTube fetch...")
    try:
        # This uses a public API endpoint that sometimes works
        url = f"https://www.youtube.com/api/timedtext"
        params = {
            "v": video_id,
            "kind": "asr",
            "lang": "en"
        }
        
        # Actually, let's try the simpler approach: nitter/invidious with better parsing
        return False  # Skip this method for now
        
    except Exception as e:
        print(f"⚠️ Direct API failed: {e}")
        return False

def download_with_invidious_v2(video_id):
    """Improved Invidious download with better format handling"""
    print("📡 Attempting improved Invidious proxy...")
    
    instances = [
        "https://invidious.snopyta.org",
        "https://y.com.sb",
        "https://invidious.sethforprivacy.com",
        "https://iv.nboeck.de",
        "https://invidio.us",
        "https://invidious.xyz"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for base_url in instances:
        try:
            print(f"🔗 Trying instance: {base_url}")
            
            # Try to get video info
            api_url = f"{base_url}/api/v1/videos/{video_id}"
            print(f"   Fetching: {api_url}")
            
            data = requests.get(api_url, timeout=15, headers=headers).json()
            
            # Check if we got valid data
            if "error" in data or not data.get("formatStreams"):
                print(f"   ❌ No valid data in response")
                continue
            
            # Try formatStreams first (these are usually more reliable)
            print(f"   Found {len(data.get('formatStreams', []))} format streams")
            
            for fmt in data.get("formatStreams", []):
                if fmt.get("url"):
                    print(f"   ⏳ Downloading from formatStreams...")
                    res = requests.get(fmt["url"], stream=True, timeout=60, headers=headers)
                    res.raise_for_status()
                    
                    with open(f"{WORKDIR}/audio.mp3", "wb") as f:
                        downloaded = 0
                        for chunk in res.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                        size_mb = downloaded / (1024*1024)
                        print(f"   ✅ Downloaded {size_mb:.2f} MB")
                    return True
            
            # Fallback: try adaptiveFormats for audio
            print(f"   Found {len(data.get('adaptiveFormats', []))} adaptive formats")
            
            best_audio = None
            for fmt in data.get("adaptiveFormats", []):
                fmt_type = fmt.get("type", "")
                if "audio" in fmt_type:
                    if best_audio is None or fmt.get("bitrate", 0) > best_audio.get("bitrate", 0):
                        best_audio = fmt
            
            if best_audio and best_audio.get("url"):
                print(f"   ⏳ Downloading from adaptiveFormats...")
                res = requests.get(best_audio["url"], stream=True, timeout=60, headers=headers)
                res.raise_for_status()
                
                with open(f"{WORKDIR}/audio.mp3", "wb") as f:
                    downloaded = 0
                    for chunk in res.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                    size_mb = downloaded / (1024*1024)
                    print(f"   ✅ Downloaded {size_mb:.2f} MB")
                return True
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️ Timeout")
            continue
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Connection error")
            continue
        except json.JSONDecodeError:
            print(f"   📄 Invalid JSON response (instance may be down)")
            continue
        except Exception as e:
            print(f"   ⚠️ Error: {str(e)}")
            continue
    
    return False

def download_media(video_id):
    """Download media with multiple fallback methods"""
    print(f"📡 Downloading media for {video_id}...")
    os.makedirs(WORKDIR, exist_ok=True)
    
    # Method 1: Try pytube first (pure Python, most reliable if it works)
    if download_with_pytube(video_id):
        download_thumbnail(video_id)
        return True
    
    # Method 2: Improved Invidious with better format handling
    if download_with_invidious_v2(video_id):
        download_thumbnail(video_id)
        return True
    
    # If all methods fail
    print("❌ All download methods failed")
    print("\nDebug Info:")
    print("   - yt-dlp: Not installed or blocked")
    print("   - pytube: Not installed or failed")
    print("   - Invidious: All instances failed or blocked")
    print("\nTroubleshooting:")
    print("   1. Try installing pytube: pip install pytube")
    print("   2. Try installing yt-dlp: pip install yt-dlp")
    print("   3. Check if your IP is blocked by YouTube")
    print("   4. Try running from a different network")
    
    return False


def main():
    token = get_yt_token()
    item = get_first_item(token)
    if not item:
        print("No items in playlist")
        sys.exit(0)

    v_id = item['contentDetails']['videoId']
    title = item['snippet']['title']
    item_id = item['id']

    print(f"Video: {title} ({v_id})")

    if check_notion_entry(v_id):
        print("MATCH FOUND: Skipping.")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write("exists=true\n")
    else:
        print("NEW ENTRY: Downloading...")
        success = download_media(v_id)
        
        if success:
            with open('video_data.json', 'w') as f:
                json.dump({"video_id": v_id, "title": title, "item_id": item_id}, f)
                
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"exists=false\nvideo_id={v_id}\ntitle={title}\n")
            print("✅ Success!")
        else:
            print("❌ Failed to download media")
            sys.exit(1)

if __name__ == "__main__":
    main()
