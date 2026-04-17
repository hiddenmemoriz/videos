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

def run_rclone(args):
    result = subprocess.run(["rclone"] + args, capture_output=True, text=True)
    return result

def test_round_trip():
    # 1. Trigger the download
    print(f"📡 Step 1: Sending URL to PikPak...")
    send_cmd = run_rclone(["backend", "addurl", f"{REMOTE}:{FOLDER}", VIDEO_URL])
    
    try:
        task_data = json.loads(send_cmd.stdout)
        task_id = task_data.get("id")
        file_name = task_data.get("file_name")
        print(f"✅ Task created! ID: {task_id} | Target: {file_name}")
    except:
        print(f"❌ Failed to parse task response: {send_cmd.stderr}")
        return False

    # 2. Polling Loop (Wait for completion)
    print("⏳ Step 2: Waiting for PikPak to finish download...")
    for i in range(20): # Max 100 seconds (20 x 5s)
        time.sleep(5)
        # Check task status
        status_cmd = run_rclone(["backend", "status", f"{REMOTE}:", task_id])
        status_data = json.loads(status_cmd.stdout)
        
        phase = status_data.get("phase")
        print(f"   - Status: {phase} ({i*5}s elapsed)")
        
        if phase == "PHASE_TYPE_COMPLETE":
            print("🎉 PikPak download finished!")
            break
        elif phase == "PHASE_TYPE_ERROR":
            print("❌ PikPak encountered an error.")
            return False
    else:
        print("⏰ Timeout waiting for PikPak.")
        return False

    # 3. Pull file to GitHub
    print(f"🚀 Step 3: Retrieving '{file_name}' to GitHub runner...")
    # We use copyto to ensure it lands exactly where we want locally
    pull_cmd = run_rclone(["copyto", f"{REMOTE}:{FOLDER}{file_name}", f"./{file_name}"])
    
    if os.path.exists(file_name):
        size = os.path.getsize(file_name)
        print(f"✅ SUCCESS! File '{file_name}' retrieved. Size: {size} bytes.")
        return True
    else:
        print("❌ File sync failed.")
        return False

if __name__ == "__main__":
    if not test_round_trip(): sys.exit(1)
