"""Turn each project's demo media into small web files.

Source GIFs are 2 to 5 MB each, too heavy for one page with twelve cards. Every project gets
a WebP poster, and animated sources also get a short H.264 clip that only loads on hover.
Outputs are committed, so the site build needs neither the project clones nor ffmpeg.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

from portfolio_site.content import Project, load_projects

POSTER_WIDTH = 960
VIDEO_WIDTH = 720
VIDEO_CRF = 30


def poster_frame(image: Image.Image, position: float = 0.5) -> Image.Image:
    """Pick a frame of an animation by relative position, 0 being the first frame."""
    if getattr(image, "is_animated", False):
        image.seek(min(int(image.n_frames * position), image.n_frames - 1))
    return image.convert("RGB")


def write_poster(
    source: Path, target: Path, width: int = POSTER_WIDTH, position: float = 0.5
) -> tuple[int, int]:
    with Image.open(source) as image:
        frame = poster_frame(image, position)
    if frame.width > width:
        frame = frame.resize((width, round(frame.height * width / frame.width)), Image.LANCZOS)
    frame.save(target, "WEBP", quality=78, method=6)
    return frame.size


def is_animated(source: Path) -> bool:
    with Image.open(source) as image:
        return bool(getattr(image, "is_animated", False))


def video_command(source: Path, target: Path) -> list[str]:
    scale = f"scale='min({VIDEO_WIDTH},iw)':-2:flags=lanczos"
    return [
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
        "-vf", scale, "-an", "-c:v", "libx264", "-preset", "slow", "-crf", str(VIDEO_CRF),
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target),
    ]  # fmt: skip


def process(project: Project, repos_dir: Path, out_dir: Path) -> list[Path]:
    """Write the media of one project and return the files created."""
    if project.media is None:
        return []
    source = repos_dir / project.repo / project.media.source
    poster = out_dir / f"{project.repo}.webp"
    write_poster(source, poster, position=project.media.frame)
    created = [poster]
    if is_animated(source):
        video = out_dir / f"{project.repo}.mp4"
        subprocess.run(video_command(source, video), check=True)
        created.append(video)
    return created


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--content", type=Path, default=Path("content/projects.yaml"))
    parser.add_argument("--repos-dir", type=Path, default=Path(".."))
    parser.add_argument("--out", type=Path, default=Path("static/media"))
    args = parser.parse_args(argv)

    if shutil.which("ffmpeg") is None:
        print("ffmpeg is required to convert GIFs")
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    for project in load_projects(args.content):
        for path in process(project, args.repos_dir, args.out):
            print(f"{path}  {path.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
