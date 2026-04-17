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

def test_round_trip():
    # 1. Trigger the download
    print(f"📡 Step 1: Sending URL to PikPak...")
    send_cmd = subprocess.run(["rclone", "backend", "addurl", f"{REMOTE}:{FOLDER}", VIDEO_URL], capture_output=True, text=True)
    
    try:
        # We parse the initial receipt to get the Task ID
        task_data = json.loads(send_cmd.stdout)
        task_id = task_data.get("id")
        file_name = task_data.get("file_name")
        print(f"✅ Task created! ID: {task_id} | Target: {file_name}")
    except Exception as e:
        print(f"❌ Failed to parse task response: {send_cmd.stderr}")
        return False

    # 2. Polling Loop
    print("⏳ Step 2: Waiting for PikPak to finish download...")
    # Increase attempts to 40 (200 seconds total)
    for i in range(40):
        time.sleep(5)
        
        # Check status using the task ID
        status_cmd = subprocess.run(["rclone", "backend", "status", f"{REMOTE}:", task_id], capture_output=True, text=True)
        
        if not status_cmd.stdout.strip():
            print(f"   - [{i*5}s] Waiting for server response...")
            continue
            
        try:
            status_data = json.loads(status_cmd.stdout)
            phase = status_data.get("phase")
            # Log the phase so we can see progress (RUNNING, COLLECTING, etc)
            print(f"   - [{i*5}s] Status: {phase}")
            
            if phase == "PHASE_TYPE_COMPLETE":
                print("🎉 PikPak download finished!")
                break
            elif phase == "PHASE_TYPE_ERROR":
                print(f"❌ PikPak Error: {status_data.get('message')}")
                return False
        except:
            # If it's not JSON, it might be a raw string from rclone
            print(f"   - [{i*5}s] Raw update: {status_cmd.stdout.strip()}")
    else:
        print("⏰ Timeout waiting for PikPak.")
        return False

    # 3. Pull file to GitHub
    print(f"🚀 Step 3: Retrieving '{file_name}' to GitHub runner...")
    # Use 'copy' to bring the file from the cloud to the current folder
    subprocess.run(["rclone", "copy", f"{REMOTE}:{FOLDER}", "./", "--include", f"{file_name}"])
    
    if os.path.exists(file_name):
        size = os.path.getsize(file_name)
        print(f"✅ SUCCESS! File '{file_name}' retrieved. Size: {size/1024/1024:.2f} MB.")
        return True
    else:
        print(f"❌ Sync failed. Check if {file_name} exists in {FOLDER}")
        return False

if __name__ == "__main__":
    if not test_round_trip(): sys.exit(1)
