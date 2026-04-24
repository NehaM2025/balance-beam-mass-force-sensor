import machine
import time
import struct

# Set up buttons on GPIO35 and GPIO36
calibrationButton = machine.Pin(35, machine.Pin.IN)
measurementButton = machine.Pin(36, machine.Pin.IN)


#LED
red_LED = machine.Pin(16, machine.Pin.OUT)
green_LED = machine.Pin(13, machine.Pin.OUT)
blue_LED = machine.Pin(4, machine.Pin.OUT)


#Set these based on what the supervisor says
red_min = 30.0
red_max = 250.0
green_min = 249.0
green_max = 600.0
blue_min = 500.0
blue_max = 1000.0

#Supervisor's Scale Gram Weight of 1000 grams
superWeight = 1000

#define zero and 1000g values
calZero = 1

# Set up GPIO pins
#GPIO 25 is INA125p SLEEP_BAR
gpio25 = machine.Pin(25, machine.Pin.OUT)

#GPIO 27 is AD7715 RESET_Bar
gpio27 = machine.Pin(27, machine.Pin.OUT)

# Set INA125p to sleep
gpio25.off()


class AD7715:
    # Register addresses
    WRITETO_SETUP=0b00010000
    READFROM_DATA=0b00111000
    WRITETO_COMREG=0b00000000

    NORMAL_MODE=0b00000110
    SELF_CALIB=0b01000110
    ZERO_SCALE_CALIB=0b10000110
    FULL_SCALE_CALIB=0b11000110
    
    CS_PIN=5


    def __init__(self):
        # Set up SPI bus using hardware-defined pins
        self.spi = machine.SPI(2, baudrate=38400, polarity=1, phase=1, firstbit = machine.SPI.MSB, sck=machine.Pin(18), mosi=machine.Pin(23), miso=machine.Pin(19))
        # self.spi.init()
        time.sleep(0.5)
        
        # GPIO pins
        self.rdy_pin = machine.Pin(26, machine.Pin.IN,pull=machine.Pin.PULL_UP)
        self.cs_pin = machine.Pin(self.CS_PIN, machine.Pin.OUT)

        # Reset AD7715
        gpio27.on()
        gpio27.off()
        gpio27.on()
        time.sleep(0.5)


        self.select()
        # Configure AD7715 control registers
        self.spi.write(bytearray([self.WRITETO_COMREG]))
        #time.sleep(0.1)
        self.deselect()

        # self.spi.write(bytearray([self.NORMAL_MODE]))
        # time.sleep(0.1)



        self.calibrate()

    #using the Cs pin to control access to the AD7715 ensures that it only listens when we want it to.
    def select(self):
        self.cs_pin.off()
        
    def deselect(self):
        self.cs_pin.on()
        
    def reset_spi(self):
        self.select()
        self.spi.write(bytearray([0xFF]))
        self.spi.write(bytearray([0xFF]))
        self.spi.write(bytearray([0xFF]))
        self.spi.write(bytearray([0xFF]))
        self.deselect()

    def calibrate(self):

        # Perform zero-scale calibration
        print("running self calibration")
        
        self.select()
        self.spi.write(bytearray([self.WRITETO_SETUP]))

        self.spi.write(bytearray([self.SELF_CALIB]))
        self.deselect()
        time.sleep(0.001)
        
        while (self.rdy_pin.value() == 1):
            ()
        self.select()
        self.spi.write(bytearray([self.READFROM_DATA]))
        
        adc_data = bytearray(2)
        self.spi.readinto(adc_data,0xFF)
        self.deselect()

        # Convert raw data to integer value
        adc_value = (adc_data[0] << 8) | adc_data[1]
        print(adc_value)

    def zero_scale_system_calibrate(self):
        # Perform zero-scale system calibration
        self.select()
        self.spi.write(bytearray([self.WRITETO_SETUP]))

        self.spi.write(bytearray([self.ZERO_SCALE_CALIB]))
        time.sleep(0.0001)
        self.deselect()
        while self.rdy_pin.value() == 1:
            ()
        self.select()
        self.spi.write(bytearray([self.READFROM_DATA]))

        adc_data = bytearray(2)
        self.spi.readinto(adc_data,0xFF)
        self.deselect()
        
        time.sleep(0.060)

        # Convert raw data to integer value
        adc_value = int( (adc_data[0] << 8) | adc_data[1])
        print(adc_value)
        
        #binary_string1 = bin(adc_value) # convert the byte to a binary string and pad with leading zeros
        #print(binary_string1)

        #binary_string2 = bin(adc_value) # convert the byte to a binary string and pad with leading zeros
        #print(binary_string2)
    

    def full_scale_system_calibrate(self, weight):
        # Perform full-scale system calibration
        self.select()
        self.spi.write(bytearray([self.WRITETO_SETUP]))

        self.spi.write(bytearray([self.FULL_SCALE_CALIB]))
        self.deselect()
        time.sleep(0.010)
        
        while (self.rdy_pin.value() == 1):
            ()
        self.select()
        self.spi.write(bytearray([self.READFROM_DATA]))

        adc_data = bytearray(2)
        self.spi.readinto(adc_data,0xFF)
        self.deselect()
        # Convert raw data to integer value
        adc_value = (adc_data[0] << 8) | adc_data[1]
        self.calFull = adc_value
        print(adc_value)

    def read_adc(self):
        #self.reset_spi()
        # Wait for RDY pin to go low
        
        while self.rdy_pin.value() == 1:
            ()
        self.select()
        self.spi.write(bytearray([self.READFROM_DATA]))

        # Read ADC data
        adc_data = bytearray(2)
        self.spi.readinto(adc_data,0xFF)
        self.deselect()
        # Convert raw data to integer value
        # adc_value = (adc_data[0] << 8) | adc_data[1]

        adc_value= struct.unpack('>H', adc_data)[0]

        #print (adc_value)
        
        binary_string1 = bin(adc_value)
        # convert the byte to a binary string and pad with leading zeros
        #print(binary_string1)
        
        #binary_string2 = bin(adc_value)
        # convert the byte to a binary string and pad with leading zeros
        #print(binary_string2)
        #print("")
        # Convert ADC data to integer value
        return adc_value


