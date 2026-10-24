#!/usr/bin/env python3
"""Post-production recipes on the system ffmpeg: the glue between every other cutroom tool.

Commands (also `cutroom edit ...`). Every command prints the ffmpeg line it runs; --dry-run prints without running.
  probe <file> [--json]                         duration, size, fps, codecs, loudness (LUFS) of audio
  trim <in> -o out [--start 0:03] [--end 0:12 | --duration 9] [--copy]
  concat <in...> -o out [--size 1920x1080] [--fps 30] [--gap 0]
                                                videos (scaled/padded to one size; silent clips get silence) or audios
  mix --voice narration.wav [--music bed.mp3] -o out.m4a [--music-db -20] [--duck] [--fade 1.5] [--tail 1]
                                                narration over music; --duck lowers the music while the voice speaks
  score <video> -o out.mp4 [--voice narration.wav] [--music bed.mp3] [--duck] [--music-db -20] [--offset 0]
                                                put narration and/or music under a video (video length wins)
  sfx <in> --cues cues.json -o out.mp4 [--stem sfx.wav] [--master-db 0]
                                                render earshot sound-effect cues sample-accurately on visual beats and mix
  loudnorm <in> -o out [--target -16]           loudness: -16 LUFS podcasts and voice, -14 LUFS social video
  captions <video> <subs.srt> -o out.mp4 [--brand NAME] [--size 46] [--position bottom|top]
                                                burn captions in the brand's text font and colors
  reframe <in> -o out --aspect 9:16|1:1|4:5|16:9 [--mode blur|crop|pad] [--height 1920]
                                                vertical and square cuts: blur-filled, cropped or padded in the brand
  watermark <in> -o out [--logo file|brand] [--corner br|bl|tr|tl] [--width 0.12] [--margin 0.04]
  gif <in> -o out.gif [--start 0] [--duration 6] [--fps 12] [--width 720]
  frames <in> -o folder [--every 2 | --at 1,5,10]  PNG frames to look at
  sheet <in> -o sheet.png [--cols 4] [--rows 3] [--width 1600]
                                                contact sheet of evenly spaced frames with timestamps
  compress <in> -o out.mp4 [--preset web|artifact|email|social] [--max-mb 15]
  stills <image...> -o out.mp4 [--seconds 4] [--size 1920x1080] [--zoom 1.08] [--audio narration.wav] [--fade 0.6]
                                                slideshow with a slow push-in (Ken Burns) and cross-fades
  audiogram <audio> -o out.mp4 [--title "..."] [--aspect 1:1|9:16|16:9] [--brand NAME]
                                                waveform video in the brand colors, for podcasts and narration clips
  silences <audio> [--db -38] [--min 0.12] [--json]
                                                pauses in speech: scene cut points for timing animations
  extract-audio <in> -o out.wav
"""
import argparse
from html import escape as html_escape
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cutroom_brand  # noqa: E402

DRY = False
ASPECTS = {"9:16": (9, 16), "1:1": (1, 1), "4:5": (4, 5), "16:9": (16, 9), "4:3": (4, 3), "3:4": (3, 4)}
PRESETS = {  # height, crf, audio kbps
    "web": (1080, 23, 128), "artifact": (720, 28, 96), "email": (540, 30, 64), "social": (1080, 21, 160),
}


def need(tool="ffmpeg"):
    if not shutil.which(tool):
        hint = cutroom_brand.install_hint(tool) if hasattr(cutroom_brand, "install_hint") else f"install {tool}"
        raise SystemExit(f"{tool} not found: {hint}")


def ff(args, quiet=True):
    need()
    cmd = ["ffmpeg", "-y", "-hide_banner"] + (["-loglevel", "error"] if quiet else []) + [str(a) for a in args]
    print("$ " + " ".join(f'"{c}"' if " " in c or ";" in c else c for c in cmd), flush=True)
    if DRY:
        return ""
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"ffmpeg failed: {r.stderr.strip()[-800:]}")
    return r.stderr


def probe(path):
    need("ffprobe")
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"cannot read {path}: {r.stderr.strip()}")
    return json.loads(r.stdout)


def info(path):
    p = probe(path)
    v = next((s for s in p["streams"] if s["codec_type"] == "video" and s.get("disposition", {}).get("attached_pic") != 1), None)
    a = next((s for s in p["streams"] if s["codec_type"] == "audio"), None)
    out = {"file": str(path), "duration": float(p["format"].get("duration", 0) or 0),
           "size_mb": round(int(p["format"].get("size", 0)) / 1e6, 2)}
    if v:
        num, den = (v.get("avg_frame_rate") or "0/1").split("/")
        out.update(width=v["width"], height=v["height"], fps=round(int(num) / int(den), 2) if int(den) else None,
                   video_codec=v["codec_name"])
    if a:
        out.update(audio_codec=a["codec_name"], sample_rate=int(a.get("sample_rate", 0)), channels=a.get("channels"))
    return out


