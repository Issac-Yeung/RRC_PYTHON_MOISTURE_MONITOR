# Write your code here :-)
import datetime, time
import BlynkLib
import logging
import smtplib, ssl
import threading
from email.message import EmailMessage
from gpiozero import PWMLED, Button, LED
from gpiozero import RGBLED
from colorzero import Color
from datetime import datetime, timedelta

from Sensor import Sensor

BLYNK_TEMPLATE_ID = "TMPL2TeXP8UXe"
BLYNK_TEMPLATE_NAME = "First Blynk App"
BLYNK_AUTH_TOKEN = "uk9DlM8Gy8Ew5PcCbiR9hB7GWpLMnS5l"
blynk = BlynkLib.Blynk(BLYNK_AUTH_TOKEN)
HIGH = 70
NORMAL = 50
HIGH_TXT = "High"
NORMAL_TXT = "Normal"
LOW_TXT = "Low"
prevLevel = LOW_TXT
currLevel = LOW_TXT

mySensor = Sensor()

rgb = RGBLED(26,19,13,active_high = False)
blueled = LED(17)
greenled = LED(4)
redled = LED(27)

stop_thread = threading.Event()
 # This decorator is used to send data to the Blynk app
def read_moisture():
    try:
        global prevLevel
        global currLevel
        moisture_value = mySensor.moisture()
        #print(str(moisture_value))
        inverted_percentage = 1 - max(1, moisture_value - 400) / 250

        percentage = round(inverted_percentage * 100 ,2)

        #logging.info("moisture value: %s, %s%%", moisture_value, percentage);
        blynk.virtual_write(4, percentage)
        led_on(percentage)
        rgbled_on(percentage)
        print(currLevel + "::" + prevLevel)
        if (currLevel != prevLevel):
            logging.info("moisture changed from %s to %s: %s, %s%%", prevLevel, currLevel, moisture_value, percentage);

        if (percentage < NORMAL):
            print("Moisture: ", str(inverted_percentage))
            if (prevLevel != currLevel):
                send_notification(percentage)
        prevLevel = currLevel
    except Exception as e:
        logging.error("moisture_monitor.read_moisture: %s", e)


def led_on(value):
    """Turn on LED."""
    try:
        red = 5
        green = 6
        blue = 7
        if (value < NORMAL):
            color = red
            blynk.virtual_write(green, 0)
            blynk.virtual_write(blue, 0)
            redled.on()
            blueled.off()
            greenled.off()
        elif (value >= HIGH):
            color = blue
            blynk.virtual_write(green, 0)
            blynk.virtual_write(red, 0)
            blueled.on()
            greenled.off()
            redled.off()
        else:
            color = green
            blynk.virtual_write(red, 0)
            blynk.virtual_write(blue, 0)
            greenled.on()
            blueled.off()
            redled.off()

        blynk.virtual_write(color, 1)
    except Exception as e:
        logging.error("moisture_monitor.led_on: %s", e)

def rgbled_on(value):
    global currLevel
    global prevLevel
    """Turn on RGBLED."""
    try:
        if (value < NORMAL):
            """Red"""
            currLevel = LOW_TXT
            rgb.blink(on_color=(1, 0, 0), off_color=(0, 0, 0), on_time=0.5, off_time=0.5, n=5)
        elif (value >= HIGH):
            """Blue"""
            rgb.color = (0, 0, 1)
            currLevel = HIGH_TXT
        else:
            """Green"""
            rgb.color = (0, 1, 0)
            currLevel = NORMAL_TXT

    except Exception as e:
        logging.error("moisture_monitor.rgbled_on: %s", e)


def send_notification(percentage):
    try:
        port = 465  # For SSL
        smtp_server = "smtp.gmail.com"
        sender_email = "wailitca@gmail.com"  # Enter your address
        receiver_email = "wailit1202@gmail.com"  # Enter receiver address
        password = "eckdmjgoxjiigrll"

        msg = EmailMessage()
        msg.set_content("Moisture Notification: " + str(percentage) + "%")
        msg['Subject'] = "Moisture Warning!"
        msg['From'] = sender_email
        msg['To'] = receiver_email

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.send_message(msg, from_addr=sender_email, to_addrs=receiver_email)

    except Exception as e:
        logging.error("moisture_monitor.send_notification: %s", e)

def setup_logger():
    """Configure the logger with a filename based on the current date."""
    current_date = datetime.now().strftime('%Y%m%d')
    log_filename = f"moisture_{current_date}.log"
    print(log_filename)
    logging.basicConfig(filename=log_filename, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

def read_moisture_thread():
    current_day = datetime.now().day
    while not stop_thread.is_set():  # Continue running until stop_thread is set
        try:
            if datetime.now().day != current_day:
                setup_logger()
                current_day = datetime.now().day

            read_moisture()
            time.sleep(1)
        except Exception as e:
            logging.error("moisture_monitor.loop: %s", e)


def main():
    setup_logger()

    try:
        logging.info("moisture start:")

        # Starting the thread
        worker_thread = threading.Thread(target=read_moisture_thread)
        worker_thread.start()

        # Here, the Blynk run can work concurrently with the thread
        blynk.run()

        # Join the thread when Blynk's run is done
        worker_thread.join()


    except Exception as e:
        stop_thread.set()  # This will signal the thread to stop
        worker_thread.join()  # Make sure the worker thread terminates
        logging.error("moisture_monitor: %s", e)
    finally:
        logging.info("moisture end:")

if __name__ == "__main__":
    main()