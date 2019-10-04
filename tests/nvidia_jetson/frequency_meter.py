#!/usr/bin/env python

# Copyright (c) 2019, NVIDIA CORPORATION. All rights reserved.
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
# EXAMPLE SETUP
# Connect a button to pin 18 and GND, a pull-up resistor connecting the button
# to 3V3 and an LED connected to pin 12. The application performs the same
# function as the button_led.py but performs a blocking wait for the button
# press event instead of continuously checking the value of the pin in order to
# reduce CPU usage.

import time
from threading import Thread

import RPi.GPIO as GPIO


class FreqShowerThread(Thread):

    def __init__(self):
        super().__init__()
        self.__freq = 0
        self.__is_runnable = False
        self.__last_check_time = time.time()
        self.__freq = 0
        self.__time_delay = 1

    def increment_freq(self):
        self.__freq += 1

    def run(self):
        self.__is_runnable = True
        while self.__is_runnable:
            now = time.time()
            if now - self.__last_check_time >= self.__time_delay:
                print("Frequency: ", self.__freq)
                self.__freq = 0
                self.__last_check_time = now
            # time.sleep(0.5)


# Pin Definitons:
led_pin = 12  # Board pin 12
but_pin = 13  # Board pin 18


def main():

    # Pin Setup:
    GPIO.setmode(GPIO.BOARD)  # BOARD pin-numbering scheme
    GPIO.setup(led_pin, GPIO.OUT)  # LED pin set as output
    GPIO.setup(but_pin, GPIO.IN)  # button pin set as input

    # Initial state for LEDs:
    GPIO.output(led_pin, GPIO.LOW)

    print("Starting demo now! Press CTRL+C to exit")

    show_thread = FreqShowerThread()
    show_thread.start()

    try:
        while True:
            # print("Waiting for button event")
            GPIO.wait_for_edge(but_pin, GPIO.RISING)

            # print("+1")

            show_thread.increment_freq()

            # event received when button pressed
            # print("Button Pressed!")
            # GPIO.output(led_pin, GPIO.HIGH)
            # time.sleep(1)
            # GPIO.output(led_pin, GPIO.LOW)
    finally:
        GPIO.cleanup()  # cleanup all GPIOs


if __name__ == '__main__':
    main()