def has_audio(path):
    return any(s["codec_type"] == "audio" for s in probe(path)["streams"])


def is_audio_only(path):
    return not any(s["codec_type"] == "video" and s.get("disposition", {}).get("attached_pic") != 1
                   for s in probe(path)["streams"])


def loudness(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
    return float(m[-1]) if m else None


def ts(s):
    """'1:05.5', '65.5' or 65.5 -> seconds."""
    if isinstance(s, (int, float)):
        return float(s)
    total = 0.0
    for part in str(s).split(":"):
        total = total * 60 + float(part)
    return total


def video_codec(out):
    ext = Path(out).suffix.lower()
    if ext == ".webm":
        return ["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "33", "-c:a", "libopus"]
    return ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-movflags", "+faststart",
            "-c:a", "aac", "-b:a", "160k"]


def audio_codec(out):
    ext = Path(out).suffix.lower()
    return {".mp3": ["-c:a", "libmp3lame", "-q:a", "3"], ".wav": ["-c:a", "pcm_s16le"], ".flac": ["-c:a", "flac"],
            ".opus": ["-c:a", "libopus", "-b:a", "96k"]}.get(ext, ["-c:a", "aac", "-b:a", "160k"])


def brand():
    try:
        return cutroom_brand.load()
    except SystemExit:
        return None


def brand_font_file(m, role="text", weight="600"):
    if not m:
        return None
    fam = m["fonts"].get(role)
    files = [f for f in m["fonts"].get("files", []) if f["family"] == fam]
    files.sort(key=lambda f: abs(int(str(f.get("weight", "400")).split()[0]) - int(weight)))
    return str(Path(m["dir"]) / files[0]["file"]) if files else None


_FILTERS = None


def has_filter(name):
    """Homebrew's default ffmpeg ships without freetype and libass: no drawtext, no subtitles."""
    global _FILTERS
    if _FILTERS is None:
        out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
        _FILTERS = {l.split()[1] for l in out.splitlines() if len(l.split()) > 2 and l.startswith(" ")}
    return name in _FILTERS


def text_pngs(items, w, h, folder, m=None):
    """Render text overlays as transparent PNGs in Chrome, with the brand fonts (no drawtext needed).

    items: [(name, inner HTML, CSS for the box)]; each PNG is w x h, the box placed by its CSS.
    """
    m = m or brand()
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    fonts = (Path(m["dir"]) / "fonts.css").as_uri() if m else ""
    out = []
    for name, inner, box in items:
        page = folder / f"{name}.html"
        page.write_text(f'<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="{fonts}"><style>'
                        f'html,body{{margin:0;width:{w}px;height:{h}px;background:transparent;overflow:hidden}}'
                        f'.b{{position:absolute;{box}}}</style><div class="b">{inner}</div>', encoding="utf-8")
        png = folder / f"{name}.png"
        cutroom_brand.chrome_run([f"--screenshot={png}", f"--window-size={w},{h}", "--default-background-color=00000000",
                                  "--virtual-time-budget=2000", page.as_uri()])
        out.append(png)
    return out


def parse_srt(path):
    cues = []
    for block in re.split(r"\n\s*\n", Path(path).read_text(encoding="utf-8-sig").strip()):
        lines = block.strip().splitlines()
        tl = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if tl is None:
            continue
        a, b = [x.strip().replace(",", ".") for x in lines[tl].split("-->")]
        cues.append((ts(a), ts(b.split()[0]), "\n".join(lines[tl + 1:])))
    return cues


def ffcolor(hx):
    return "0x" + hx.lstrip("#")


def esc_filter_path(p):
    return str(p).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


# --- commands ------------------------------------------------------------------------------------

def cmd_probe(a):
    i = info(a.file)
    if not is_audio_only(a.file) and not has_audio(a.file):
        i["loudness_lufs"] = None
    else:
        i["loudness_lufs"] = loudness(a.file)
    if a.json:
        print(json.dumps(i, indent=2))
    else:
        for k, v in i.items():
            print(f"{k:<14} {v}")


def cmd_trim(a):
    start = ts(a.start or 0)
    args = ["-ss", start, "-i", a.input]
    if a.end is not None:
        args += ["-t", ts(a.end) - start]
    elif a.duration is not None:
        args += ["-t", ts(a.duration)]
    if a.copy:
        args += ["-c", "copy"]
    elif is_audio_only(a.input):
        args += audio_codec(a.output)
    else:
        args += video_codec(a.output)
    ff(args + [a.output])


def cmd_concat(a):
    if all(is_audio_only(f) for f in a.inputs):
        inputs = sum([["-i", f] for f in a.inputs], [])
        parts = "".join(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo[a{i}];" for i in range(len(a.inputs)))
        if a.gap:
            parts += f"anullsrc=r=48000:cl=stereo,atrim=duration={a.gap}[g];"
        chain = "".join(f"[a{i}]" for i in range(len(a.inputs)))
        ff(inputs + ["-filter_complex", parts + f"{chain}concat=n={len(a.inputs)}:v=0:a=1[out]", "-map", "[out]"]
           + audio_codec(a.output) + [a.output])
        return
    first = info(a.inputs[0])
    w, h = map(int, (a.size or f"{first['width']}x{first['height']}").split("x"))
    fps = a.fps or first.get("fps") or 30
    inputs, chains, labels = [], [], []
    for i, f in enumerate(a.inputs):
        inputs += ["-i", f]
        d = info(f)["duration"]
        chains.append(f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,"
                      f"setsar=1,fps={fps},format=yuv420p[v{i}]")
        if has_audio(f):
            chains.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo[a{i}]")
        else:
            chains.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={d}[a{i}]")
        labels.append(f"[v{i}][a{i}]")
    fc = ";".join(chains) + ";" + "".join(labels) + f"concat=n={len(a.inputs)}:v=1:a=1[v][a]"
    ff(inputs + ["-filter_complex", fc, "-map", "[v]", "-map", "[a]"] + video_codec(a.output) + [a.output])


def duck_chain(voice_label, music_label, music_db, duck, fade, total):
    """Music under the voice: level, optional sidechain ducking, fades. Returns (filters, output label)."""
    f = [f"{music_label}volume={music_db}dB,afade=t=in:d={fade},afade=t=out:st={max(0, total - fade)}:d={fade}[m0]"]
    if duck:
        f.append(f"{voice_label}asplit=2[vk][vm]")
        f.append("[m0][vk]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=350:makeup=1[m1]")
        f.append("[vm][m1]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mix]")
    else:
        f.append(f"{voice_label}[m0]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mix]")
    return f, "[mix]"


def cmd_mix(a):
    vd = info(a.voice)["duration"]
    total = vd + a.tail
    if not a.music:
        ff(["-i", a.voice, "-af", f"apad=pad_dur={a.tail}", "-t", total] + audio_codec(a.output) + [a.output])
        return
    f = [f"[0:a]aresample=48000,aformat=channel_layouts=stereo,apad=pad_dur={a.tail}[v]",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration={total}[mus]"]
    more, out = duck_chain("[v]", "[mus]", a.music_db, a.duck, a.fade, total)
    ff(["-i", a.voice, "-stream_loop", "-1", "-i", a.music, "-filter_complex", ";".join(f + more), "-map", out,
        "-t", total] + audio_codec(a.output) + [a.output])


def cmd_score(a):
    if not a.voice and not a.music:
        raise SystemExit("give --voice and/or --music")
    total = info(a.video)["duration"]
    inputs, f, idx = ["-i", a.video], [], 1
    has_v = False
    if a.voice:
        inputs += ["-i", a.voice]
        f.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(a.offset * 1000)}:all=1,"
                 f"apad,atrim=duration={total}[v]")
        idx += 1
        has_v = True
    elif has_audio(a.video):
        f.append(f"[0:a]aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration={total}[v]")
        has_v = True
    if a.music:
        inputs += ["-stream_loop", "-1", "-i", a.music]
        f.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration={total}[mus]")
    if has_v and a.music:
        more, out = duck_chain("[v]", "[mus]", a.music_db, a.duck, a.fade, total)
        f += more
    elif a.music:
        f.append(f"[mus]volume={a.music_db}dB,afade=t=in:d={a.fade},afade=t=out:st={max(0, total - a.fade)}:d={a.fade}[mix]")
        out = "[mix]"
    else:
        out = "[v]"
    ff(inputs + ["-filter_complex", ";".join(f), "-map", "0:v", "-map", out, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                 "-shortest", "-movflags", "+faststart", a.output])


def cmd_loudnorm(a):
    args = ["-i", a.input, "-af", f"loudnorm=I={a.target}:TP=-1.5:LRA=11"]
    if is_audio_only(a.input):
        args += ["-ar", "48000"] + audio_codec(a.output)
    else:
        args += ["-c:v", "copy", "-c:a", "aac", "-b:a", "160k"]
    ff(args + [a.output])
    if not DRY:
        print(f"loudness: {loudness(a.output):.1f} LUFS (target {a.target})")


def cmd_captions(a):
    m = cutroom_brand.load(a.brand) if a.brand else brand()
    c = m["colors"] if m else {"text": "#14161F", "deep": "#121A3A", "on_deep": "#FFFFFF"}
    font = m["fonts"]["text"] if m else "sans-serif"
    fontsdir = str(Path(m["dir"]) / "fonts") if m else None

    def ass(hx, alpha="00"):
        h = hx.lstrip("#")
        return f"&H{alpha}{h[4:6]}{h[2:4]}{h[0:2]}"
    style = (f"FontName={font},FontSize={a.size},Bold=1,PrimaryColour={ass(c['on_deep'])},"
             f"BackColour={ass(c['deep'], '40')},BorderStyle=4,Outline=10,Shadow=0,MarginV={a.margin},"
             f"Alignment={8 if a.position == 'top' else 2}")
    if has_filter("subtitles") and not a.html:
        sub = f"subtitles='{esc_filter_path(Path(a.subs).resolve())}'"
        if fontsdir:
            sub += f":fontsdir='{esc_filter_path(fontsdir)}'"
        sub += f":force_style='{style}'"
        ff(["-i", a.video, "-vf", sub] + video_codec(a.output) + [a.output])
        return
    # No libass (or --html): each cue becomes a transparent PNG in the brand font, played as one overlay track.
    i = info(a.video)
    W, H = i["width"], i["height"]
    px = round(a.size * min(W, H) / 1080)  # sized by the short side: the same look in 16:9 and 9:16
    pos = f"top:{a.margin * H // 1080}px" if a.position == "top" else f"bottom:{a.margin * H // 1080}px"
    box = (f"left:8%;right:8%;{pos};text-align:center;"
           f"font:700 {px}px/1.25 '{font}',sans-serif;color:{c['on_deep']};")
    cues = parse_srt(a.subs)
    with tempfile.TemporaryDirectory() as t:
        items = [("blank", "", "display:none")]
        for k, (s0, s1, text) in enumerate(cues):
            span = html_escape(text).replace("\n", "<br>")
            items.append((f"c{k:04d}", f'<span style="background:{c["deep"]}cc;padding:.18em .5em;border-radius:.3em;'
                                       f'-webkit-box-decoration-break:clone;box-decoration-break:clone;line-height:1.55">{span}</span>', box))
        pngs = text_pngs(items, W, H, t, m)
        lines, now = ["ffconcat version 1.0"], 0.0
        for k, (s0, s1, _) in enumerate(cues):
            if s0 > now:
                lines += [f"file '{pngs[0]}'", f"duration {s0 - now:.3f}"]
            lines += [f"file '{pngs[k + 1]}'", f"duration {max(0.04, s1 - max(s0, now)):.3f}"]
            now = max(now, s1)
        lines += [f"file '{pngs[0]}'", f"duration {max(0.04, i['duration'] - now):.3f}", f"file '{pngs[0]}'"]
        lst = Path(t) / "captions.txt"
        lst.write_text("\n".join(lines) + "\n")
        ff(["-i", a.video, "-f", "concat", "-safe", "0", "-i", lst, "-filter_complex",
            "[1:v]format=rgba[c];[0:v][c]overlay=0:0:eof_action=pass:format=auto,format=yuv420p[v]", "-map", "[v]",
            "-map", "0:a?"] + video_codec(a.output) + [a.output])


def cmd_reframe(a):
    i = info(a.input)
    aw, ah = ASPECTS.get(a.aspect) or tuple(map(int, a.aspect.split(":")))
    H = a.height or (1920 if ah > aw else 1080)
    W = int(round(H * aw / ah / 2) * 2)
    if a.mode == "crop":
        vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"
    elif a.mode == "pad":
        m = brand()
        bg = ffcolor(m["colors"]["deep"]) if m else "black"
        vf = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color={bg},setsar=1"
    else:
        vf = (f"split=2[bg][fg];[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=28:2,"
              f"eq=brightness=-0.08[b];[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[f];"
              f"[b][f]overlay=(W-w)/2:(H-h)/2,setsar=1")
    args = ["-i", a.input, "-filter_complex" if a.mode == "blur" else "-vf", vf]
    ff(args + video_codec(a.output) + [a.output])
    print(f"{a.output}  {W}x{H} from {i.get('width')}x{i.get('height')} ({a.mode})")


def logo_png(logo, width_px, tmp):
    """SVG logos are rasterized in Chrome at the target width; PNG/JPG pass through."""
    p = Path(logo)
    if p.suffix.lower() != ".svg":
        return str(p)
    out = Path(tmp) / "logo.png"
    page = Path(tmp) / "logo.html"
    page.write_text(f'<!doctype html><body style="margin:0;background:transparent"><img src="{p.resolve().as_uri()}" '
                    f'style="width:{width_px}px;display:block"></body>')
    import xml.etree.ElementTree as ET
    root = ET.parse(p).getroot()
    vb = [float(x) for x in (root.get("viewBox") or "0 0 100 100").split()]
    hpx = int(width_px * vb[3] / vb[2]) + 1
    cutroom_brand.chrome_run([f"--screenshot={out}", f"--window-size={width_px},{hpx}", "--default-background-color=00000000",
                              page.as_uri()])
    return str(out)


def cmd_watermark(a):
    i = info(a.input)
    m = brand()
    logo = a.logo
    if not logo or logo == "brand":
        if not m:
            raise SystemExit("no logo given and no brand")
        rel = m["logos"].get("on_deep" if a.on == "dark" else "on_light")
        if not rel:
            raise SystemExit("the brand has no logo for that background")
        logo = str(Path(m["dir"]) / rel)
    wpx = int(i["width"] * a.width)
    mx, my = int(i["width"] * a.margin), int(i["height"] * a.margin)
    pos = {"br": f"W-w-{mx}:H-h-{my}", "bl": f"{mx}:H-h-{my}", "tr": f"W-w-{mx}:{my}", "tl": f"{mx}:{my}"}[a.corner]
    with tempfile.TemporaryDirectory() as t:
        lp = logo_png(logo, wpx, t)
        ff(["-i", a.input, "-i", lp, "-filter_complex", f"[1:v]scale={wpx}:-1[lg];[0:v][lg]overlay={pos}"]
           + video_codec(a.output) + [a.output])


def cmd_gif(a):
    # Decode everything and trim after fps: variable frame rate sources (ManimGX) cut wrong with -ss/-t.
    vf = (f"fps={a.fps},trim=start={a.start}:duration={a.duration},setpts=PTS-STARTPTS,scale={a.width}:-1:flags=lanczos,"
          "split[x][y];[x]palettegen=stats_mode=diff[p];[y][p]paletteuse=dither=bayer:bayer_scale=4")
    ff(["-i", a.input, "-an", "-filter_complex", vf, a.output])
    if not DRY:
        print(f"{a.output}  {os.path.getsize(a.output) / 1e6:.2f} MB")


def cmd_frames(a):
    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=True)
    if a.at:
        for t in a.at.split(","):
            ff(["-ss", ts(t), "-i", a.input, "-frames:v", 1, out / f"t{ts(t):07.2f}.png"])
    else:
        ff(["-i", a.input, "-vf", f"fps=1/{a.every}", out / "frame-%03d.png"])
    print(out)


