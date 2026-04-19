#!/bin/bash

# --- 1. CONFIG & ASSETS ---
AUDIO="./assets/audio/audio.mp3"
IMAGE="./assets/image/image.jpg"
LOGO="./assets/spotify.png"
METADATA="metadata.json"
OUT_DIR="./output"
TEMP_LOOP="temp_motion.mp4"

mkdir -p "$OUT_DIR"

# --- 2. READ METADATA & SANITIZE ---
if [ -f "$METADATA" ] && command -v jq >/dev/null 2>&1; then
    ARTIST=$(jq -r '.artist // "Artist"' "$METADATA" | sed 's/[^a-zA-Z0-9 ]//g' | tr ' ' '_')
    TRACK=$(jq -r '.track // "Track"' "$METADATA" | sed 's/[^a-zA-Z0-9 ]//g' | tr ' ' '_')
    FILENAME="${ARTIST}_-_${TRACK}.mp4"
else
    FILENAME="reel_$(date +%s).mp4"
fi
FINAL_OUT="$OUT_DIR/$FILENAME"

# --- 3. CALCULATE TIMINGS ---
if [ ! -f "$AUDIO" ]; then echo "❌ Missing audio: $AUDIO"; exit 1; fi
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")
FADE_OUT_START=$(echo "$DURATION - 2" | bc -l)

# --- 4. PHASE 1: PRE-RENDER 10S MOTION LOOP ---
# We render at 720p (1280x720) because it's blurred—this saves 50% CPU time.
echo "⚡ Phase 1: Generating 10s Motion Loop (720p Optimized)..."
ffmpeg -y -loop 1 -t 10 -i "$IMAGE" \
-filter_complex "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,zoompan=z='1.03+0.01*sin(on*0.3)':d=300:s=1280x720:fps=30,boxblur=10:5" \
-c:v libx264 -preset ultrafast -crf 20 -pix_fmt yuv420p "$TEMP_LOOP"

# --- 5. PHASE 2: FINAL ASSEMBLY ---
# We stream_loop the motion background and overlay high-res foreground assets.
echo "🎬 Phase 2: Assembling Final Reel ($FILENAME)..."
ffmpeg -y \
-stream_loop -1 -t "$DURATION" -i "$TEMP_LOOP" \
-i "$AUDIO" \
-loop 1 -t "$DURATION" -i "$IMAGE" \
-loop 1 -t "$DURATION" -i "$LOGO" \
-filter_complex "
[0:v]scale=1920:1080,rotate='0.04*sin(2*PI*n/150)':fillcolor=black@0[bg];
[2:v]scale=600:600:force_original_aspect_ratio=increase,crop=600:600,eq=saturation=1.2:contrast=1.05[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2[vbase];
[3:v]scale=150:-1,format=yuva420p,fade=t=in:st=5:d=1:alpha=1,fade=t=out:st=9:d=1:
