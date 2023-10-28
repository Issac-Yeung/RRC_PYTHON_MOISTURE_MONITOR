import time
from grove.adc import ADC

class Sensor:
    def __init__(self):
        self.aio = ADC(address=0x08)

    def moisture(self):
        return self.aio.read(0)