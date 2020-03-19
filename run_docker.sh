#! /bin/bash
docker run -it -v="/home/notha99y/Documents/personal_projects/python-cropper-tk:/cropper" -e DISPLAY=$DISPLAY -e QT_X11_NO_MITSHM=1 -v /tmp/.X11-unix:/tmp/.X11-unix cropper:latest
