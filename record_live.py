"""Small script saving video recordings using Picamera."""
import argparse
import ctypes as ct
import datetime
import logging
import pathlib
import shutil
import subprocess
from typing import Generator, Dict, Any

import picamera
from picamera import mmal
import brightpi

logger = logging.getLogger("Pi")
logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(name)s: %(message)s",
    datefmt="%d.%m.%y %H:%M:%S",
    level=logging.INFO,
)

BYTES_PER_GB = 1024 * 1024 * 1024


class PiCameraGs(picamera.PiCamera):
    """Greyworld is not yet an option for picamera, as it is in raspvid.
    It helps fix incorrect colours induced by the removal of the IR filter."""

    AWB_MODES = {
        "off": mmal.MMAL_PARAM_AWBMODE_OFF,
        "auto": mmal.MMAL_PARAM_AWBMODE_AUTO,
        "sunlight": mmal.MMAL_PARAM_AWBMODE_SUNLIGHT,
        "cloudy": mmal.MMAL_PARAM_AWBMODE_CLOUDY,
        "shade": mmal.MMAL_PARAM_AWBMODE_SHADE,
        "tungsten": mmal.MMAL_PARAM_AWBMODE_TUNGSTEN,
        "fluorescent": mmal.MMAL_PARAM_AWBMODE_FLUORESCENT,
        "incandescent": mmal.MMAL_PARAM_AWBMODE_INCANDESCENT,
        "flash": mmal.MMAL_PARAM_AWBMODE_FLASH,
        "horizon": mmal.MMAL_PARAM_AWBMODE_HORIZON,
        "greyworld": ct.c_uint32(10),
    }


def record_n_segments(
    n: int, seconds: int, camera: picamera.PiCamera, save_dir: pathlib.Path
) -> None:
    """Record n segments of footage of a particular duration (in seconds)."""
    info_str = f"-{camera.framerate}fps-"
    for filename in camera.record_sequence(
        "%s.h264"
        % (
            save_dir
            / (str(i) + info_str + f"{datetime.datetime.now().strftime('%d%m%y-%H%M')}")
        )
        for i in range(0, n)
    ):
        camera.wait_recording(seconds)
        logger.info("Video saved, %s.", filename)


def convert_to_greyscale(
    video_dir: Generator[pathlib.PosixPath, None, None], remove_orig: bool = False
) -> None:
    """Convert videos in a directory to grayscale. Converted videos will be saved
    to same path with 'gry-' prefix and original videos can optionally be removed.

    Exceptions raised:
        CalledProcessError: raised if ffmpeg doesnt successfully convert a file.
    """
    for file in video_dir:
        new_path = file.parent / ("gry-" + file.stem + file.suffix)
        subprocess.run(
            ["ffmpeg", "-i", file, "-vf", "format=gray", new_path], check=True
        )
        logger.info("%s converted, saved as %s.", file.stem, new_path.stem)
        if remove_orig:
            file.unlink()
            logger.info("Deleted %s.", file.stem)


def test_setup(args: Dict[str, Any]):
    """Change arguments to test the setup."""
    args["experiment_name"] = "test"
    args["segment_length"] = 3  # seconds
    args["session_length"] = 6  # seconds
    args["ir"] = True


if __name__ == "__main__":

    logger.info("------------------------------")
    # ------------------------
    # Parse Arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--experiment_name",
        type=str,
        default=datetime.datetime.now().strftime("%Y%m%d-%H%M"),
        help="Name for experimental run.",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=60,
        help="Frames per second to record in.",
    )
    parser.add_argument(
        "--segment_length",
        type=int,
        default=120,
        help="Length of an individual video segment (in seconds).",
    )
    parser.add_argument(
        "--session_length",
        type=int,
        default=24,
        help="Desired length of resulting footage (in seconds). \
        i.e. 21600 - 6hrs, 28800 - 8hrs, 43200 - 12hrs, 64800 - 18hrs, 86400 - 24hrs.",
    )
    parser.add_argument(
        "--ir",
        action="store_true",
        help="Use infrared lighting when recording.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run a small test, mostly ignores other arguments.",
    )
    args = vars(parser.parse_args())
    # Setup test arguments if debug
    if args["debug"]:
        test_setup(args)
    assert (
        args["segment_length"] < args["session_length"]
    ), "Segment length exceeds total session time."
    logger.info("Running with args: %s", str(args))
    # ------------------------
    # Set up lighting conditions
    if args["ir"]:
        # ---
        # Set up and initialise BrightPi
        brightPi = brightpi.BrightPi()
        brightPi.reset()
        # ---
        # Turn on IR LEDs
        brightPi.set_led_on_off(brightpi.LED_IR, brightpi.OFF)
        leds_indices_on = brightPi.get_led_on_off(brightpi.LED_IR)
        logger.info("BrightPi setup, IR leds ON: %s", str(leds_indices_on))
    # ------------------------
    # Set up camera
    camera = PiCameraGs(resolution=(640, 480), framerate=args["fps"])
    # camera.vflip = True
    camera.hflip = True  # To mirror real image
    camera.exposure_mode = "night"
    camera.ISO = 800
    camera.awb_mode = "greyworld"
    logger.info(
        "Camera setup -fps %d -ex %s -ISO %d -h %d -w %d.",
        camera.framerate,
        camera.exposure_mode,
        camera.ISO,
        camera.resolution.height,
        camera.resolution.width,
    )
    # ------------------------
    # Recording loop
    n_segments = 5
    num_iterations = int(
        round(args["session_length"] / (n_segments * args["segment_length"]))
    )
    for recording_iter in range(num_iterations):
        logger.info("--------\nRecording loop %d / %d.", recording_iter, num_iterations)
        # ---
        # Set up save dir
        outputs = pathlib.Path("data", args["experiment_name"])
        save_dir = outputs / str(recording_iter)
        save_dir.mkdir(parents=True, exist_ok=True)
        # ---
        # Record n segments of footage for certain duration before checking storage
        logger.info("About to start recording %d segments...", n_segments)
        record_n_segments(
            n=n_segments,
            seconds=args["segment_length"],
            camera=camera,
            save_dir=save_dir,
        )
        logger.info("Recording finished.")
        # ---
        # Reset lighting conditions
        if args["ir"]:
            # ---
            # Reset BrightPi
            brightPi.reset()
            leds_indices_on = brightPi.get_led_on_off(brightpi.LED_IR)
            logger.info("BrightPi reset, IR leds ON: %s", str(leds_indices_on))
        # ---
        # Check available space in filesystem
        space = shutil.disk_usage(outputs)  # Returns total, used and free bytes
        total, used = float(space.total) / BYTES_PER_GB
        used = float(space.used) / BYTES_PER_GB
        logger.info("Used %.2fgb / %.2fgb." % total, used)
        if used > 10.0:  # i.e. filesystem is over 10gb
            # Write to extra USB space
            logger.info("Writing footage so far to connected USB...")
            pass
            logger.info("Written to USB and deleted.")

        # Convert videos to greyscale and delete originals to save space
        # logger.info("Converting to greyscale...")
        # convert_to_greyscale(save_dir.glob("*"), remove_orig=True)
        # logger.info("Finished conversions.")
