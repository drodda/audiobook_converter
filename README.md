# Audiobook Converter
Combine audio, cue sheet, and cover (optional) into a single file using ffmpeg

```
usage: python3 audiobook_convert.py [-h] [-c COVER] [--ffmpeg FFMPEG] [--ffprobe FFPROBE] [--audio-codec AUDIO_CODEC] [--ffmpeg-loglevel FFMPEG_LOGLEVEL] audio_file cue_file output_file

Combine audio, cue sheet, and cover (optional) into a single file using ffmpeg

positional arguments:
  audio_file            Audiobook file path
  cue_file              Cue file path
  output_file           Output file path

optional arguments:
  -h, --help            show this help message and exit
  -c COVER, --cover COVER
                        Cover file (optional)
  --ffmpeg FFMPEG       ffmpeg binary path. Default: 'ffmpeg'
  --ffprobe FFPROBE     ffmpeg binary path. Default: 'ffprobe'
  --audio-codec AUDIO_CODEC
                        ffmpeg audio codec options. Default: 'copy'
  --ffmpeg-loglevel FFMPEG_LOGLEVEL
                        ffmpeg log level. Default: 'warning'
```

Example usage:
```
python3 audiobook_convert.py book.mp3 book.cue --cover cover.jpg book.m4b
```


This script will reencode or remux an audiobook (usually mp3) into an mp4 container and embed chapters from a cuesheet. It can optionally also add a cover image.

Chapters are parsed from a cuesheet and written to an ffmpeg metadata file, which is used when converting an audiobook with ffmpeg. 
