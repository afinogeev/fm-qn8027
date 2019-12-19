#module used to control the qn8027 fm transmitter

import smbus
import time

currentFreq = 8800
maxFreq = 10790
minFreq = 7610

bus = smbus.SMBus(1)    #we are using i2c port 1
DEVICE_ADDRESS = 0x2C      #7 bit address (will be left shifted to add the read write bit)

SYSTEM_REG = 0x00       #system register
CH1_REG = 0x01          #register that the lower 8 bits of the frequency goes in
GPLT_REG = 0x02
XTL_REG = 0x03
VGA_REG = 0x04
CID1_REG =  0x05
CID2_REG =  0x06
STATUS_REG = 0x07
RDSD0_REG = 0x08
RDSD1_REG = 0x09
RDSD2_REG = 0x0A
RDSD3_REG = 0x0B
RDSD4_REG = 0x0C
RDSD5_REG = 0x0D
RDSD6_REG = 0x0E
RDSD7_REG = 0x0F
PAC_REG = 0x10
FDEV_REG = 0x11
RDS_REG = 0x12

SWRST = 0x80
RECAL = 0x40
RDSEN = 0x80
RDSRDY = 0x04

CH0_MASK = 0x03
CH1_MASK = 0xFF
TRANSMIT_MASK = 0x20
PAOFF_MASK = 0x30


#initializes the device and sets default values to it
def init():
    #TRY CONNECTING TO THE DEVICE FIRST

    print("QN8027 initialization")
    global currentFreq
    writeData(SYSTEM_REG, SWRST, SWRST)     #reset all registers
    writeData(VGA_REG, 0x0F, 0x09)
    #writeData(FDEV_REG, 0xFF, 0x80)
    writeData(RDS_REG, 0x80, 0x80)
    recalibrate()
    writeData(GPLT_REG, PAOFF_MASK, 0x30)     #tell the device that it shouldn't go into standby if there is no audio
    writeData(GPLT_REG, 0x0F, 0x07)
    setFrequency(currentFreq)
    enableTransmit(True)


#I don't know if this actually helps anything, but it doesn't seem to hurt
def recalibrate():
    writeData(SYSTEM_REG, RECAL, RECAL)
    writeData(SYSTEM_REG, RECAL, 0x00)
    
    
#sets the frequency, give it a frequency formatted like 10310 for 103.1MHz, or 9890 for 98.9MHz
#make sure the frequency is an odd numbered 200KHz slice, and not something like 98.4MHz
def setFrequency(freq):
    global currentFreq
    currentFreq = freq
    freq = (freq - 7600) / 5    #convert the frequency to a 10 bit decimal
    #we need 10 bits because the device wants 2 bits to go in on register, and the other 8 in another register
    #it's strange but whatever
    partOne = int(freq) >> 8     #shift it to the right 8 times, this leaves us with the first 2 bits
    partTwo = int(freq) & 0xFF   #AND it with a mask covering the last 8 bits, leaving the last 8 bits
    
    #write out the parts to their specific registers
    writeData(SYSTEM_REG, CH0_MASK, partOne)
    writeData(CH1_REG, CH1_MASK, partTwo)
    
    print("Transmitting on: " + str(getFrequency()))


#returns the current frequency set on the device formatted like 10310 for 103.1MHz
def getFrequency():
    partOne = bus.read_byte_data(DEVICE_ADDRESS, SYSTEM_REG)    #get the first part out of the system register
    partOne = partOne & CH0_MASK    #mask out the two bits that we want
    partTwo = bus.read_byte_data(DEVICE_ADDRESS, CH1_REG)   #get the second part out, no need to apply any masks
    
    combined = (partOne << 8) | partTwo
    #shift the first part left two, and then OR them together, leaving a 10 bit value
    output = (combined * 5) + 7600      #convert the output to something readable
    return output
    

#enabled or disable FM transmission
def enableTransmit(enabled):
    if enabled:
        writeData(SYSTEM_REG, TRANSMIT_MASK, TRANSMIT_MASK)
    else:
        writeData(SYSTEM_REG, TRANSMIT_MASK, 0x00)
    

