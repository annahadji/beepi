"""Utils/equivalent functions for using Picamera instead of picam."""
import ctypes as ct
import datetime
import logging
import pathlib
import shutil
import subprocess

import picamera

logger = logging.getLogger("BeePi")
logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(name)s: %(message)s",
    datefmt="%d.%m.%y %H:%M:%S",
    level=logging.INFO,
)


class PiCameraGs(picamera.PiCamera):
    """Greyworld is not yet an option for picamera, as it is in raspvid.
    It helps fix incorrect colours induced by the removal of the IR filter."""

    AWB_MODES = {
        "greyworld": ct.c_uint32(10),
    }


def record_n_segments(
    num_segs: int,
    seconds: int,
    name: str,
    camera: picamera.PiCamera,
    save_dir: pathlib.Path,
) -> None:
    """Record n segments of footage of a particular duration (in seconds)."""
    for filename in camera.record_sequence(
        "%s.h264"
        % (
            save_dir
            / f"{datetime.datetime.now().strftime('%y%m%d-%H%M%S')}-sid{segment}-{name}"
        )
        for segment in range(0, num_segs)
    ):
        camera.wait_recording(seconds)
        logger.info("Video saved, %s.", filename)


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


# if __name__ == "__main__":

# # ------------------------
# # Set up picamera
# camera = PiCameraGs(resolution=(640, 480), framerate=args["fps"])
# # camera.vflip = True
# camera.hflip = True  # To mirror real image
# camera.exposure_mode = "night"
# camera.ISO = 800
# camera.awb_mode = "greyworld"
# logger.info(
#     "Camera setup -fps %d -ex %s -ISO %d -h %d -w %d.",
#     camera.framerate,
#     camera.exposure_mode,
#     camera.ISO,
#     camera.resolution.height,
#     camera.resolution.width,
# )
# ------------------------
