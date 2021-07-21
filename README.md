# 🎥 🐝 BeePi

Personal setup of a Raspberry Pi and NOIR camera for recording honeybees in a dark observation hive. The setup is intended for close up filming of the comb for short durations, implemented using [picam](https://github.com/iizukanao/picam) to record audio and video. Equivelent functions for recording video only in [picamera](https://picamera.readthedocs.io/en/release-1.13/) v1.13 are in `utils.py`. The main purpose of this repo is to version control the camera config across subsequent filming periods.

## Physical Components

- [Raspberry Pi 4 Model B](https://thepihut.com/products/raspberry-pi-4-model-b) - 4gb memory and 64gb Micro SD Card (v3.6.0).
- [Raspberry Pi NoIR Camera Module V2](https://thepihut.com/products/raspberry-pi-noir-camera-module) - camera used for recording.
- [BrightPi](https://uk.pi-supply.com/products/bright-pi-bright-white-ir-camera-light-raspberry-pi) - 8 Infra red (940nm) and 4 white light LEDs used to light surface of comb.
- [PIR Camera Case](https://thepihut.com/products/pir-camera-case-for-raspberry-pi-4-3) - hold components together.

## Example usage

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

```
# For running picam version

# After a reboot
./mount_usb  # If you have a USB stick for overflow storage space
./make_dirs  # Initialise

# Run the script
python3 record_picam.py --debug
```