def cmd_sheet(a):
    i = info(a.input)
    n = a.cols * a.rows
    step = i["duration"] / (n + 1)
    tw = a.width // a.cols
    m = brand()
    font = brand_font_file(m, "mono", "400")
    draw = (f",drawtext=text='%{{pts\\:hms}}':x=8:y=h-th-8:fontsize={max(14, tw // 18)}:fontcolor=white:"
            f"box=1:boxcolor=black@0.55:boxborderw=6" + (f":fontfile='{esc_filter_path(font)}'" if font else "")
            if has_filter("drawtext") else "")
    vf = f"fps=1/{step},scale={tw}:-1{draw},tile={a.cols}x{a.rows}:padding=6:margin=6:color=white"
    ff(["-i", a.input, "-vf", vf, "-frames:v", 1, a.output])


def cmd_compress(a):
    h, crf, ab = PRESETS[a.preset]
    i = info(a.input)
    h = min(h, i.get("height") or h)
    args = ["-i", a.input, "-vf", f"scale=-2:{h}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "slow",
            "-movflags", "+faststart", "-c:a", "aac", "-b:a", f"{ab}k"]
    if a.max_mb:  # bitrate budget for a size cap
        kbps = max(200, int(a.max_mb * 8000 / max(i["duration"], 1) * 0.95) - ab)
        args += ["-b:v", f"{kbps}k", "-maxrate", f"{kbps * 1.4:.0f}k", "-bufsize", f"{kbps * 2}k"]
    else:
        args += ["-crf", crf]
    ff(args + [a.output])
    if not DRY:
        print(f"{a.output}  {os.path.getsize(a.output) / 1e6:.2f} MB (from {i['size_mb']} MB)")


