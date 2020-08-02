# install ampy from https://learn.adafruit.com/micropython-basics-load-files-and-run-code/install-ampy
export PORT=/dev/cu.SLAB_USBtoUART
ampy --port $PORT put main.py
ampy --port $PORT put sleepscheduler/sleepscheduler.py
