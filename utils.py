"""Util functions to video processing."""
import logging
import pathlib
import subprocess

logger = logging.getLogger("BeePi")
logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(name)s: %(message)s",
    datefmt="%d.%m.%y %H:%M:%S",
    level=logging.INFO,
)


def convert_to_greyscale(video_dir: pathlib.Path, remove_orig: bool = False) -> None:
    """Convert videos in a directory to grayscale. Converted videos will be saved
    to same path with 'gry-' prefix and original videos can optionally be removed.

    Exceptions raised:
        CalledProcessError: raised if ffmpeg doesnt successfully convert a file.
    """
    for file in video_dir.glob("*.h264"):
        new_path = file.parent / ("gry-" + file.stem + file.suffix)
        subprocess.run(
            ["ffmpeg", "-i", file, "-vf", "format=gray", new_path], check=True
        )
        logger.info("%s converted, saved as %s.", file.stem, new_path.stem)
        if remove_orig:
            file.unlink()
            logger.info("Deleted %s.", file.stem)