def cmd_stills(a):
    w, h = map(int, a.size.split("x"))
    fps, sec, fade = 30, a.seconds, a.fade
    frames = int(sec * fps)
    inputs, chains = [], []
    for k, img in enumerate(a.images):
        inputs += ["-i", img]  # one frame; zoompan emits `frames` frames from it
        chains.append(f"[{k}:v]scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase,crop={w * 2}:{h * 2},"
                      f"zoompan=z='min(zoom+{(a.zoom - 1) / frames:.6f},{a.zoom})':d={frames}:x='iw/2-(iw/zoom/2)':"
                      f"y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps},setsar=1,format=yuv420p[s{k}]")
    last, offset = "[s0]", sec - fade
    for k in range(1, len(a.images)):
        chains.append(f"{last}[s{k}]xfade=transition=fade:duration={fade}:offset={offset:.3f}[x{k}]")
        last, offset = f"[x{k}]", offset + sec - fade
    args = inputs + ["-filter_complex", ";".join(chains), "-map", last]
    if a.audio:
        args = args[:0] + inputs + ["-i", a.audio, "-filter_complex", ";".join(chains), "-map", last,
                                    "-map", f"{len(a.images)}:a", "-shortest"]
    ff(args + video_codec(a.output) + [a.output])


def cmd_audiogram(a):
    m = cutroom_brand.load(a.brand) if a.brand else brand()
    c = m["colors"] if m else {"deep": "#121A3A", "accent": "#FF6B4A", "on_deep": "#FFFFFF", "accent_soft": "#A9B4FF"}
    aw, ah = ASPECTS[a.aspect]
    H = 1080 if aw >= ah else 1920
    W = int(round(H * aw / ah / 2) * 2)
    dur = info(a.audio)["duration"]
    wave_h = H // 4
    fc = (f"color=c={ffcolor(c['deep'])}:s={W}x{H}:d={dur}[bg];"
          f"[0:a]aformat=channel_layouts=mono,showwaves=s={int(W * 0.8)}x{wave_h}:mode=cline:rate=30:scale=cbrt:draw=full:"
          f"colors={ffcolor(c['accent'])},format=rgba[w];[bg][w]overlay=(W-w)/2:(H-h)/2+{H // 10}")
    with tempfile.TemporaryDirectory() as t:
        disp = m["fonts"]["display"] if m else "sans-serif"
        logo = (Path(m["dir"]) / m["logos"]["on_deep"]).as_uri() if m and m["logos"].get("on_deep") else ""
        title = html_escape(a.title or "")
        png = text_pngs([("title", f'<div style="font:600 {int(W / 15)}px/1.12 \'{disp}\',sans-serif;color:{c["on_deep"]};'
                                   f'letter-spacing:-.02em">{title}</div>'
                                   + (f'<img src="{logo}" style="height:{int(W / 22)}px;margin-top:{int(W / 18)}px">' if logo else ""),
                          f"left:{int(W * .1)}px;top:{int(H * .14)}px;width:{int(W * .8)}px")], W, H, t, m)[0]
        fc += "[wv];[wv][1:v]overlay=0:0[v]"
        ff(["-i", a.audio, "-i", png, "-filter_complex", fc, "-map", "[v]", "-map", "0:a", "-r", 30] + video_codec(a.output)
           + ["-shortest", a.output])


