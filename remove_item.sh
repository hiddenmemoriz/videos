#!/bin/bash

# 1. Extract the cookie and authorization from your JSON secret
# Most YTM OAuth JSONs store the headers in a specific block
COOKIE=$(echo '$YTM_OAUTH_JSON' | jq -r '.headers.Cookie // empty')
AUTH=$(echo '$YTM_OAUTH_JSON' | jq -r '.headers.Authorization // empty')

# 2. Define IDs
PLAYLIST_ID="PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"
VIDEO_ID="-oIMyMEvMLI"

# 3. Get the internal 'setVideoId'
# This is the "secret" row ID for that specific song in your playlist
# We use a raw browse request to find it
echo "Searching for internal setVideoId..."
PLAYLIST_DATA=$(curl -s -X POST "https://music.youtube.com/youtubei/v1/browse?key=AIzaSyAO_SshvRxxxxxxx" \
  -H "Content-Type: application/json" \
  -H "Authorization: $AUTH" \
  -H "Cookie: $COOKIE" \
  -d '{"browseId": "VL'"$PLAYLIST_ID"'"}' )

SET_VIDEO_ID=$(echo "$PLAYLIST_DATA" | jq -r --arg vid "$VIDEO_ID" '.. | objects | select(.videoId? == $vid) | .setVideoId' | head -n 1)

if [ -z "$SET_VIDEO_ID" ]; then
    echo "Error: Could not find track in playlist."
    exit 1
fi

echo "Found setVideoId: $SET_VIDEO_ID. Removing track..."

# 4. The Nuclear Option: Raw Remove Request
curl -s -X POST "https://music.youtube.com/youtubei/v1/browse/edit_playlist?key=AIzaSyAO_SshvRxxxxxxx" \
  -H "Content-Type: application/json" \
  -H "Authorization: $AUTH" \
  -H "Cookie: $COOKIE" \
  -d '{
    "context": {
      "client": {
        "clientName": "WEB_REMIX",
        "clientVersion": "1.20240410.01.00"
      }
    },
    "playlistId": "'"$PLAYLIST_ID"'",
    "actions": [
      {
        "action": "ACTION_REMOVE_VIDEO",
        "setVideoId": "'"$SET_VIDEO_ID"'"
      }
    ]
  }'
