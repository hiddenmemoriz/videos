#!/bin/bash

# --- PATHS ---
AUDIO="./assets/trim_audio/trim_audio.mp3"
IMAGE="./assets/image/image.jpg"
LOGO="./assets/spotify.png"
FINAL_OUT="./output/output.mp4"

mkdir -p ./output

# 1. Verify Audio and Get Exact Duration
if [ ! -f "$AUDIO" ]; then
    echo "❌ ERROR: Trimmed audio not found at $AUDIO"
    exit 1
fi

# Get duration using ffprobe (e.g., 20.04)
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")

# 2. AUTO-CALCULATE TIMINGS
# logo_start = middle of the video
LOGO_START=$(echo "$DURATION / 2" | bc -l)
# fade_out = 2 seconds before the end
FADE_OUT=$(echo "$DURATION - 2" | bc -l)

echo "🎬 Rendering Reel..."
echo "⏱️ Total Duration: $DURATION"
echo "🎨 Logo Start: $LOGO_START | Fade Out: $FADE_OUT"

# 3. RENDER ENGINE
# We use -t $DURATION at the input level to prevent the infinite loop bug
ffmpeg -y \
-t "$DURATION" -loop 1 -i "$IMAGE" \
-t "$DURATION" -i "$AUDIO" \
-t "$DURATION" -loop 1 -i "$LOGO" \
-filter_complex "
[0:v]format=yuv420p,crop=min(iw\,ih):min(iw\,ih),scale=1080:1080,eq=saturation=1.2:contrast=1.05[cover];
[0:v]format=yuv420p,crop=min(iw\,ih):min(iw\,ih),scale=300:300,gblur=sigma=15,
scale=1080:1920:force_original_aspect_ratio=increase,
zoompan=z='1.03+0.01*sin(on*0.3)':d=1:s=1080x1920:fps=30,
rotate='0.04*sin(2*PI*t/5)':fillcolor=black@0,
crop=1080:1920[bg];
[cover]scale=900:900[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2-200[vbase];
[2:v]scale=200:-1[logo];
[logo]fade=t=in:st=$LOGO_START:d=0.6:alpha=1,
fade=t=out:st=$FADE_OUT:d=2:alpha=1[logofaded];
[vbase][logofaded]overlay=(W-w)/2:H-h-60:enable='between(t,$LOGO_START,$DURATION)',format=yuv420p[v];
[1:a]afade=t=in:st=0:d=1.5,afade=t=out:st=$FADE_OUT:d=2[a]
" \
-map "[v]" \
-map "[a]" \
-c:v libx264 -preset veryfast -crf 22 \
-pix_fmt yuv420p \
-c:a aac -b:a 192k \
"$FINAL_OUT"

echo "✅ Success: $FINAL_OUT"