def cmd_silences(a):
    need()
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", a.input, "-af", f"silencedetect=noise={a.db}dB:d={a.min}",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    pauses = [{"start": round(s, 3), "end": round(e, 3), "mid": round((s + e) / 2, 3)} for s, e in zip(starts, ends)]
    total = info(a.input)["duration"]
    if a.json:
        print(json.dumps({"duration": total, "pauses": pauses}, indent=2))
    else:
        for p in pauses:
            print(f"{p['start']:8.2f} – {p['end']:8.2f}   cut at {p['mid']:.2f}")
        print(f"duration {total:.2f} s · {len(pauses)} pauses")


def cmd_extract_audio(a):
    ff(["-i", a.input, "-vn"] + audio_codec(a.output) + [a.output])


SFX_RENDER_PY = r"""
import json, math, os, sys
import numpy as np
import soundfile as sf
from earshot.forge import bank

cfg = json.loads(sys.argv[1])
cues_doc = json.load(open(cfg["cues"], encoding="utf-8"))
cues = cues_doc["cues"] if isinstance(cues_doc, dict) and "cues" in cues_doc else cues_doc
sr = 48000
dur = float(cfg["duration"])
master_db = float(cfg.get("master_db", 0.0))
buf = np.zeros((max(1, int(round(dur * sr))), 2), dtype=np.float64)
PEAK_CATS = {"whoosh_fast", "whoosh_big", "pro_whoosh_big", "swish", "swipe", "reverse_swell", "pro_zip"}
END_CATS = {"riser", "pro_riser", "pro_glitch"}
rows = []

for idx, c in enumerate(cues):
    t_raw = c.get("time", c.get("t", 0.0))
    if isinstance(t_raw, str):
        parts = [float(p) for p in t_raw.split(":")]
        t = sum(p * (60 ** i) for i, p in enumerate(reversed(parts)))
    else:
        t = float(t_raw)
    sid = c.get("sound") or c.get("id")
    if not sid:
        continue
    seed_off = c.get("seed")
    if os.path.isfile(str(sid)):
        y, file_sr = sf.read(str(sid), always_2d=False)
        if file_sr != sr:
            import soxr
            y = soxr.resample(np.asarray(y, np.float32), file_sr, sr)
        y = bank.normalize(np.asarray(y, np.float32), -6.0).astype(np.float32)
        meta = {"id": sid, **bank.measure(y, sr), "category": "file", "checks": {"ok": True, "warnings": []}}
    else:
        e = bank.get(sid)
        seed = (int(e["seed"]) + int(seed_off)) if seed_off is not None else None
        y, meta = bank.render(
            e,
            seed=seed,
            dur=c.get("dur"),
            apex=c.get("apex"),
            pitch=c.get("pitch"),
            peak_db=-6.0,
            sr=sr,
            checks=True,
        )
        meta["category"] = e.get("category", "")
    align = c.get("align")
    if not align:
        cat = meta.get("category", "")
        align = "peak" if cat in PEAK_CATS else ("end" if cat in END_CATS else "onset")
    anchor_s = (
        meta["peak_s"] if align == "peak"
        else meta["end_s"] if align == "end"
        else meta["onset_s"] if align == "onset"
        else 0.0
    )
    gain_db = float(c.get("gain_db", -12.0)) + master_db
    if "peak_db" in c:
        gain_db = (float(c["peak_db"]) - (-6.0)) + master_db
    gain = 10.0 ** (gain_db / 20.0)
    arr = np.asarray(y, dtype=np.float64) * gain
    if arr.ndim == 1:
        pan = max(-1.0, min(1.0, float(c.get("pan", 0.0))))
        angle = (pan + 1.0) * (math.pi / 4.0)
        arr = np.column_stack([arr * math.cos(angle), arr * math.sin(angle)])
    start = int(round((t - anchor_s) * sr))
    s0 = max(0, start)
    a0 = max(0, -start)
    n = min(len(buf) - s0, len(arr) - a0)
    if n > 0:
        buf[s0:s0 + n] += arr[a0:a0 + n]
    warns = [w["code"] for w in (meta.get("checks") or {}).get("warnings", [])]
    rows.append({
        "index": idx + 1,
        "time": round(t, 3),
        "sound": sid,
        "align": align,
        "anchor_ms": round(anchor_s * 1000, 1),
        "dur_s": meta["dur_s"],
        "peak_dbfs": round(-6.0 + gain_db, 1),
        "warnings": warns,
        "note": c.get("note") or c.get("label") or "",
    })

peak = float(np.abs(buf).max()) if len(buf) else 0.0
limit = 10.0 ** (-1.0 / 20.0)
if peak > limit:
    buf = np.tanh(buf / limit) * limit
sf.write(cfg["stem"], buf.astype(np.float32), sr, subtype="PCM_24")
for r in rows:
    w = f" !{','.join(r['warnings'])}" if r["warnings"] else ""
    note = f"  ({r['note']})" if r["note"] else ""
    print(f"  {r['time']:6.2f}s  {r['sound']:<30} align={r['align']:<5} ({r['anchor_ms']:5.1f}ms)  {r['peak_dbfs']:+5.1f} dBFS{w}{note}")
print(f"✓ rendered {len(rows)} cues → {cfg['stem']} ({dur:.2f}s, peak {20*math.log10(max(peak, 1e-9)):.1f} dBFS)")
"""


