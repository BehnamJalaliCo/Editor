#!/usr/bin/env bash
# usage: master.sh WORKDIR OUT.mp4  — mux picture.mp4 + mix.wav, 2-pass loudnorm to -14 LUFS / -1 dBTP
set -euo pipefail
W=$1; OUT=$2
J=$(ffmpeg -hide_banner -i "$W/mix.wav" -af loudnorm=I=-14:TP=-1.0:LRA=9:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
M=$(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(f\"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}\")")
ffmpeg -v error -y -i "$W/picture.mp4" -i "$W/mix.wav" -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-14:TP=-1.0:LRA=9:$M:linear=true,aresample=48000" -c:a aac -b:a 256k \
  -shortest -movflags +faststart "$OUT"
