import os
import json
import subprocess
import re

def smart_cleanup():
    # 1. Load metadata to get the Title/Artist
    if not os.path.exists("metadata.json"):
        print("⚠️ metadata.json missing. Cleanup skipped.")
        return

    with open("metadata.json", "r") as f:
        meta = json.load(f)

    # We extract Title and Artist to create multiple search patterns
    track_title = meta.get('track', '')
    video_id = meta.get('video_id', '')
    
    remote_name = "mypikpak"
    remote_path = "Download/temp/"

    # 2. Build a list of patterns to match
    # We want to match the Track Title (e.g., AGUANTA) and the Video ID
    patterns = []
    if track_title:
        # Clean title of special characters that might break rclone
        clean_title = re.sub(r'[^\w\s]', '', track_title)
        patterns.append(f"*{clean_title}*")
    if video_id:
        patterns.append(f"*{video_id}*")

    if not patterns:
        print("⚠️ No patterns found to match. Cleanup skipped.")
        return

    print(f"🔎 Searching for files matching: {patterns}")

    # 3. Use rclone to delete specific matches only
    for pattern in patterns:
        cmd = [
            "rclone", "delete", f"{remote_name}:{remote_path}",
            "--include", pattern
        ]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        if res.returncode == 0:
            print(f"🗑️ Purged files matching: {pattern}")
        else:
            print(f"❌ Error matching {pattern}: {res.stderr.strip()}")

if __name__ == "__main__":
    smart_cleanup()
