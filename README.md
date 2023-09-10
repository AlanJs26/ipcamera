# Remote Cameras (icsee)

My attempt at managing multiple IP cameras, processing, and storing their video footage using Python.

## Requirements

- arp (net-tools)
- python >= 3.10 

## How to use

All configurations are in `config.json` file, where you can add new cameras providing a name, a path for storing their footage, the password and their MAC address.

> Note that I have only tested this project on icsee cameras, specifically those that support ONVIF such as the A8B model. If you want to use it with different cameras, you will probably need to do some fine-tuning in the code.

The main fields are:

|Field|Type|Purpose|
|--|-|-|
|segment_size|`integer`|The script works by recording continually and after some time, checking if there was detected some human in the footage to decide if that segment should be discarded or not. The `segment_size` field controls the size (in seconds) of the segment that should be kept.|
|segment_name|`string`|Is the name of the segment video file that will be stored. Here you can put `{}` to insert the time when the segment was recorded.|
|scale_factor|`integer`|It is the scale factor that the video will be scaled to be stored in a more manageable file size.|
|realtime|`boolean`|It is used to ignore the video buffering used by OpenCV in such a way that it tries to fetch the most recent frame of the cameras. It is useful when running the script on a weak computer that is not able to manage all cameras and fetch their recordings in real-time.|
|retry_interval|`integer`|It is the interval (in seconds) to reconnect when it loses a connection to one of the cameras.|
|min_confidence|`float`|It is the minimal confidence to trust in the human detector neural network.|
|debug|`boolean`|If it is true, the script will not store the video segments on disk.|
|X11|`boolean`|It controls if it is shown the video capture in a window.|
|cameras|`camera_type`|It is a list of all cameras. `camera_type` is described below.|


#### camera_type

|field|type|purpose|
|-|-|-|
|name|`string`|The name of the camera. This name is used when logging in the terminal.|
|folder|`string`|Where the video footage will be stored.|
|password|`string`|The camera password. On Icsee cameras, it is set when configuring the camera for the first time on the app.|
|mac|`string`|The MAC address of the camera. You can find it using the command `arp-scan --localnet` (which is one of the requirements for this project) or by looking at the connected devices in your router's web interface.|


