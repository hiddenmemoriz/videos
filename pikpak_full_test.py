import subprocess
import time
import json
import sys
import os

# --- CONFIG ---
REMOTE = "mypikpak"
FOLDER = "/R97group/phonkstax/reels/"
VIDEO_URL = "https://www.youtube.com/watch?v=tdocUW4aKnY"
# --------------

def run_command(args):
    return subprocess.run(args, capture_output=True, text=True)

def test_round_trip():
    # 1. Trigger the download
    print(f"📡 Step 1: Sending URL to PikPak...")
    send_cmd = run_command(["rclone", "backend", "addurl", f"{REMOTE}:{FOLDER}", VIDEO_URL])
    
    try:
        task_data = json.loads(send_cmd.stdout)
        file_name = task_data.get("file_name")
        print(f"✅ Task created! Target file: {file_name}")
    except:
        print(f"❌ Failed to trigger PikPak. Check your login.")
        return False

    # 2. Polling the Folder (Wait for the file to appear)
    print(f"⏳ Step 2: Watching folder {FOLDER} for {file_name}...")
    # 60 attempts * 10 seconds = 10 minutes max
    for i in range(60):
        # We list the folder and check if our file_name is in the list
        list_cmd = run_command(["rclone", "lsf", f"{REMOTE}:{FOLDER}"])
        
        if file_name in list_cmd.stdout:
            # Check if the file size is greater than 0 (PikPak creates it at 0 then fills it)
            size_cmd = run_command(["rclone", "lsjson", f"{REMOTE}:{FOLDER}{file_name}"])
            try:
                size_data = json.loads(size_cmd.stdout)[0]
                if size_data.get("Size", 0) > 1000: # Over 1KB means it's likely done
                    print(f"🎉 File detected! Size: {size_data.get('Size')} bytes.")
                    break
            except:
                pass
        
        print(f"   - [{i*10}s] Still waiting for file to finish cloud transfer...")
        time.sleep(10)
    else:
        print("⏰ Timeout: File never appeared in the folder.")
        return False

    # 3. Pull file to GitHub
    print(f"🚀 Step 3: Downloading '{file_name}' to GitHub runner...")
    run_command(["rclone", "copyto", f"{REMOTE}:{FOLDER}{file_name}", f"./{file_name}"])
    
    if os.path.exists(file_name):
        size = os.path.getsize(file_name)
        print(f"✅ SUCCESS! Final local size: {size/1024/1024:.2f} MB")
        return True
    else:
        print("❌ Download failed.")
        return False

if __name__ == "__main__":
    if not test_round_trip(): sys.exit(1)
