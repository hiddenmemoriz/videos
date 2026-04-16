import subprocess
import json

def get_ytm_playlist(url):
    # --flat-playlist: Don't resolve every video, just get the list (Fast)
    # --dump-single-json: Output everything as one JSON object
    command = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-single-json",
        url
    ]
    
    print(f"Fetching Unlisted Playlist...")
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return

    data = json.loads(result.stdout)
    
    print(f"\n--- {data.get('title', 'Playlist')} ---")
    
    # This extracts the ID and Title for each track
    for entry in data.get('entries', []):
        print(f"ID: {entry.get('id')} | Title: {entry.get('title')}")

if __name__ == "__main__":
    PLAYLIST_URL = "https://music.youtube.com/playlist?list=PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"
    get_ytm_playlist(PLAYLIST_URL)