def cmd_sfx(a):
    import cutroom_home
    home = cutroom_home.home()
    sound_py = str(cutroom_home.env_bin(home, "sound", "python"))
    if not os.path.exists(sound_py):
        raise SystemExit("sound component is not installed: run `cutroom setup sound --yes`")
    dur = float(a.duration) if a.duration else info(a.input)["duration"]
    with tempfile.TemporaryDirectory() as t:
        stem = str(Path(a.stem).resolve()) if a.stem else str(Path(t) / "sfx-stem.wav")
        Path(stem).parent.mkdir(parents=True, exist_ok=True)
        cfg = json.dumps({"cues": str(Path(a.cues).resolve()), "duration": dur, "stem": stem, "master_db": a.master_db})
        print(f"$ earshot render cues ({a.cues})", flush=True)
        if not DRY:
            r = subprocess.run([sound_py, "-c", SFX_RENDER_PY, cfg], text=True)
            if r.returncode != 0:
                raise SystemExit(f"sfx cue render failed ({r.returncode})")
        if a.stem_only:
            if not a.stem:
                shutil.copy2(stem, a.output)
            return
        if is_audio_only(a.input):
            fc = "[0:a]aresample=48000,aformat=channel_layouts=stereo[base];[1:a]aresample=48000,aformat=channel_layouts=stereo[sfx];[base][sfx]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,alimiter=limit=0.891:level=disabled[out]"
            ff(["-i", a.input, "-i", stem, "-filter_complex", fc, "-map", "[out]"] + audio_codec(a.output) + [a.output])
        elif has_audio(a.input):
            fc = "[0:a]aresample=48000,aformat=channel_layouts=stereo[base];[1:a]aresample=48000,aformat=channel_layouts=stereo[sfx];[base][sfx]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,alimiter=limit=0.891:level=disabled[out]"
            ff(["-i", a.input, "-i", stem, "-filter_complex", fc, "-map", "0:v", "-map", "[out]", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.output])
        else:
            ff(["-i", a.input, "-i", stem, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.output])


