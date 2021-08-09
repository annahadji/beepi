# 🎥 🐝 BeePi

Personal setup of a Raspberry Pi and NOIR camera for recording honeybees in a dark observation hive.

The setup is intended for close up filming of the comb for short durations and uses [picam](https://github.com/iizukanao/picam) v1.4.11 to record audio and video, or for recording video only using [picamera](https://picamera.readthedocs.io/en/release-1.13/) v1.13. The main purpose of this repo is to version control the camera config across subsequent filming periods.

## Physical Components

- [Raspberry Pi 4 Model B](https://thepihut.com/products/raspberry-pi-4-model-b) - 4gb memory and 64gb Micro SD Card (v3.6.0).
- [Raspberry Pi NoIR Camera Module V2](https://thepihut.com/products/raspberry-pi-noir-camera-module) - camera used for recording.
- [BrightPi](https://uk.pi-supply.com/products/bright-pi-bright-white-ir-camera-light-raspberry-pi) - 8 Infra red (940nm) and 4 white light LEDs used to light surface of comb.
- [PIR Camera Case](https://thepihut.com/products/pir-camera-case-for-raspberry-pi-4-3) - hold components together.

## Getting started

Install the dependencies by following the installation instructions for [picam](https://github.com/iizukanao/picam) and [BrightPi](https://github.com/PiSupply/Bright-Pi). picamera is typically pre-installed on Raspberry Pis.s To then test a filming setup with audio, clone this repository and run the following:

```bash
# For running from terminal...

# After a reboot of the Pi
./mount_usb  # If there's a USB stick for overflow storage space
./make_dirs  # Create picam directories (from picam docs)

# Run the script (assumes index of microphone is "hw:1,0", can be checked by `arecord -l`)
python3 record.py --debug
```

There are a few different arguments I use when recording footage.

```
[00:09:10] 🚀 beepi $ python3 record.py --help
usage: record.py [-h] [--experiment_name EXPERIMENT_NAME] [--fps FPS]
                 [--width WIDTH] [--height HEIGHT] [--camera_mode CAMERA_MODE]
                 [--segment_length SEGMENT_LENGTH]
                 [--session_length SESSION_LENGTH] [--ir] [--debug]
                 [--use_picamera]

Record segments of video and audio using picam or picamera. Picam can provide
audio from a connected USB microphone; picamera can be used for higher
resolution files (e.g. 1640 x 922 and upwards).

optional arguments:
  -h, --help            show this help message and exit
  --experiment_name EXPERIMENT_NAME
                        Name for experimental run.
  --fps FPS             Frames per second to record in.
  --width WIDTH         Width of video in pixels. Defaults to 640.
  --height HEIGHT       Height of video in pixels. Defaults to 480.
  --camera_mode CAMERA_MODE
                        Raspberry pi camera mode. Defaults to 6 (for high fps
                        using picam). Warning: picam modes seem to be shifted
                        by one relative to picamera modes.
  --segment_length SEGMENT_LENGTH
                        Length of an individual video segment (in seconds).
  --session_length SESSION_LENGTH
                        Desired length of resulting footage (in seconds). i.e.
                        21600 - 6hrs, 28800 - 8hrs, 43200 - 12hrs, 64800 -
                        18hrs, 86400 - 24hrs.
  --ir                  Use infrared lighting when recording.
  --debug               Run a small preconfigured test.
  --use_picamera        Use picamera instead of picam for experiment.
```

Some parameters for filming are held constant. These include the ISO (800), white balance ("greyworld"), and a horizontal and vertical flip of the image.

# Example commands

```
# Record video and audio, 90 fps, low resolution (picam)
python3 record.py --experiment_name sgarden_210809_1156 --width 640 --height 480 --fps 90 --camera_mode 6 --session_length 21600

# Record just video, using full field of view, 30 fps is the highest we can go (picamera)
python3 record.py --experiment_name sgarden_210809_1156 --width 1640 --height 1232 --fps 30 --camera_mode 4 --session_length 21600 --use_picamera
```
