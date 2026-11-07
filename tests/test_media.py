from PIL import Image

from portfolio_site.content import parse_project
from portfolio_site.media import is_animated, poster_frame, process, video_command, write_poster


def project(media):
    return parse_project(
        {
            "repo": "demo",
            "title": "T",
            "area": "A",
            "size": "small",
            "summary": "S",
            "metric": "1",
            "metric_label": "L",
            "caveat": "C",
            "tags": [],
            "media": media,
        }
    )


def gif(path, colours=((255, 0, 0), (0, 255, 0), (0, 0, 255))):
    frames = [Image.new("RGB", (40, 20), colour) for colour in colours]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=100, loop=0)


def test_poster_uses_the_middle_frame(tmp_path):
    path = tmp_path / "a.gif"
    gif(path)
    with Image.open(path) as image:
        red, green, blue = poster_frame(image).getpixel((5, 5))
    assert green > red and green > blue


def test_poster_position_selects_the_frame(tmp_path):
    path = tmp_path / "a.gif"
    gif(path)
    with Image.open(path) as image:
        red, _, blue = poster_frame(image, 0.0).getpixel((5, 5))
        assert red > blue
        red, _, blue = poster_frame(image, 1.0).getpixel((5, 5))
        assert blue > red


def test_poster_downscales_but_never_upscales(tmp_path):
    source = tmp_path / "a.png"
    Image.new("RGB", (200, 100), "white").save(source)
    assert write_poster(source, tmp_path / "small.webp", width=100) == (100, 50)
    assert write_poster(source, tmp_path / "same.webp", width=400) == (200, 100)


def test_detects_animation(tmp_path):
    animated, still = tmp_path / "a.gif", tmp_path / "b.png"
    gif(animated)
    Image.new("RGB", (4, 4)).save(still)
    assert is_animated(animated)
    assert not is_animated(still)


def test_video_is_browser_safe(tmp_path):
    command = video_command(tmp_path / "a.gif", tmp_path / "a.mp4")
    assert command[command.index("-pix_fmt") + 1] == "yuv420p"
    assert "+faststart" in command


def test_still_image_gets_a_poster_only(tmp_path):
    (tmp_path / "demo").mkdir()
    Image.new("RGB", (30, 30)).save(tmp_path / "demo" / "a.png")
    created = process(project({"source": "a.png", "alt": "x"}), tmp_path, tmp_path)
    assert [path.name for path in created] == ["demo.webp"]


def test_project_without_media_is_skipped(tmp_path):
    assert process(project(None), tmp_path, tmp_path) == []
