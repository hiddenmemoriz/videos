import os
import json
import subprocess

def sync_cleanup():
    if not os.path.exists("metadata.json"):
        print("❌ Metadata missing, cleanup skipped.")
        return

    with open("metadata.json", "r") as f:
        meta = json.load(f)

    # 1. Identify what we MUST KEEP (the next video)
    prefetch_list = meta.get('prefetch_urls', [])
    keep_ids = []
    for url in prefetch_list:
        # Extract Video ID safely
        p_vid_id = url.split("v=")[-1].split("&")[0]
        keep_ids.append(p_vid_id)

    remote_name = "mypikpak"
    # Try without the leading slash if /Download/temp/ fails
    remote_path = "Download/temp/" 

    print(f"📡 Scanning Cloud: {remote_name}:{remote_path}")
    
    # 2. Check if the directory even exists to avoid the ERROR listing loop
    check_cmd = ["rclone", "lsd", f"{remote_name}:Download/"]
    check_res = subprocess.run(check_cmd, capture_output=True, text=True)
    
    if "directory not found" in check_res.stderr:
        print("⚠️ Path not found on server. Nothing to clean.")
        return

    # 3. List files in the cloud
    ls_cmd = ["rclone", "lsf", f"{remote_name}:{remote_path}"]
    res = subprocess.run(ls_cmd, capture_output=True, text=True)
    
    if res.returncode != 0:
        print(f"⚠️ Could not list directory: {res.stderr.strip()}")
        return

    cloud_files = res.stdout.splitlines()

    # 4. Delete old files
    for file_name in cloud_files:
        # Skip directories
        if file_name.endswith('/'):
            continue
            
        should_keep = False
        for vid_id in keep_ids:
            if vid_id in file_name:
                should_keep = True
                break
        
        if not should_keep:
            print(f"🗑️ Purging: {file_name}")
            # Use 'deletefile' to target the specific file accurately
            del_cmd = ["rclone", "deletefile", f"{remote_name}:{remote_path}{file_name}"]
            subprocess.run(del_cmd)
        else:
            print(f"✅ Keeping pre-fetch: {file_name}")

if __name__ == "__main__":
    sync_cleanup()