#writes specific bits of data to a specified register
def writeData(register, bitmask, data):
    currentData = bus.read_byte_data(DEVICE_ADDRESS, register)
    #get the data that is already in the specified register (for merging in new data)
    
    output = currentData & (~ bitmask)  #AND the current data with the NOTed bitmask
    output = output | (data & bitmask)  #AND the new data with the bitmask, and then OR it with the current output      
    
    bus.write_byte_data(DEVICE_ADDRESS, register, output)       #write out the data

#reads bits from register
def readData(register, bitmask):
    currentData = bus.read_byte_data(DEVICE_ADDRESS, register)
    return currentData & bitmask

#sets RDS data
def setRDS(data):
    if(len(data)>8):
        data = data[0:8:1]
    else:
        data = data.center(8," ")
    data_b = bytes(data, "utf-8")
    #print(data)
    i=0
    for j in range(0,40):
        time.sleep(0.05)
        status = readData(STATUS_REG,8)
        #print(status)
        #writing A0 rds group
        if(status==8):
            i+=1
            if(i==1):
                writeData(RDSD0_REG, 0xFF, 0b01110000)
                writeData(RDSD1_REG, 0xFF, 0b00000000)
                writeData(RDSD2_REG, 0xFF, 0b00000101)
                writeData(RDSD3_REG, 0xFF, 0b01100100)
                writeData(RDSD4_REG, 0xFF, 0b00000000)
                writeData(RDSD5_REG, 0xFF, 0b00000000)
                writeData(RDSD6_REG, 0xFF, data_b[0])
                writeData(RDSD7_REG, 0xFF, data_b[1])
            if(i==2):
                writeData(RDSD0_REG, 0xFF, 0b01110000)
                writeData(RDSD1_REG, 0xFF, 0b00000000)
                writeData(RDSD2_REG, 0xFF, 0b00000101)
                writeData(RDSD3_REG, 0xFF, 0b01100001)
                writeData(RDSD4_REG, 0xFF, 0b00000000)
                writeData(RDSD5_REG, 0xFF, 0b00000000)
                writeData(RDSD6_REG, 0xFF, data_b[2])
                writeData(RDSD7_REG, 0xFF, data_b[3])
            if(i==3):
                writeData(RDSD0_REG, 0xFF, 0b01110000)
                writeData(RDSD1_REG, 0xFF, 0b00000000)
                writeData(RDSD2_REG, 0xFF, 0b00000110)
                writeData(RDSD3_REG, 0xFF, 0b01100010)
                writeData(RDSD4_REG, 0xFF, 0b00000000)
                writeData(RDSD5_REG, 0xFF, 0b00000000)
                writeData(RDSD6_REG, 0xFF, data_b[4])
                writeData(RDSD7_REG, 0xFF, data_b[5])
            if(i==4):
                writeData(RDSD0_REG, 0xFF, 0b01110000)
                writeData(RDSD1_REG, 0xFF, 0b00000000)
                writeData(RDSD2_REG, 0xFF, 0b00000110)
                writeData(RDSD3_REG, 0xFF, 0b01100111)
                writeData(RDSD4_REG, 0xFF, 0b00000000)
                writeData(RDSD5_REG, 0xFF, 0b00000000)
                writeData(RDSD6_REG, 0xFF, data_b[6])
                writeData(RDSD7_REG, 0xFF, data_b[7])
            if(i==5):
                #print('rds done')
                break
        rdy = readData(SYSTEM_REG, 4)
        if(rdy==0b00000100):
            writeData(SYSTEM_REG, 4, 0) #RDSRDY=0
        else:
            writeData(SYSTEM_REG, 4, 4) #RDSRDY=1
    
    
#sets TX power
def setPower(power_p):
    power_n = int(1.27*power_p)
    enableTransmit(False)
    writeData(PAC_REG, 0x7F, power_n)
    recalibrate()
    enableTransmit(True)
    print("Power: " + str(power_n))
"""
"""