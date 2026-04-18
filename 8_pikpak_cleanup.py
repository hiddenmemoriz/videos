import os
import json
import subprocess
import sys

def cleanup():
    # Load metadata to get the filename we just processed
    if not os.path.exists("metadata.json"):
        print("❌ Metadata missing, cleanup skipped.")
        return

    with open("metadata.json", "r") as f:
        meta = json.load(f)

    file_name = meta.get('cloud_file_name')
    remote_path = "/Download/temp/"
    remote_name = "mypikpak"

    if not file_name:
        print("⚠️ No cloud filename found in metadata. Nothing to delete.")
        return

    print(f"🗑️ Deleting processed file from PikPak: {file_name}")
    
    # Run rclone delete
    # This keeps your warm-up files safe because it targets only this specific file
    cmd = ["rclone", "delete", f"{remote_name}:{remote_path}{file_name}"]
    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode == 0:
        print("✅ PikPak cloud cleaned successfully.")
    else:
        print(f"❌ Cleanup failed: {res.stderr}")

if __name__ == "__main__":
    cleanup()
