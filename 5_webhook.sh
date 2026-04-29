#!/bin/bash
set -e

# --- 1. GET FILE ---
OUT_FILE=$(ls ./output/*.mp4 2>/dev/null | head -n 1)

if [ ! -f "$OUT_FILE" ]; then
    echo "❌ Error: Final video file was not created."
    exit 1
fi

URL_FILENAME=$(basename "$OUT_FILE")
SAFE_NAME="${URL_FILENAME%.*}"

# --- 2. GIT SETUP ---
echo "📤 Uploading to GitHub..."

git config --global user.name "github-actions[bot]"
git config --global user.email "github-actions[bot]@users.noreply.github.com"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "🌿 Branch: $CURRENT_BRANCH"

# --- 3. CLEAN OLD FILES ---
find ./output -type f ! -name "$URL_FILENAME" -delete

# --- 4. STAGE PROPERLY (IMPORTANT) ---
git add -A output/
git add metadata.json

# --- 5. COMMIT ONLY IF CHANGES ---
if git diff --cached --quiet; then
    echo "No changes to commit"
else
    git commit -m "🎬 Reel: $SAFE_NAME [skip ci]"
    git push origin "$CURRENT_BRANCH" --force
fi

# --- 6. RAW URL ---
RAW_URL="https://raw.githubusercontent.com/${GITHUB_REPOSITORY}/${CURRENT_BRANCH}/output/${URL_FILENAME}"

# --- 7. WEBHOOK ---
if [ -n "$WEBHOOK_URL" ]; then
    echo "⏳ Waiting for GitHub sync..."
    sleep 5

    echo "📡 Sending webhook..."

    PAYLOAD=$(jq -n \
        --arg url "$RAW_URL" \
        --arg name "$URL_FILENAME" \
        '{fileUrl: $url, fileName: $name}')

    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$PAYLOAD" \
        "$WEBHOOK_URL")

    echo "📩 Response: $RESPONSE"
fi

echo "✅ Done"
