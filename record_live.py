"""Small script saving video recordings using Picamera."""
import ctypes as ct
import logging
import pathlib
import time

import picamera
from picamera import mmal
import brightpi


logger = logging.getLogger("PI")
logging.basicConfig(filename="logs.txt",
                    filemode="a",  # Append, not overwrite
                    format="%(asctime)s %(name)s: %(message)s",
                    datefmt="%d.%m.%y %H:%M:%S",
                    level=logging.INFO)


class PiCamera2(picamera.PiCamera):
    """Greyworld is not yet an option for picamera, as it is available in raspvid."""
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

if __name__ == "__main__":
    logger.info("------------------------------")

    # Set up and initialise BrightPi
    brightPi = brightpi.BrightPi()
    brightPi.reset()

    # Turn on IR LEDs
    brightPi.set_led_on_off(brightpi.LED_IR, brightpi.OFF)
    leds_on = sum(brightPi.get_led_on_off(brightpi.LED_IR))
    logger.info("BrightPi setup, %d IR leds ON.", leds_on)

    # Set up camera
    camera = PiCamera2(resolution=(640, 480), framerate=90)
    camera.vflip = True
    camera.hflip = True
    camera.exposure_mode = "night"
    camera.ISO = 800  # Larger ISO for darker environments
    camera.awb_mode = "greyworld"  # Unlike raspvid, picamera doesn't have greyworld
    logger.info(
        "Camera setup -fps %d -ex %s -ISO %d -h %d -w %d.",
        camera.framerate,
        camera.exposure_mode,
        camera.ISO,
        camera.resolution.height,
        camera.resolution.width
    )

    # Set up save dir
    outputs = pathlib.Path("data")
    save_dir = outputs / str(len([i for i in outputs.glob("*") if i.is_dir()]))
    save_dir.mkdir(parents=True, exist_ok=True)

    # Record N segments of 5s
    logger.info("About to start recording...")
    for filename in camera.record_sequence(  # TODO: make name of file more informative
            "%s.h264" % (save_dir / str(i)) for i in range(1, 3)):
        camera.wait_recording(5)
        logger.info("Video saved to %s.", filename)
    logger.info("Recording finished.")

    # Reset BrightPi
    brightPi.reset()
    leds_on = sum(brightPi.get_led_on_off(brightpi.LED_IR))
    logger.info("BrightPi reset, %d IR leds ON.", leds_on)
