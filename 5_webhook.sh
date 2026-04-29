#!/bin/bash
set -e

# --- 1. GET OUTPUT FILE ---
OUT_FILE=$(ls ./output/*.mp4 2>/dev/null | head -n 1)

if [ ! -f "$OUT_FILE" ]; then
    echo "❌ Error: No video file found."
    exit 1
fi

FILENAME=$(basename "$OUT_FILE")
SAFE_NAME="${FILENAME%.*}"

# --- 2. GIT SETUP ---
echo "📤 Preparing Git..."

git config --global user.name "github-actions[bot]"
git config --global user.email "github-actions[bot]@users.noreply.github.com"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "🌿 Branch: $CURRENT_BRANCH"

# --- 3. CLEAN OLD FILES (keep only latest) ---
find ./output -type f ! -name "$FILENAME" -delete

# --- 4. STAGE EVERYTHING CORRECTLY ---
git add -A output/
git add metadata.json

# --- 5. COMMIT + FORCE PUSH ---
if git diff --cached --quiet; then
    echo "No changes to commit"
else
    git commit -m "🎬 Reel: $SAFE_NAME [skip ci]"
    git push origin "$CURRENT_BRANCH" --force
    echo "✅ Pushed latest video"
fi

# --- 6. BUILD RAW URL ---
RAW_URL="https://raw.githubusercontent.com/${GITHUB_REPOSITORY}/${CURRENT_BRANCH}/output/${FILENAME}"

# --- 7. WEBHOOK ---
if [ -n "$WEBHOOK_URL" ]; then
    echo "⏳ Waiting for GitHub to update..."
    sleep 5

    echo "📡 Sending webhook..."

    PAYLOAD=$(jq -n \
        --arg url "$RAW_URL" \
        --arg name "$FILENAME" \
        '{fileUrl: $url, fileName: $name}')

    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$PAYLOAD" \
        "$WEBHOOK_URL")

    echo "📩 Response: $RESPONSE"
fi

echo "✨ Done"
