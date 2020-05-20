#!/usr/bin/python
# This is a userspace program that interfaces a Huanyang GT-series VFD to LinuxCNC HAL
import hal, time
import argparse
import minimalmodbus

# modbus communication options
# Any options not specified in the command line will use the default values listed below.
device = "/dev/ttyUSB0"
byte_size = 8
baudrate = 38400
parity = "N"
stop_bits = 1
slave = 1
max_speed = 24000
min_speed = 7200

period = 0.25 # seconds to sleep before each cycle
motor_is_on = False
baud_values = ["1200", "2400", "4800", "9600", "19200", "38400"]
parity_values = ["E", "O", "N"]
stop_values = ["1", "2"]
byte_values = ["5", "6", "7", "8"]

h = hal.component("gt_vfd")
parser = argparse.ArgumentParser()
ser = minimalmodbus.Instrument(device, slave)

# Parse command line options
def parse_args():
    global device, baudrate, parity, stop_bits, byte_size, slave, max_speed, min_speed
    parser.add_argument("-d", "--device", help="serial device")
    parser.add_argument("-b", "--bits", help="number of bits")
    parser.add_argument("-r", "--rate", help="baudrate")
    parser.add_argument("-p", "--parity", help="parity")
    parser.add_argument("-s", "--stopbits", help="stop bits")
    parser.add_argument("-t", "--slave", help="modbus slave number")
    parser.add_argument("-M", "--maxrpm", help="max motor speed in RPM")
    parser.add_argument("-m", "--minrpm", help="min motor speed in RPM")
    args = parser.parse_args()
    if args.device:
        device = args.device
    if args.bits:
        if args.bits in byte_values:
            byte_size = int(args.bits)
        else:
            print("Invalid byte size - using default of {}".format(byte_size))
            print("Must be one of ", byte_values)
    if args.rate:
        if args.rate in baud_values:
            baudrate = int(args.rate)
        else:
            print("Invalid baud rate - using default of {}".format(baudrate))
            print("Must be one of ", baud_values)
    if args.parity:
        if args.parity in parity_values:
            parity = args.parity
        else:
            print("Invalid parity setting - using default of {}".format(parity))
            print("Must be one of ", parity_values)
    if args.stopbits:
        if args.stopbits in stop_values:
            stop_bits = int(args.stopbits)
        else:
            print("Invalid stop bits - using default of {}".format(stop_bits))
            print("Must be one of ", stop_values)
    if args.slave:
        if 1 <= int(args.slave) <= 127:
            slave = int(args.slave)
        else:
            print("Slave address must be between 1 and 127")
    if args.maxrpm:
        if float(args.maxrpm) > min_speed:
            max_speed = float(args.maxrpm)
        else:
            print("Max RPM must be greater than Min RPM")
    if args.minrpm:
        if float(args.minrpm) < max_speed:
            min_speed = float(args.minrpm)
        else:
            print("Min RPM must be less than Max RPM")

# Initialize the serial port
def init_serial():
    ser.serial.port = device
    ser.serial.baudrate = baudrate
    ser.serial.parity = parity
    ser.serial.stopbits = stop_bits
    ser.serial.bytesize = byte_size
    ser.serial.timeout = .05
    ser.debug = False
#    print(ser)

# Create HAL pins
def init_pins():
    h.newpin('speed-cmd', hal.HAL_FLOAT, hal.HAL_IN)
    h.newpin('speed-fb', hal.HAL_FLOAT, hal.HAL_OUT)
    h.newpin('spindle-on', hal.HAL_BIT, hal.HAL_IN)
    h.newpin('output-amps', hal.HAL_FLOAT, hal.HAL_OUT)
    h.newpin('output-volts', hal.HAL_FLOAT, hal.HAL_OUT)
    h.newpin('fault-info', hal.HAL_U32, hal.HAL_OUT)
    h.newpin('modbus-errors', hal.HAL_U32, hal.HAL_OUT)
    h['modbus-errors'] = 0
    h.ready()

# write VFD registers
# write_register(address, value, decimal places[0], function code[6], signed[false])
# Turn spindle motor on or off
def set_motor_on(state):
    try:
        ser.write_register(0x1000, state, 0, 6)
    except Exception, e:
        h['modbus-errors'] += 1
        motor_is_on = False
        print("Error writing register 0x1000: " + str(e))

# Set spindle speed as percentage of maximum speed
def set_motor_speed():
    if h['speed-cmd'] > max_speed:
        speed_cmd = 100
    elif h['speed-cmd'] < min_speed:
        speed_cmd = (min_speed / max_speed) * 100
    else:
        speed_cmd = (h['speed-cmd'] / max_speed) * 100
    try:
        ser.write_register(0x2000, speed_cmd, 2, 6)
    except Exception, e:
        h['modbus-errors'] += 1
        print("Error writing register 0x2000: " + str(e))
    
# read VFD registers
# read_register(address, decimal places[0], function code[3], signed[false])
def get_amps():
    try:
        h['output-amps'] = float(ser.read_register(0x3004, 1))
    except Exception, e:
        h['modbus-errors'] += 1
        print("Error reading register 0x3004: " + str(e))

def get_speed():
    try:
        h['speed-fb'] = float(ser.read_register(0x3005, 0)) / 60
    except Exception, e:
        h['modbus-errors'] += 1
        print("Error reading register 0x3005: " + str(e))

def get_volts():
    try:
        h['output-volts'] = float(ser.read_register(0x3003, 0))
    except Exception, e:
        h['modbus-errors'] += 1
        print("Error reading register 0x3003: " + str(e))

def get_faults():
    try:
        h['fault-info'] = float(ser.read_register(0x5000, 0))
    except Exception, e:
        h['modbus-errors'] += 1
        print("Error reading register 0x5000: " + str(e))

parse_args()
init_serial()
init_pins()
try:
    while 1:
        time.sleep(period)
        get_amps()
        get_volts()
        get_speed()
        get_faults()
        if h['spindle-on'] is True:
            set_motor_speed()
            if motor_is_on is False:
                motor_is_on = True
                set_motor_on(1)
        elif motor_is_on is True:
            motor_is_on = False
            set_motor_on(5)
except KeyboardInterrupt:
    raise SystemExit

