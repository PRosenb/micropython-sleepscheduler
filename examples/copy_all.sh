export PORT=/dev/cu.SLAB_USBtoUART
ampy --port $PORT put execute_3_times.py
ampy --port $PORT put led_on_even_minute.py
ampy --port $PORT put sensors_every_minute.py
ampy --port $PORT put temp_diff.py
