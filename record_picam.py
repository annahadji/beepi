"""Small script saving video recordings using Picamera."""
import argparse
import ctypes as ct
import datetime
import logging
import math
import pathlib
import shutil
import subprocess
import time
from typing import Generator, Dict, Any

import picamera
from picamera import mmal
import brightpi

logger = logging.getLogger("BeePi")
logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(name)s: %(message)s",
    datefmt="%d.%m.%y %H:%M:%S",
    level=logging.INFO,
)

WRITE_TO_USB_AFTER = 8.0  # Try to write to usb after accumulating this many gb of data
LEAVE_SPARE_ON_PI = 6.0  # Make sure to leave this many spare gb on filesystem
BYTES_PER_GB = 1024 * 1024 * 1024

def record_n_segments(n: int, seconds: int, iteration: int) -> None:
    """Record n segments of footage of a particular duration (in seconds).
    Iteration parameter is used in naming."""
    start_rec = pathlib.Path("/home/pi/picam/hooks/start_record")
    stop_rec = pathlib.Path("/home/pi/picam/hooks/stop_record")
    for segment in range(n):
        filename = f"{iteration}-{segment}-{datetime.datetime.now().strftime('%d%m%y-%H%M')}.ts"
        with start_rec.open("w") as f:
            f.write(f"filename={filename}")
        time.sleep(seconds)
        stop_rec.touch()
        logger.info("Video saved, %s.", filename)
        time.sleep(1)
        
def convert_to_mp4(
    ts_file, remove_orig: bool = False
) -> None:
    """Convert videos in a directory to grayscale. Converted videos will be saved
    to same path with 'gry-' prefix and original videos can optionally be removed.

    Exceptions raised:
        CalledProcessError: raised if ffmpeg doesnt successfully convert a file.
    """
    new_path = ts_file.parent / (ts_file.stem + ".mp4")
    subprocess.run(
        ["ffmpeg", "-i", ts_file, "-c:v", "copy", "-c:a", "copy", "-bsf:a", "aac_adtstoasc", str(new_path)], check=True
    )
    logger.info("Converted and saved %s.", str(ts_file))
    if remove_orig:
        ts_file.unlink()
        logger.info("Deleted %s.", str(ts_file))


def write_to_usb(data_path: pathlib.Path, usb_path: pathlib.Path) -> None:
    """Write all .h264 video files in data dir to path on usb, and remove original files."""
    for video_path in data_path.glob("*.mp4"):
        target_path = usb_path / "data" / video_path.name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(video_path, target_path)
        video_path.unlink()

def test_setup(args: Dict[str, Any]):
    """Change arguments to test the setup."""
    args["experiment_name"] = "test"
    args["segment_length"] = 3  # seconds
    args["session_length"] = 7  # seconds
    args["fps"] = 60
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
        default=400,
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
    assert (args["segment_length"] < args["session_length"]), "Seg len > session len."
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
        brightPi.set_led_on_off(brightpi.LED_IR, brightpi.ON)
        leds_indices_on = brightPi.get_led_on_off(brightpi.LED_IR)
        logger.info("BrightPi setup, IR leds ON: %s", str(leds_indices_on))
    # ------------------------
    # Recording loop
    n_segments = 5
    num_iterations = max(
        1, int(math.ceil(args["session_length"] / (n_segments * args["segment_length"])))
    )
    space_on_usb = True
    for recording_iter in range(num_iterations):
        logger.info("--------")
        logger.info("Recording loop %d / %d.", recording_iter + 1, num_iterations)
        # ---
        # Record n segments of footage for certain duration
        camera_proc = subprocess.Popen(["./picam", "--alsadev", "hw:1,0",
                                        "--width", "640",
                                        "--height", "480",
                                        "--fps", "60",
                                        "--mode", "6",
                                        "--hflip",
                                        "--wb", "greyworld",
                                        "--iso", "800"], cwd="/home/pi/picam")
        time.sleep(2)  # Camera warmup
        logger.info("About to start recording %d segments...", n_segments)
        record_n_segments(
            n=n_segments,
            seconds=args["segment_length"],
            iteration=recording_iter  # Passed for naming
        )
        logger.info("Recording finished.")
        camera_proc.terminate()
        time.sleep(2)
        # ---
        # Convert from .ts to .mp4
        ts_files_save_archive_path = pathlib.Path("/home/pi/picam/archive")
        ts_files_save_rec_path = pathlib.Path("/home/pi/picam/rec")
        for filename in ts_files_save_archive_path.glob("*.ts"):
            convert_to_mp4(filename, remove_orig=True)
            (ts_files_save_rec_path / filename.name).unlink()
        # ---
        # Reset lighting conditions
        if args["ir"]:
            brightPi.reset()
            leds_indices_on = brightPi.get_led_on_off(brightpi.LED_IR)
            logger.info("BrightPi reset, IR leds ON: %s", str(leds_indices_on))
        # ---
        # Check available space in filesystem
        space = shutil.disk_usage(ts_files_save_archive_path)  # Returns total, used and free bytes
        total = float(space.total) / BYTES_PER_GB
        used = float(space.used) / BYTES_PER_GB
        logger.info("Filesystem usage %.2fgb / %.2fgb." % (used, total))
        if used > WRITE_TO_USB_AFTER and space_on_usb:
            # ---
            # Check available space in USB
            usb_path = pathlib.Path("/home/pi/usbstick")
            usb_space = shutil.disk_usage(usb_path)
            usb_total = float(usb_space.total) / BYTES_PER_GB
            usb_used = float(usb_space.used) / BYTES_PER_GB
            usb_free = float(usb_space.free) / BYTES_PER_GB
            logger.info("USB usage %.2fgb / %.2fgb." % (usb_used, usb_total))
            if used > usb_free:
                space_on_usb = False
                logger.info("USB storage will be exceeded by next write. Next write cancelled.")
                break
            # ---
            # Write to USB
            logger.info("Moving .mp4 files in %s to %s...", str(ts_files_save_archive_path), str(usb_path))
            write_to_usb(ts_files_save_archive_path, usb_path)
            used = float(shutil.disk_usage(ts_files_save_archive_path).used) / BYTES_PER_GB
            logger.info("Files moved. Filesystem usage now: %.2fgb." % (used))
        # ---
        # Break out of loop if space is exceeded
        if (total - used) < LEAVE_SPARE_ON_PI:
            logger.info("Terminating program at loop %d due to space constraints.", recording_iter)
            break
