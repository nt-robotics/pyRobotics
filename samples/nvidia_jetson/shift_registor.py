import time

import RPi.GPIO as GPIO


LATCH_PIN = 13
CLK_PIN = 12
DATA_PIN = 11

GPIO.setmode(GPIO.BOARD)  # BOARD pin-numbering scheme

GPIO.setup(LATCH_PIN, GPIO.OUT)  # LED pin set as output
GPIO.setup(CLK_PIN, GPIO.OUT)  # LED pin set as output
GPIO.setup(DATA_PIN, GPIO.OUT)  # LED pin set as output

GPIO.output(DATA_PIN, GPIO.LOW)
GPIO.output(LATCH_PIN, GPIO.LOW)
GPIO.output(CLK_PIN, GPIO.LOW)


def pulse_clc():
    GPIO.output(CLK_PIN, GPIO.HIGH)
    GPIO.output(CLK_PIN, GPIO.LOW)


def ser_latch():
    GPIO.output(LATCH_PIN, GPIO.HIGH)
    GPIO.output(LATCH_PIN, GPIO.LOW)


# byte1 = 0b00000000
# byte2 = 0b11111111

while True:

    for i in range(0, 16):
        GPIO.output(DATA_PIN, 1)
        pulse_clc()

    ser_latch()
    time.sleep(1)

    for i in range(0, 16):
        GPIO.output(DATA_PIN, 0)
        pulse_clc()

    ser_latch()
    time.sleep(1)
