import requests
import json
import time

def test_cobalt_download(youtube_url):
    # Use a common Cobalt instance API endpoint
    # Note: Public instances can change; you may need to find a fresh one at cobalt.tools
    API_URL = "https://cobalt.tools/api/json" 
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": youtube_url,
        "downloadMode": "audio", # "audio" for mp3, "v" for video
        "audioFormat": "mp3",
        "audioBitrate": "192",
        "filenameStyle": "basic"
    }

    print(f"📡 Sending request to Cobalt for: {youtube_url}")
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        result = response.json()

        if response.status_code == 200 and result.get("status") == "stream":
            download_url = result.get("url")
            print(f"✅ Success! Download link found: {download_url}")
            
            # Download the actual file
            print("⏳ Downloading file...")
            file_data = requests.get(download_url)
            with open("test_audio.mp3", "wb") as f:
                f.write(file_data.content)
            print("🎉 Saved as 'test_audio.mp3'")
            return True
        else:
            print(f"❌ Cobalt Error: {result.get('text', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"💥 Request failed: {e}")
        return False

if __name__ == "__main__":
    # Test with a known phonk track
    test_cobalt_download("https://www.youtube.com/watch?v=tdocUW4aKnY")
