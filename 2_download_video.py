import subprocess
import time
import json
import os
import sys
import glob

# --- CONFIG ---
REMOTE = "mypikpak"
REMOTE_PATH = "/Download/temp/"
LOCAL_DIR = "./assets/download/"
# Folders to wipe for a fresh start
CLEAN_PATHS = [
    "./assets/download/", 
    "./assets/audio/", 
    "./assets/image/", 
    "./assets/trim_audio/"
]

def run_cmd(args):
    """Helper to run shell commands and capture output."""
    return subprocess.run(args, capture_output=True, text=True)

def download():
    # 1. Load Metadata from Step 1
    if not os.path.exists("metadata.json"):
        print("❌ Error: metadata.json not found. Did Step 1 fail?")
        sys.exit(1)
        
    with open("metadata.json", "r") as f:
        meta = json.load(f)
    
    VIDEO_URL = meta['yt_url']
    VIDEO_ID = meta['video_id']
    PREFETCH_LIST = meta.get('prefetch_urls', [])

    # 2. Cleanup local asset folders
    print("🧹 Cleaning local asset folders...")
    for folder in CLEAN_PATHS:
        os.makedirs(folder, exist_ok=True)
        for f in glob.glob(os.path.join(folder, "*")):
            try: os.remove(f)
            except: pass

    # 3. SCAN CLOUD & SMART DISPATCH (Avoid Redundant Tasks)
    print("📡 Scanning Cloud storage to manage tasks...")
    cloud_ls_res = run_cmd(["rclone", "lsf", f"{REMOTE}:{REMOTE_PATH}"])
    cloud_files = cloud_ls_res.stdout

    # A. Handle Pre-fetch (Warm-up)
    if PREFETCH_LIST:
        print(f"⚡ Checking warm-up queue for {len(PREFETCH_LIST)} items...")
        for url in PREFETCH_LIST:
            # Extract Video ID to see if it's already in the cloud
            p_vid_id = url.split("v=")[-1].split("&")[0]
            if p_vid_id in cloud_files:
                print(f"  > Skipping: {p_vid_id} already exists/processing in Cloud.")
            else:
                run_cmd(["rclone", "backend", "addurl", f"{REMOTE}:{REMOTE_PATH}", url])
                print(f"  > Dispatched NEW warm-up: {p_vid_id}")

    # B. Identify or Dispatch Active Video
    file_name = None
    for line in cloud_files.splitlines():
        if VIDEO_ID in line:
            file_name = line
            print(f"⏩ Instant Hit! Found active file in Cloud: {file_name}")
            break

    if not file_name:
        print(f"🆕 Active Video {VIDEO_ID} not in cloud. Dispatching request...")
        send_res = run_cmd(["rclone", "backend", "addurl", f"{REMOTE}:{REMOTE_PATH}", VIDEO_URL])
        try:
            task_data = json.loads(send_res.stdout)
            file_name = task_data.get("file_name")
            print(f"✅ Target Locked: {file_name}")
        except:
            # Fallback if PikPak returns task info without filename immediately
            print("⚠️ Task dispatched, waiting for filename to appear...")
            time.sleep(5)
            retry_ls = run_cmd(["rclone", "lsf", f"{REMOTE}:{REMOTE_PATH}"])
            for line in retry_ls.stdout.splitlines():
                if VIDEO_ID in line:
                    file_name = line
                    break

    if not file_name:
        print("❌ Error: Could not determine filename for active task.")
        sys.exit(1)

    # 4. Polling Loop
    print(f"⏳ Waiting for Cloud Muxing to complete...")
    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    # Wait up to 10 minutes (120 * 5s)
    for i in range(120):
        symbol = spinner[i % len(spinner)]
        # Re-check the cloud for the file
        list_cmd = run_cmd(["rclone", "lsf", f"{REMOTE}:{REMOTE_PATH}"])
        
        if file_name in list_cmd.stdout:
            # Check if file size is > 1KB (ensures stitching is done)
            size_cmd = run_cmd(["rclone", "lsjson", f"{REMOTE}:{REMOTE_PATH}{file_name}"])
            try:
                size_data = json.loads(size_cmd.stdout)[0]
                if size_data.get("Size", 0) > 1000:
                    print(f"\n✨ FILE READY! Size: {size_data['Size']/1024/1024:.2f} MB")
                    break
            except: pass
            print(f"\r{symbol} [{i*5}s] File detected, cloud is still stitching...", end="")
        else:
            print(f"\r{symbol} [{i*5}s] PikPak is still fetching from YouTube...", end="")
        
        sys.stdout.flush()
        time.sleep(5)
    else:
        print("\n⏰ Timeout: PikPak took too long to process.")
        sys.exit(1)

    # 5. Pull to Runner
    dest_path = os.path.join(LOCAL_DIR, file_name)
    print(f"🚀 Pulling file from PikPak to GitHub Runner...")
    # copyto is safer than copy for specific single files
    run_cmd(["rclone", "copyto", f"{REMOTE}:{REMOTE_PATH}{file_name}", dest_path])
    
    if os.path.exists(dest_path):
        print(f"🏆 MISSION ACCOMPLISHED: {dest_path}")
        
        # 6. Cleanup (Optional: Remove ONLY the active file from cloud to save space)
        # print(f"🗑️ Deleting {file_name} from Cloud temp...")
        # run_cmd(["rclone", "delete", f"{REMOTE}:{REMOTE_PATH}{file_name}"])
    else:
        print("❌ Download failed. File not found on runner.")
        sys.exit(1)

if __name__ == "__main__":
    download()
