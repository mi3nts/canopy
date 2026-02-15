import Odroid.GPIO as GPIO
import time
 
PIN = 16
 
GPIO.setmode(GPIO.BOARD)
GPIO.setup(PIN, GPIO.OUT)
 
# If the kernel/OS is running then this code should always be running and sent to the relay handler over GPIO
try:
    while True:
        GPIO.output(PIN, GPIO.HIGH)
        time.sleep(0.25)
        GPIO.output(PIN, GPIO.LOW)
        time.sleep(0.25)
except KeyboardInterrupt:
    GPIO.cleanup()