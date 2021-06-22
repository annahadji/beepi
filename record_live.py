"""Small script saving video recordings using Picamera."""
import ctypes as ct
import datetime
import logging
import pathlib
import subprocess
import time
from typing import Generator

import picamera
from picamera import mmal
import brightpi


logger = logging.getLogger("PI")
logging.basicConfig(filename="logs.txt",
                    filemode="a",
                    format="%(asctime)s %(name)s: %(message)s",
                    datefmt="%d.%m.%y %H:%M:%S",
                    level=logging.INFO)


class PiCameraGs(picamera.PiCamera):
    """Greyworld is not yet an option for picamera, as it is in raspvid.
    It helps fix incorrect colours induced by the removal of the IR filter."""
    AWB_MODES = {
        'off':           mmal.MMAL_PARAM_AWBMODE_OFF,
        'auto':          mmal.MMAL_PARAM_AWBMODE_AUTO,
        'sunlight':      mmal.MMAL_PARAM_AWBMODE_SUNLIGHT,
        'cloudy':        mmal.MMAL_PARAM_AWBMODE_CLOUDY,
        'shade':         mmal.MMAL_PARAM_AWBMODE_SHADE,
        'tungsten':      mmal.MMAL_PARAM_AWBMODE_TUNGSTEN,
        'fluorescent':   mmal.MMAL_PARAM_AWBMODE_FLUORESCENT,
        'incandescent':  mmal.MMAL_PARAM_AWBMODE_INCANDESCENT,
        'flash':         mmal.MMAL_PARAM_AWBMODE_FLASH,
        'horizon':       mmal.MMAL_PARAM_AWBMODE_HORIZON,
        'greyworld':     ct.c_uint32(10)
        }


def record_n_segments(n: int, seconds: int, camera: picamera.PiCamera, save_dir: pathlib.Path) -> None:
    """Record n segments of footage of a particular duration (in seconds)."""
    info_str  = f"-{camera.framerate}fps-"
    for filename in camera.record_sequence(
            "%s.h264" % (save_dir / (str(i) + info_str + f"{datetime.datetime.now().strftime('%d%m%y-%H%M')}")) for i in range(0, n)):
        camera.wait_recording(seconds)
        logger.info("Video saved, %s.", filename)

def convert_to_greyscale(video_dir: Generator[pathlib.PosixPath, None, None], remove_orig: bool=False) -> None:
    """Convert videos in a directory to grayscale. Converted videos will be saved
    to same path with 'gry-' prefix and original videos can optionally be removed.

    Exceptions raised:
        CalledProcessError: raised if ffmpeg doesnt successfully convert a file.
    """
    for file in video_dir:
        new_path = file.parent / ("gry-" + file.stem + file.suffix)
        subprocess.run(["ffmpeg", "-i", file, "-vf", "format=gray", new_path], check=True)
        logger.info("%s converted, saved as %s.", file.stem, new_path.stem)
        if remove_orig:
            file.unlink()
            logger.info("Deleted %s.", file.stem)


if __name__ == "__main__":

    logger.info("------------------------------")
    #------------------------
    # Set up and initialise BrightPi
    brightPi = brightpi.BrightPi()
    brightPi.reset()
    #------------------------
    # Turn on IR LEDs
    brightPi.set_led_on_off(brightpi.LED_IR, brightpi.OFF)
    leds_on = sum(brightPi.get_led_on_off(brightpi.LED_IR))
    logger.info("BrightPi setup, %d IR leds ON.", leds_on)
    #------------------------
    # Set up camera
    camera = PiCameraGs(resolution=(640, 480), framerate=90)
    camera.vflip = True
    camera.hflip = True
    camera.exposure_mode = "night"
    camera.ISO = 800
    camera.awb_mode = "greyworld"
    logger.info(
        "Camera setup -fps %d -ex %s -ISO %d -h %d -w %d.",
        camera.framerate,
        camera.exposure_mode,
        camera.ISO,
        camera.resolution.height,
        camera.resolution.width
    )
    #------------------------
    # Set up save dir
    outputs = pathlib.Path("data")
    save_dir = outputs / str(len([i for i in outputs.glob("*") if i.is_dir()]))
    save_dir.mkdir(parents=True, exist_ok=True)
    #------------------------
    # Record N segments of 5s
    logger.info("About to start recording...")
    record_n_segments(n=3, seconds=5, camera=camera, save_dir=save_dir)
    logger.info("Recording finished.")
    #------------------------
    # Reset BrightPi
    brightPi.reset()
    leds_on = sum(brightPi.get_led_on_off(brightpi.LED_IR))
    logger.info("BrightPi reset, %d IR leds ON.", leds_on)
    #------------------------
    # Convert videos to greyscale and delete originals to save space
    logger.info("Converting to greyscale...")
    convert_to_greyscale(save_dir.glob("*"), remove_orig=True)
    logger.info("Finished conversions.")
