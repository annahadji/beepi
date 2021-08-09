"""Record segments of video and audio using picam or picamera. Picam can provide audio
from a connected USB microphone; picamera can be used for higher resolution files
(e.g. 1640 x 922 and upwards)."""
import argparse
import ctypes
import datetime
import logging
import math
import pathlib
import shutil
import subprocess
import time
from typing import Dict, Any

# Import RaspPi picamera library (alternative 'picam' is setup locally already)
import picamera
from picamera import mmal

# Control infra red lights
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


class PiCameraGs(picamera.PiCamera):
    """Greyworld is not yet an option for picamera, as it is in raspvid.
    It helps fix incorrect colours induced by the removal of the IR filter."""

    AWB_MODES = {
        "auto": mmal.MMAL_PARAM_AWBMODE_AUTO,
        "greyworld": ctypes.c_uint32(10),
    }


def record_n_segments_picam(num_segs: int, seconds: int, name: str) -> None:
    """Record n segments of footage of a particular duration (in seconds) using picam.
    Saves video files with .ts extension."""
    start_rec = pathlib.Path("/home/pi/picam/hooks/start_record")
    stop_rec = pathlib.Path("/home/pi/picam/hooks/stop_record")
    for segment in range(num_segs):
        timestamp = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
        filename = f"{timestamp}-sid{segment}-{name}.ts"
        with start_rec.open("w") as file:
            file.write(f"filename={filename}")
        time.sleep(seconds)
        stop_rec.touch()
        if pathlib.Path("/home/pi/picam/archive", filename).exists():
            logger.info("Video saved, %s.", filename)
        else:
            logger.warning("Error recording video, %s.", filename)
        time.sleep(1)


def record_n_segments_picamera(
    num_segs: int,
    seconds: int,
    name: str,
    camera: picamera.PiCamera,
    save_dir: pathlib.Path,
) -> None:
    """Record n segments of footage of a particular duration (in seconds) using picamera.
    Saves video files with .h264 extension."""
    for filename in camera.record_sequence(
        "%s.h264"
        % (
            save_dir
            / f"{datetime.datetime.now().strftime('%y%m%d-%H%M%S')}-sid{segment}-{name}"
        )
        for segment in range(0, num_segs)
    ):
        camera.wait_recording(seconds)
        if pathlib.Path(filename).exists():
            logger.info("Video saved, %s.", filename)
        else:
            logger.warning("Error recording video, %s.", filename)


def convert_to_mp4(
    video_file: pathlib.Path, fps: int = None, remove_orig: bool = False
) -> None:
    """Convert video to mp4. Converted videos will be saved and original videos can
    optionally be removed. Frame rate will be inferred if not specified.

    Exceptions raised:
        CalledProcessError: raised if ffmpeg doesnt successfully convert a file.
    """
    new_path = video_file.parent / (video_file.stem + ".mp4")
    subprocess_args_list = [
        "ffmpeg",
        "-i",
        video_file,
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-bsf:a",
        "aac_adtstoasc",
        str(new_path),
    ]
    if fps is not None:
        # Force specific frame rate (i.e. for converting .h264)
        subprocess_args_list.insert(1, "-framerate")
        subprocess_args_list.insert(2, f"{fps}")
    # Run conversion
    subprocess.run(subprocess_args_list, check=True)
    if new_path.exists():
        logger.info("Converted to mp4 and saved %s.", str(video_file))
        if remove_orig:
            video_file.unlink()
            logger.info("Deleted %s.", str(video_file))
    else:
        logger.warning("Conversion warning on file %s.", str(new_path))


def write_to_usb(
    data_path: pathlib.Path, usbstick_path: pathlib.Path, ext: str
) -> None:
    """Write all .ext video files in data dir to path on usb, and remove original files.
    Extension for picam should be mp4, and h264 for picamera unless converted beforehand."""
    for video_path in data_path.glob(f"*.{ext}"):
        target_path = usbstick_path / "data" / video_path.name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(video_path, target_path)
        video_path.unlink()