def main(argv=None):
    global DRY
    ap = argparse.ArgumentParser(prog="cutroom edit", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def p(name, fn, *pos):
        s = sub.add_parser(name)
        for x in pos:
            s.add_argument(x, nargs="+" if x in ("inputs", "images") else None)
        s.set_defaults(fn=fn)
        return s
    s = p("probe", cmd_probe, "file"); s.add_argument("--json", action="store_true")
    s = p("trim", cmd_trim, "input"); s.add_argument("-o", "--output", required=True); s.add_argument("--start")
    s.add_argument("--end"); s.add_argument("--duration"); s.add_argument("--copy", action="store_true")
    s = p("concat", cmd_concat, "inputs"); s.add_argument("-o", "--output", required=True); s.add_argument("--size")
    s.add_argument("--fps", type=float); s.add_argument("--gap", type=float, default=0)
    s = p("mix", cmd_mix); s.add_argument("--voice", required=True); s.add_argument("--music")
    s.add_argument("-o", "--output", required=True); s.add_argument("--music-db", type=float, default=-20)
    s.add_argument("--duck", action="store_true"); s.add_argument("--fade", type=float, default=1.5)
    s.add_argument("--tail", type=float, default=1.0)
    s = p("score", cmd_score, "video"); s.add_argument("-o", "--output", required=True); s.add_argument("--voice")
    s.add_argument("--music"); s.add_argument("--duck", action="store_true"); s.add_argument("--music-db", type=float, default=-20)
    s.add_argument("--fade", type=float, default=1.5); s.add_argument("--offset", type=float, default=0)
    s = p("sfx", cmd_sfx, "input"); s.add_argument("--cues", required=True, help="JSON file of timed earshot cues")
    s.add_argument("-o", "--output", required=True); s.add_argument("--stem", help="also save the rendered stereo SFX stem WAV")
    s.add_argument("--stem-only", action="store_true", help="only write the SFX stem WAV without muxing")
    s.add_argument("--duration", type=float, help="override duration in seconds (for --stem-only)")
    s.add_argument("--master-db", type=float, default=0.0, help="master gain offset in dB for all cues")
    s = p("loudnorm", cmd_loudnorm, "input"); s.add_argument("-o", "--output", required=True)
    s.add_argument("--target", type=float, default=-16)
    s = p("captions", cmd_captions, "video", "subs"); s.add_argument("-o", "--output", required=True)
    s.add_argument("--brand"); s.add_argument("--size", type=int, default=46); s.add_argument("--margin", type=int, default=70)
    s.add_argument("--position", choices=["bottom", "top"], default="bottom")
    s.add_argument("--html", action="store_true", help="render cues in Chrome even when ffmpeg has libass")
    s = p("reframe", cmd_reframe, "input"); s.add_argument("-o", "--output", required=True)
    s.add_argument("--aspect", required=True); s.add_argument("--mode", choices=["blur", "crop", "pad"], default="blur")
    s.add_argument("--height", type=int)
    s = p("watermark", cmd_watermark, "input"); s.add_argument("-o", "--output", required=True); s.add_argument("--logo")
    s.add_argument("--on", choices=["dark", "light"], default="dark", help="background under the logo (picks the brand logo)")
    s.add_argument("--corner", choices=["br", "bl", "tr", "tl"], default="br"); s.add_argument("--width", type=float, default=0.12)
    s.add_argument("--margin", type=float, default=0.04)
    s = p("gif", cmd_gif, "input"); s.add_argument("-o", "--output", required=True); s.add_argument("--start", type=float, default=0)
    s.add_argument("--duration", type=float, default=6); s.add_argument("--fps", type=int, default=12)
    s.add_argument("--width", type=int, default=720)
    s = p("frames", cmd_frames, "input"); s.add_argument("-o", "--output", required=True)
    s.add_argument("--every", type=float, default=2); s.add_argument("--at")
    s = p("sheet", cmd_sheet, "input"); s.add_argument("-o", "--output", required=True)
    s.add_argument("--cols", type=int, default=4); s.add_argument("--rows", type=int, default=3); s.add_argument("--width", type=int, default=1600)
    s = p("compress", cmd_compress, "input"); s.add_argument("-o", "--output", required=True)
    s.add_argument("--preset", choices=list(PRESETS), default="web"); s.add_argument("--max-mb", type=float)
    s = p("stills", cmd_stills, "images"); s.add_argument("-o", "--output", required=True)
    s.add_argument("--seconds", type=float, default=4); s.add_argument("--size", default="1920x1080")
    s.add_argument("--zoom", type=float, default=1.08); s.add_argument("--audio"); s.add_argument("--fade", type=float, default=0.6)
    s = p("audiogram", cmd_audiogram, "audio"); s.add_argument("-o", "--output", required=True); s.add_argument("--title")
    s.add_argument("--aspect", choices=["1:1", "9:16", "16:9"], default="1:1"); s.add_argument("--brand")
    s = p("silences", cmd_silences, "input"); s.add_argument("--db", type=float, default=-38)
    s.add_argument("--min", type=float, default=0.12); s.add_argument("--json", action="store_true")
    s = p("extract-audio", cmd_extract_audio, "input"); s.add_argument("-o", "--output", required=True)
    a = ap.parse_args(argv)
    DRY = a.dry_run
    a.fn(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