#define AD
#spi = machine.SPI(2, baudrate=1000000, polarity=1, phase=0,firstbit=0,sck=machine.Pin(18), mosi=machine.Pin(19), miso=machine.Pin(23))
ad = AD7715()

# Wait for user to verify no weight on the pan
print("Zero scale calibration - verify there is no weight on the pan and press calibration button")

while not calibrationButton.value():
    time.sleep(0.1)

while calibrationButton.value():
    time.sleep(.1)

print("")
print("Zero scale system calibration started")

#turn on INA125p
gpio25.on()
time.sleep(1)

# Perform zero scale system calibration
ad.zero_scale_system_calibrate()
print("")
print("Zero scale system calibration completed")

#turn off INA125p
gpio25.off()

# # Wait for user to verify 1000 gram weight on the pan
print("")
print("Place 1000g for full scale calibration")
while not calibrationButton.value():
    time.sleep(0.1)

while calibrationButton.value():
    time.sleep(0.1)

print("")
print("Full-scale system calibration started")
#turn on INA125p
gpio25.on()
time.sleep(1)

# Perform full-scale system calibration
ad.full_scale_system_calibrate(superWeight)
print("")
print("Full-scale system calibration completed")
#turn off INA125p
gpio25.off()

zero_values = []
while True:
    print("")
    print("Remove weight from the pan and press measure button after placing new weights that you'd like to measure")
    
    while not (measurementButton.value()):
        time.sleep(0.1)

    # Wait for measurementButton press
    while (measurementButton.value()):
        time.sleep(0.1)
        #turn on INA125p
    gpio25.on()
    
    red_LED.value(0)
    green_LED.value(0)
    blue_LED.value(0)
    time.sleep(1)
    # Record zero values every 1/4 second
    zero_values.append(ad.read_adc())
    time.sleep(2)
    if len(zero_values) > 5:
        zero_values.pop(0)

    # Measure weight
    print("")
    print("Now measuring weight...")
    print("")
    time.sleep(0.5)

    values = []
    for i in range(5):
        values.append(ad.read_adc())
        time.sleep(0.01)

    values = []
    for i in range(25):
        values.append(ad.read_adc())
        time.sleep(0.01)
    average_value = sum(values) / 25.0
    print("", average_value)
    print("Average voltage: {:6.3f}".format(1.859 * (average_value/ad.calFull)))
    #1.698 is the measured differeence in INA output between 500g on the pan and nothing on the pan;
    #i.e. the scale factor of the loadcell and the INA combined. Currrent INA gain resistor is 33Ohms,
    #for nominal gain of 1820.
    average_value = average_value * (1000 / ad.calFull)
    #average_value = round(average_value * 10) / 10
    #print("calFull ", ad.calFull)
    print("Average mass, grams = {:6.1f}".format(average_value))


    # Light up LEDS
    if red_min <= average_value <= red_max:
        # Turn on the LED
        red_LED.value(1)
    if green_min <= average_value <= green_max:
        # Turn on the LED
        green_LED.value(1)
    if blue_min <= average_value <= blue_max:
        # Turn on the LED
        blue_LED.value(1)

    # # # Check if significantly different from previous values
    # average_mass = 0.0
    # if abs(average_value - sum(zero_values)/len(zero_values)) > 10:
    # #     # Wait for measurementButton release
    #      while not measurementButton.value():
    #          time.sleep(0.01)

    #     # # Perform weight measurement
    #     #You uncommented lines 260-266
    #      print("Weight detected. Performing weight measurement...")
    #      values = []
    #      for i in range(50):
    #          values.append(ad.read_adc())
    #          time.sleep(0.01)
    #      average_value = int(sum(values) / len(values))
    #      print("Average value VOLTAGE: {}".format(average_value))
    #      average_mass = average_value/ 100

        # Prompt to remove weight
    print("Please remove weight from the pan.")
    print("")
        # time.sleep(5)
        # # Wait for stabilization
        # stable = False
        # while not stable:
        #     for i in range(10):
        #         zero_values.append(ad.read_adc())
        #         time.sleep(0.25)
        #         if len(zero_values) > 10:
        #             zero_values.pop(0)
        #     if abs(average_value - sum(zero_values)/len(zero_values)) < 5:
        #         stable = True

    #turn off INA125p
    gpio25.off()

# Clear console
# print("\033c", end="")
