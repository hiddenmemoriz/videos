#!/bin/bash
mkdir -p ./output

# Path Configuration
AUDIO="./assets/audio/audio.mp3"
IMAGE="./assets/image/image.jpg"
LOGO="./assets/spotify.png" # Ensure this exists in your root or assets
FINAL_OUT="./output/output.mp4"

# 1. Get duration using ffprobe
duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")

# 2. Calculate timing
# Note: bc is required for decimal math in bash
logo_start=$(echo "$duration * 0.5" | bc)
fade_out=$(echo "$duration - 2" | bc)

echo "🎬 Rendering Phonk Reel..."
echo "⏱️ Duration: $duration | Logo Start: $logo_start | Fade Out: $fade_out"

# 3. The Heavy Duty FFmpeg Render
ffmpeg -y \
-loop 1 -i "$IMAGE" \
-i "$AUDIO" \
-loop 1 -i "$LOGO" \
-filter_complex "
[0:v]format=yuv420p,crop=min(iw\,ih):min(iw\,ih),scale=1080:1080,eq=saturation=1.2:contrast=1.05[cover];
[0:v]format=yuv420p,crop=min(iw\,ih):min(iw\,ih),
scale=1500:1500,
gblur=sigma=30,
zoompan=z='1.03+0.01*sin(on*0.3)':d=1:s=1400x1400:fps=30,
rotate='0.04*sin(2*PI*t/5)':fillcolor=black@0,
scale=1080:1920:force_original_aspect_ratio=increase,
crop=1080:1920[bg];
[cover]scale=900:900[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2-200[vbase];
[2:v]scale=200:-1[logo];
[logo]fade=t=in:st=$logo_start:d=0.6:alpha=1,
fade=t=out:st=$fade_out:d=2:alpha=1[logofaded];
[vbase][logofaded]overlay=(W-w)/2:H-h-60:enable='between(t,$logo_start,$duration)',format=yuv420p[v];
[1:a]afade=t=in:st=0:d=1.5,afade=t=out:st=$fade_out:d=2[a]
" \
-map "[v]" \
-map "[a]" \
-c:v libx264 -preset fast -crf 18 \
-pix_fmt yuv420p \
-c:a aac -b:a 192k \
-shortest \
-t "$duration" \
"$FINAL_OUT"

echo "✅ Rendering Complete: $FINAL_OUT"
