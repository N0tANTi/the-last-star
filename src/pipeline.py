"""Master Blender Python pipeline for 'The Last Star' — preview keyframes or render full 59s MP4."""
import argparse
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import bpy
from shots import SHOT_SPECS, SHOT_BUILDERS
from sound import generate_soundtrack


def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    parser = argparse.ArgumentParser(description="The Last Star Blender Python Pipeline")
    parser.add_argument("--mode", choices=["preview", "render", "assemble"], default="preview")
    parser.add_argument("--shots", default="all", help="Comma-separated shot names or 'all'")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--fps", type=int, default=24)
    return parser.parse_args(argv)


def selected_specs(shots_arg):
    if shots_arg == "all":
        return list(SHOT_SPECS)
    wanted = {s.strip() for s in shots_arg.split(",") if s.strip()}
    return [sp for sp in SHOT_SPECS if sp[0] in wanted]


def render_previews(args):
    out_dir = os.path.join(PROJECT_ROOT, "output", "previews")
    os.makedirs(out_dir, exist_ok=True)
    specs = selected_specs(args.shots)
    t_all = time.time()
    for name, frames, preview_frame in specs:
        t0 = time.time()
        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = SHOT_BUILDERS[name](frames, args.width, args.height, args.samples)
        bpy.context.window.scene = sc
        sc.frame_set(preview_frame)
        out_path = os.path.join(out_dir, f"{name}.png")
        sc.render.filepath = out_path
        bpy.ops.render.render(write_still=True)
        print(f"[preview] {name} (f{preview_frame}/{frames}) -> {out_path} ({time.time() - t0:.2f}s)")
    print(f"[preview] All {len(specs)} previews completed in {time.time() - t_all:.1f}s")


def render_all_shots(args):
    frames_root = os.path.join(PROJECT_ROOT, "output", "frames")
    os.makedirs(frames_root, exist_ok=True)
    specs = selected_specs(args.shots)
    t_all = time.time()
    for name, frames, _ in specs:
        shot_dir = os.path.join(frames_root, name)
        os.makedirs(shot_dir, exist_ok=True)
        t0 = time.time()
        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = SHOT_BUILDERS[name](frames, args.width, args.height, args.samples)
        bpy.context.window.scene = sc
        sc.render.fps = args.fps
        sc.render.image_settings.file_format = "PNG"
        sc.render.filepath = os.path.join(shot_dir, "frame_")
        bpy.ops.render.render(animation=True)
        print(f"[render] {name} ({frames} frames) done in {time.time() - t0:.1f}s")
    print(f"[render] Shot rendering finished in {time.time() - t_all:.1f}s")


def assemble_video(args):
    """Use Blender 5.2 VSE + built-in FFmpeg to stitch all shot PNG sequences + stereo soundtrack into output/TheLastStar.mp4."""
    sound_path = os.path.join(PROJECT_ROOT, "output", "soundtrack.wav")
    generate_soundtrack(sound_path)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.data.scenes.new("Master_VSE")
    bpy.context.window.scene = sc
    sc.render.resolution_x = args.width
    sc.render.resolution_y = args.height
    sc.render.resolution_percentage = 100
    sc.render.fps = args.fps
    sc.view_settings.view_transform = "Standard"

    se = sc.sequence_editor_create()
    frames_root = os.path.join(PROJECT_ROOT, "output", "frames")

    cursor = 1
    for name, frames, _ in SHOT_SPECS:
        shot_dir = os.path.join(frames_root, name)
        pngs = sorted(f for f in os.listdir(shot_dir) if f.lower().endswith(".png"))
        if not pngs:
            raise RuntimeError(f"Missing rendered frames for shot {name} in {shot_dir}")
        strip = se.strips.new_image(
            name=name,
            filepath=os.path.join(shot_dir, pngs[0]),
            channel=2,
            frame_start=cursor,
        )
        for p in pngs[1:]:
            strip.elements.append(p)
        cursor += len(pngs)

    total_frames = cursor - 1
    sc.frame_start = 1
    sc.frame_end = total_frames

    # Add stereo soundtrack on channel 1
    se.strips.new_sound(name="Soundtrack", filepath=sound_path, channel=1, frame_start=1)

    # Configure Blender 5.2 FFmpeg H.264 + AAC output
    out_mp4 = os.path.join(PROJECT_ROOT, "output", "TheLastStar.mp4")
    if hasattr(sc.render.image_settings, "media_type"):
        sc.render.image_settings.media_type = "VIDEO"
    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"
    sc.render.ffmpeg.codec = "H264"
    sc.render.ffmpeg.constant_rate_factor = "HIGH"
    sc.render.ffmpeg.ffmpeg_preset = "GOOD"
    sc.render.ffmpeg.audio_codec = "AAC"
    sc.render.ffmpeg.audio_bitrate = 192
    sc.render.filepath = out_mp4

    t0 = time.time()
    bpy.ops.render.render(animation=True)
    print(f"[assemble] Exported {out_mp4} ({total_frames} frames @ {args.fps}fps) in {time.time() - t0:.1f}s")


def main():
    args = parse_args()
    if args.mode == "preview":
        render_previews(args)
    elif args.mode == "render":
        render_all_shots(args)
        assemble_video(args)
    elif args.mode == "assemble":
        assemble_video(args)


if __name__ == "__main__":
    main()
