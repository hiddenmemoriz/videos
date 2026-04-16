import os
import requests
import json
import sys

# --- CONFIGURATION ---
PLAYLIST_ID = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"
TARGET_VIDEO_ID = sys.argv[1] if len(sys.argv) > 1 else "-oIMyMEvMLI"
API_KEY = "AIzaSyC9XL3ZjWddXya6X74dJoCTL-WEYFDNX30" # <--- ENSURE THIS IS YOUR KEY FROM BROWSER

def get_fresh_access_token():
    try:
        oauth_data = json.loads(os.environ['YTM_OAUTH_JSON'])
        url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": os.environ['YTM_CLIENT_ID'],
            "client_secret": os.environ['YTM_CLIENT_SECRET'],
            "refresh_token": oauth_data['refresh_token'],
            "grant_type": "refresh_token"
        }
        r = requests.post(url, data=payload)
        return r.json().get('access_token')
    except Exception as e:
        print(f"Token Refresh Error: {e}")
        return None

def find_set_video_id(data, target_vid):
    """Recursively search the entire JSON for the videoId and return its setVideoId."""
    if isinstance(data, dict):
        if data.get('videoId') == target_vid and 'setVideoId' in data:
            return data['setVideoId']
        for v in data.values():
            result = find_set_video_id(v, target_vid)
            if result: return result
    elif isinstance(data, list):
        for item in data:
            result = find_set_video_id(item, target_vid)
            if result: return result
    return None

def remove_track():
    token = get_fresh_access_token()
    if not token: return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    context = {"context": {"client": {"clientName": "WEB_REMIX", "clientVersion": "1.20240410.01.00"}}}

    # STEP 1: Find the setVideoId
    print(f"Searching for track {TARGET_VIDEO_ID}...")
    browse_url = f"https://music.youtube.com/youtubei/v1/browse?key={API_KEY}"
    
    # Use the 'VL' prefix for playlist IDs in the raw API
    clean_playlist_id = PLAYLIST_ID if PLAYLIST_ID.startswith("VL") else f"VL{PLAYLIST_ID}"
    
    r = requests.post(browse_url, json={**context, "browseId": clean_playlist_id}, headers=headers)
    
    if r.status_code != 200:
        print(f"Browse failed: {r.status_code} - {r.text}")
        return

    # Deep Search for the ID
    set_video_id = find_set_video_id(r.json(), TARGET_VIDEO_ID)

    if not set_video_id:
        print("Track not found. If the list is empty or private, check your Scopes.")
        return

    # STEP 2: Execute Removal
    print(f"Found setVideoId: {set_video_id}. Removing...")
    edit_url = f"https://music.youtube.com/youtubei/v1/browse/edit_playlist?key={API_KEY}"
    edit_payload = {
        **context,
        "playlistId": PLAYLIST_ID.replace("VL", ""), # Removal usually wants the ID without VL
        "actions": [{"action": "ACTION_REMOVE_VIDEO", "setVideoId": set_video_id}]
    }
    
    final_res = requests.post(edit_url, json=edit_payload, headers=headers)
    print(f"Done. Status: {final_res.status_code}")
    if "ACTIONS_SUCCESS" in final_res.text:
        print("Successfully removed!")

if __name__ == "__main__":
    remove_track()
