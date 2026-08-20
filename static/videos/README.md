# Hero background video

Drop a video file in this folder and the home page hero will use it
automatically — no settings change, no code change.

- Accepted: `.mp4` (preferred), `.webm`, `.mov`
- If several are present the first `.mp4` alphabetically wins
- With a file here, the YouTube embed is skipped entirely
- Remove the file and the site falls back to the YouTube embed

Discovery is cached for 5 minutes, so allow a moment (or restart the dev
server) after adding a file.

## Getting the file

The hero video is your own upload, so download the original from
YouTube Studio → Content → the video → the three-dot menu → Download.
That avoids third-party downloader sites entirely.

## Compressing it

A hero background should be small. It is muted, sits behind a dark scrim
and is decorative, so it does not need to be high fidelity. Aim for under
about 5 MB.

With ffmpeg:

    ffmpeg -i original.mp4 \
      -t 20 -an \
      -vf "scale=1280:-2" \
      -c:v libx264 -crf 30 -preset slow -movflags +faststart \
      hero.mp4

- `-t 20` trims to the first 20 seconds; it loops, so it does not need to
  be the whole video
- `-an` strips the audio track: the hero is always muted, so the audio is
  pure wasted bytes
- `scale=1280` is plenty behind a scrim
- `+faststart` moves the index to the front so playback can begin before
  the whole file has downloaded

## Poster frame

`static/images/hero_poster.jpg` shows instantly and stays visible until
the video is ready, so the hero never looks empty. Replace it with a still
from your own footage if you would like a closer match.
