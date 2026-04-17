#!/bin/bash

# Find the rendered video (handles dynamic naming)
FINAL_OUT=$(ls ./output/*.mp4 2>/dev/null | head -n 1)
METADATA="metadata.json"

if [ -z "$FINAL_OUT" ]; then
    echo "❌ ERROR: No video found in ./output/ to upload."
    exit 1
fi

FILENAME=$(basename "$FINAL_OUT")

# Check if the secret variable is actually set
if [ -z "$WEBHOOK_URL" ]; then
    echo "⚠️ WEBHOOK_URL is not set. Cannot upload."
    exit 1
fi

echo "📡 Found file: $FILENAME"
echo "📡 Encoding and sending to Google Drive..."

# Encode video to base64
BASE64_VIDEO=$(base64 -w 0 "$FINAL_OUT")

# Send to Apps Script
RESPONSE=$(curl -L -s -X POST "$WEBHOOK_URL" \
    -F "filename=$FILENAME" \
    -F "file=$BASE64_VIDEO")

echo "📩 Server Response: $RESPONSE"

if [[ "$RESPONSE" == *"Success"* ]]; then
    echo "🎉 Upload Complete!"
else
    echo "❌ Upload Failed. Check Google Apps Script logs."
    exit 1
fi
