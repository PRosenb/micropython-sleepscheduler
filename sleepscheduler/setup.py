import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system's.
sys.path.pop(0)
from setuptools import setup
sys.path.append("..")

# https://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
import imp
sdist_upip = imp.load_source('sdist_upip', './sdist_upip.py')

setup(name='micropython-sleepscheduler',
      version='0.0.1',
      description='A simple scheduler for ESP32 supporting deep sleep.',
      long_description='This library for ESP32 aims to make it easy to execute tasks on regular basis and put the CPU on sleep in between.',
      url='https://github.com/PRosenb/sleepscheduler',
      author='Pete',
      author_email='arduino@pete.ch',
      platforms=['esp32'],
      license='Apache License, Version 2.0',
      cmdclass={'sdist': sdist_upip.sdist},
      py_modules=['sleepscheduler'],
)
