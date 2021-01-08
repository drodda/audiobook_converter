#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
import tempfile
import traceback


DESCRIPTION = "Combine audio, cue sheet, and cover (optional) into a single file using ffmpeg"


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("audio_file", help="Audiobook file path")
    parser.add_argument("cue_file", help="Cue file path")
    parser.add_argument("output_file", help="Output file path")
    parser.add_argument("-c", "--cover", help="Cover file")
    parser.add_argument("--ffmpeg", help="ffmpeg binary path", default="ffmpeg")
    parser.add_argument("--ffprobe", help="ffmpeg binary path", default="ffprobe")
    parser.add_argument("--audio-codec", help="ffmpeg audio codec options", default="copy")
    parser.add_argument("-v", "--ffmpeg-loglevel", help="ffmpeg log level", default="warning")
    args = parser.parse_args()

    _, output_ext = os.path.splitext(args.output_file)
    if output_ext not in [".mp4", ".m4a", ".m4b"]:
        print("Output file should be .mp4 or .m4a or .m4b")
        sys.exit(-1)

    # Get duration of audio file
    cmd = [
        args.ffprobe,
        "-v", "error",
        "-show_entries",
        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
        args.audio_file,
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE)
    if p.returncode != 0:
        print("Error: unable to get audio duration")
        sys.exit(-1)
    duration = float(p.stdout)

    # Convert cue sheet to ffmpeg metadata
    cuesheet = CueSheet.from_cuesheet(open(args.cue_file).read(), duration=duration)
    ffmpeg_metadata = cuesheet.as_ffmpeg_metadata()

    # Create output file
    with tempfile.NamedTemporaryFile(mode="w", prefix="ffmpeg_meta_", suffix=".ini") as meta_fd:
        meta_fd.write(ffmpeg_metadata)
        meta_fd.flush()

        cmd = [
            args.ffmpeg,
            "-i", args.audio_file,
            "-i", meta_fd.name,
        ]
        if args.cover:
            cmd += [
                "-i", args.cover,
                "-c:v", "copy",
                "-map", "2",
                "-disposition:0", "attached_pic",
            ]
        cmd += [
            "-c:a", args.audio_codec,
            "-map", "0",
            "-map_metadata", "1",
            "-f", "mp4",
            args.output_file,
            "-stats",
            "-loglevel", args.ffmpeg_loglevel,
        ]
        p = subprocess.run(cmd)
    if p.returncode != 0:
        print("Error: conversion failed")
        sys.exit(-1)
    print("Finished writing {}".format(args.output_file))


class CueSheet:
    """ Minimum representation of cue sheet required to produce ffmpeg metadata chapters """

    class CueTrack:
        """ Minimum representation of cue sheet track """
        def __init__(self, title, time_start, time_end=None):
            self.title = title
            self.start = time_start
            self.end = time_end

        def __repr__(self):
            return '<"{}" - {}:{}>'.format(self.title, self.start, self.end or "?")

    def __init__(self, title, artist, tracks=None):
        self.title = title
        self.artist = artist
        self.tracks = tracks if tracks else []

    def __repr__(self):
        return '<"{}" - "{}" ({} tracks)>'.format(self.title, self.artist, len(self.tracks))

    def as_ffmpeg_metadata(self):
        def _escape(s):
            for tok in ["\\", "=", ";", "#"]:
                s = s.replace(tok, "\\" + tok)
            return s
        result = ";FFMETADATA1\n"
        if self.title:
            result += "title={}\n".format(_escape(self.title))
        if self.artist:
            result += "artist={}\n".format(_escape(self.artist))
        for track in self.tracks:
            result += "[CHAPTER]\nTIMEBASE=1/1000\n"
            result += "START={}\n".format(int(track.start * 1000))
            track_end = track.end or track.start
            result += "END={}\n".format(int(track_end * 1000))
            if track.title:
                result += "title={}\n".format(_escape(track.title))
        return result

    @classmethod
    def from_cuesheet(cls, text, duration=None):
        """ Constructor: create CueSheet from cuesheet text """
        header_dict, track_dicts = cls._split_cuesheet_text(text)
        # Parse header
        title = header_dict.get("TITLE", "").strip('"')
        artist = header_dict.get("PERFORMER", "").strip('"')

        # Parse tracks to get title and start and end times
        n_tracks = len(track_dicts)
        tracks_start = []
        tracks_title = []
        offset = 0
        for track_dict in track_dicts:
            if "INDEX" in track_dict:
                # Ignore index number, use only time
                val = track_dict["INDEX"].split(" ")[-1].split(":")
                # Minutes
                offset = int(val[0]) * 60
                if len(val) > 1:
                    # Seconds
                    offset += int(val[1])
                    if len(val) > 2:
                        # Frames
                        offset += int(val[2]) / 75
            tracks_start.append(offset)
            tracks_title.append(track_dict.get("TITLE", "").strip('"'))
        tracks_end = tracks_start[1:] + [duration]

        # Make CueTrack and CueSheet objects
        tracks = [cls.CueTrack(tracks_title[i], tracks_start[i], tracks_end[i]) for i in range(n_tracks)]
        return cls(title, artist, tracks)

    @classmethod
    def _split_cuesheet_text(cls, text):
        """ Split a cue sheet into a dictionary of params from header and a list of list of dicts for each track """
        header_dict = {}
        track_dicts = []
        track_dict = {}
        in_header = True
        for line in text.splitlines():
            key, val = line.strip().split(" ", 1)
            if key == "TRACK":
                in_header = False
                # Push the current track
                if track_dict:
                    track_dicts.append(track_dict)
                # Start new track
                track_dict = {key: val}
            else:
                if in_header:
                    header_dict[key] = val
                else:
                    track_dict[key] = val
        # Push last track
        if track_dict:
            track_dicts.append(track_dict)
        return header_dict, track_dicts


if __name__ == "__main__":
    # noinspection PyBroadException
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception:
        traceback.print_exc()