def test_setup(arguments: Dict[str, Any]):
    """Change arguments to test the setup."""
    arguments["experiment_name"] = "test"
    arguments["segment_length"] = 3  # seconds
    arguments["session_length"] = 7  # seconds
    # Will also depend on what N_SEGMENTS is


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
        "--width",
        type=int,
        default=640,
        help="Width of video in pixels. Defaults to 640.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=480,
        help="Height of video in pixels. Defaults to 480.",
    )
    parser.add_argument(
        "--camera_mode",
        type=int,
        default=6,
        help="Raspberry pi camera mode. Defaults to 6 (for high fps using picam). \
        Warning: picam modes seem to be shifted by one relative to picamera modes.",
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
        help="Run a small preconfigured test.",
    )
    parser.add_argument(
        "--use_picamera",
        action="store_true",
        help="Use picamera instead of picam for experiment.",
    )
    args = vars(parser.parse_args())
    # ---
    # Setup test arguments if debug
    if args["debug"]:
        test_setup(args)
    assert args["segment_length"] < args["session_length"], "Seg len > session len."
    logger.info("Running with args: %s", str(args))
    # ------------------------
    # Set up lighting conditions
    if args["ir"]:
        # ---
        # Set up and initialise BrightPi
        brightPi = brightpi.BrightPi()
        brightPi.reset()
        logger.info("Filming with IR. BrightPi setup.")
    # ------------------------
    # Recording loop
    N_SEGMENTS = 5
    num_iterations = max(
        1,
        int(math.ceil(args["session_length"] / (N_SEGMENTS * args["segment_length"]))),
    )
    space_on_usb = True
    for recording_iter in range(num_iterations):
        logger.info("--------")
        logger.info("Recording loop %d / %d.", recording_iter + 1, num_iterations)
        # ---
        # Turn on IR LEDs
        if args["ir"]:
            brightPi.set_led_on_off(brightpi.LED_IR, brightpi.ON)
            leds_indices_on = brightPi.get_led_on_off(brightpi.LED_IR)
            logger.info("BrightPi IR leds ON: %s", str(leds_indices_on))
        # ---
        # Record n segments of footage for certain duration
        if args["use_picamera"]:
            # ---
            # Use picamera
            camera = PiCameraGs(
                resolution=(args["width"], args["height"]), framerate=args["fps"]
            )
            camera.vflip = True
            camera.hflip = True
            camera.ISO = 800
            camera.awb_mode = "greyworld"
            camera.mode = args["camera_mode"]
            time.sleep(5)  # Camera warmup
            logger.info("About to start recording %d segments...", N_SEGMENTS)
            run_details = f"{args['fps']}fps-{args['width']}x{args['height']}"
            local_video_files_path = pathlib.Path("/home/pi/picamera_data")
            local_video_files_path.mkdir(parents=True, exist_ok=True)
            record_n_segments_picamera(
                num_segs=N_SEGMENTS,
                seconds=args["segment_length"],
                name=f"iter{recording_iter}-{args['experiment_name']}-{run_details}",  # Passed for naming
                camera=camera,
                save_dir=local_video_files_path,
            )
            time.sleep(2)
            # ---
            # Convert from .h264 to .mp4
            for h264_filename in local_video_files_path.glob(f"*.h264"):
                convert_to_mp4(h264_filename, fps=args["fps"], remove_orig=True)
        else:
            # ---
            # Use picam
            camera_proc = subprocess.Popen(
                [
                    "./picam",
                    "--alsadev",
                    "hw:1,0",
                    "--width",
                    f"{args['width']}",
                    "--height",
                    f"{args['height']}",
                    "--fps",
                    f"{args['fps']}",
                    "--mode",
                    f"{args['camera_mode']}",
                    "--hflip",
                    "--vflip",
                    "--wb",
                    "greyworld",
                    "--iso",
                    "800",
                ],
                cwd="/home/pi/picam",
            )
            time.sleep(5)  # Camera warmup
            logger.info("About to start recording %d segments...", N_SEGMENTS)
            run_details = f"{args['fps']}fps-{args['width']}x{args['height']}"
            record_n_segments_picam(
                num_segs=N_SEGMENTS,
                seconds=args["segment_length"],
                name=f"iter{recording_iter}-{args['experiment_name']}-{run_details}",  # Passed for naming
            )
            logger.info("Recording finished.")
            camera_proc.terminate()
            time.sleep(2)
            # ---
            # Convert from .ts to .mp4
            ts_files_save_archive_path = pathlib.Path("/home/pi/picam/archive")
            ts_files_save_rec_path = pathlib.Path("/home/pi/picam/rec")
            for ts_filename in ts_files_save_archive_path.glob("*.ts"):
                convert_to_mp4(ts_filename, remove_orig=True)
                (ts_files_save_rec_path / ts_filename.name).unlink()
            local_video_files_path = ts_files_save_archive_path
        # ---
        # Reset lighting conditions
        if args["ir"]:
            brightPi.reset()
            leds_indices_on = brightPi.get_led_on_off(brightpi.LED_IR)
            logger.info("BrightPi reset, IR leds ON: %s", str(leds_indices_on))
        # ---
        # Check available space in filesystem
        space = shutil.disk_usage(
            local_video_files_path
        )  # Returns total, used and free bytes
        total = float(space.total) / BYTES_PER_GB
        used = float(space.used) / BYTES_PER_GB
        logger.info("Filesystem usage %dgb / %dgb.", used, total)
        if used > WRITE_TO_USB_AFTER and space_on_usb:
            # ---
            # Check available space in USB
            usb_path = pathlib.Path("/home/pi/usbstick")
            usb_space = shutil.disk_usage(usb_path)
            usb_total = float(usb_space.total) / BYTES_PER_GB
            usb_used = float(usb_space.used) / BYTES_PER_GB
            usb_free = float(usb_space.free) / BYTES_PER_GB
            logger.info("USB usage %dgb / %dgb.", round(usb_used), round(usb_total))
            if used > usb_free:
                space_on_usb = False
                logger.info("USB space will be exceeded. Next write cancelled.")
                break
            # ---
            # Write to USB
            logger.info(
                "Moving .mp4 files in %s to %s...",
                str(local_video_files_path),
                str(usb_path),
            )
            write_to_usb(local_video_files_path, usb_path, "mp4")
            used = float(shutil.disk_usage(local_video_files_path).used) / BYTES_PER_GB
            logger.info("Files moved. Filesystem usage now: %dgb.", round(used))
        # ---
        # Break out of loop if space is exceeded
        if (total - used) < LEAVE_SPARE_ON_PI:
            logger.info("Terminating at loop %d due to space.", recording_iter)
            break
