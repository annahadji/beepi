# 🎥 🐝 BeePi

Personal setup of a Raspberry Pi and NOIR camera for recording honeybees in a dark observation hive.

The setup is intended for close up filming of the comb for short durations and uses [picam](https://github.com/iizukanao/picam) v1.4.11 to record audio and video. Equivalent functions for recording video only in [picamera](https://picamera.readthedocs.io/en/release-1.13/) v1.13 are in `utils.py`. The main purpose of this repo is to version control the camera config across subsequent filming periods.

## Physical Components

- [Raspberry Pi 4 Model B](https://thepihut.com/products/raspberry-pi-4-model-b) - 4gb memory and 64gb Micro SD Card (v3.6.0).
- [Raspberry Pi NoIR Camera Module V2](https://thepihut.com/products/raspberry-pi-noir-camera-module) - camera used for recording.
- [BrightPi](https://uk.pi-supply.com/products/bright-pi-bright-white-ir-camera-light-raspberry-pi) - 8 Infra red (940nm) and 4 white light LEDs used to light surface of comb.
- [PIR Camera Case](https://thepihut.com/products/pir-camera-case-for-raspberry-pi-4-3) - hold components together.

## Getting started

Install the dependencies by following the installation instructions for [picam](https://github.com/iizukanao/picam) and [BrightPi](https://github.com/PiSupply/Bright-Pi). To then test a filming setup, clone this repository and run the following:

```bash
# For running from terminal...

# After a reboot of the Pi
./mount_usb  # If there's a USB stick for overflow storage space
./make_dirs  # Create picam directories (from picam docs)

# Run the script (assumes index of microphone is "hw:1,0", can be checked by `arecord -l`)
python3 record_picam.py --debug
```

There are a few different arguments I use when recording footage.

```
[00:09:10] 🚀 beepi $ python3 record_picam.py --h
usage: record_picam.py [-h] [--experiment_name EXPERIMENT_NAME] [--fps FPS] [--segment_length SEGMENT_LENGTH] [--session_length SESSION_LENGTH] [--ir] [--debug]

Record segments of video and audio using picam.

optional arguments:
  -h, --help            show this help message and exit
  --experiment_name EXPERIMENT_NAME
                        Name for experimental run.
  --fps FPS             Frames per second to record in.
  --segment_length SEGMENT_LENGTH
                        Length of an individual video segment (in seconds).
  --session_length SESSION_LENGTH
                        Desired length of resulting footage (in seconds). i.e. 21600 - 6hrs, 28800 - 8hrs, 43200 - 12hrs, 64800 - 18hrs, 86400 - 24hrs.
  --ir                  Use infrared lighting when recording.
  --debug               Run a small preconfigured test.
```

Some parameters for filming are held constant. These include the image resolution (640 x 480), ISO (800), camera mode (6), white balance ("greyworld"), and a horizontal and vertical flip of the image.
