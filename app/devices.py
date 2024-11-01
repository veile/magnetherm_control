    # -*- coding: utf-8 -*-
"""
Created on Wed Sep  9 12:32:52 2020

@author: Veile
"""
import serial
import time
import random
import sys


if sys.platform.startswith('linux'):
    import board
    import digitalio
    import adafruit_max31856
    from osensapy import osensapy

class WrongDeviceError(Exception):
    """Base class for wrong device"""

class ToneGenerator():
    endchar = "\r\n"
    def __init__(self, port, baudrate=19200):

        self.ser = serial.Serial(port=port,
                                 baudrate=baudrate)

    def comm(self, cmd):
        cmd = cmd + self.endchar
        self.ser.write(cmd.encode('utf-8'))

        time.sleep(.07)

        reply = self.ser.read(self.ser.inWaiting()).decode('utf-8', errors='ignore')
        if reply == '':
            return self.error_status().strip(self.endchar)
        else:
            return reply.strip(self.endchar)

    def get_id(self):
        # Asks for device identification
        return self.comm('*IDN?')

    def error_status(self):
        return self.comm('EER?')

    def set_output(self, state):
        s = state.upper()
        if s not in ['ON', 'OFF']:
            raise NameError("%s is not a valid output mode" %s)

        return self.comm('OUTPUT '+s)

    def set_amplitude(self, amplitude, unit='VPP'):
        # Checks if input is allowed
        if not 0.005 < amplitude < 20:
            raise ValueError("Amplitude is not within required range 5mV-20V")

        unit = unit.upper()
        if unit not in ['VPP', 'VRMS', 'DBM']:
            raise NameError("Amplitude Type %s is not valid" %unit)

        cmd = 'AMPUNIT ' + unit + ';AMPL ' + str(amplitude)
        return self.comm(cmd)

    # Implement check on frequency
    def set_frequency(self, f):
        return self.comm('WAVFREQ '+ str(f))

    def set_waveform(self, form):
        form = form.upper()
        if form not in ['SINE', 'SQUARE', 'TRIANG', 'DC', '+PULSE', '-PULSE']:
            raise NameError("Waveform %s is not valid" %form)

        return self.comm('WAVE ' + form)

    def set_symmetry(self, value):
        if 0 <= value <= 100:
            return self.comm('SYMM ' + str(value))
        else:
            raise ValueError("Symmetry has to be a float between 0-100")


class PowerSupply():
    endchar = "\r\n"

    def __init__(self, port, baudrate=9600):

        self.ser = serial.Serial(port=port,
                                 baudrate=baudrate)

        self.set_default()

    def comm(self, cmd):
        cmd = cmd + self.endchar
        self.ser.write(cmd.encode('utf-8'))

        time.sleep(.07)

        reply = self.ser.read(self.ser.inWaiting()).decode('utf-8', errors='ignore')
        if reply == '':
            return self.error_status().strip(self.endchar)
        else:
            return reply.strip(self.endchar)

    def error_status(self):
        return self.comm('EER?')

    def get_id(self):
        return self.comm('*IDN?')

    def get_V(self):
        return self.comm('V1O?')

    def set_V(self, V):
        # Checks if input is allowed
        if not 0 <= V <= 60:
            raise ValueError("Voltage is not within required range 0-60V")
        return self.comm('V1 ' + str(V))

    def get_I(self):
        return self.comm('I1O?')

    def set_I(self, I):
        # Checks if input is allowed
        if not 0 <= I <= 30:
            raise ValueError("Current is not within required range 0-20A")
        return self.comm('I1 ' + str(I))

    def set(self, V, I):
        self.set_V(V)
        self.set_I(I)

    def get_output(self):
        cmd = 'OP1?' + self.endchar
        self.ser.write(cmd.encode('utf-8'))
        time.sleep(self.wait)
        # Reads return message
        out = ''
        while self.ser.in_waiting > 0:
            out += self.ser.readline().decode('utf-8')
        return out

    def set_output(self, state):
        modes = {'OFF': 0,
                 'ON': 1}
        if isinstance(state, str):
            s = state.upper()
            if s not in ['OFF', 'ON']:
                raise NameError("%s is not a valid output mode!" %s)
            mode = modes[s]
        else:
            if state not in [0, 1]:
                raise NameError("%s is not a valid input" %str(state))
            mode = state

        return self.comm('OP1 ' + str(mode))

    def set_default(self):
        self.set(0, 0)
        self.set_output('OFF')

    def status(self):
        V = self.get_V()
        I = self.get_I()
        OP = self.get_output()

        status = V+I+OP
        return status


class fiber():
    '''
    id = 247 single channel transmitter
    id = 40  triple channel transmitter
    '''
    def __init__(self, port, id=40):
        self.transmitter = osensapy.Transmitter(port, id, baudrate=115200)

    def __len__(self):
        return 3

    def initiate(self):
    # Compability between TC and fibre
        pass
    
    def get_T(self):
        return [reading[1] for reading in self.transmitter.fast_batch(3)]
        
        
    def reinitialize(self):
        port = self.transmitter.modbus.serial.port
        self.transmitter.close()
        self.transmitter = osensapy.Transmitter(port, 247, baudrate=115200)


class TC():
    """
    Class that handles the SPI driven thermocouple amplifier from Adafruit (MAX 31856)
    """
    def __init__(self, CS_PINS=['D5'], tc_type='N'):
        self.CS_PINS = CS_PINS
        
        spi = board.SPI()
        
        cs = [digitalio.DigitalInOut(getattr(board, pin)) for pin in self.CS_PINS]
        for c in cs:
            c.direction = digitalio.Direction.OUTPUT
        
        self.tcs = [adafruit_max31856.MAX31856(spi, c, thermocouple_type=getattr(adafruit_max31856.ThermocoupleType, tc_type)) for c in cs]
        for tc in self.tcs:

             tc.noise_rejection = 50


    def __len__(self):
        return len(self.tcs)

    def initiate(self):
        [tc.initiate_one_shot_measurement() for tc in self.tcs]
    
    def get_T(self):
        # [tc.initiate_one_shot_measurement() for tc in self.tcs]
        
        # while self.tcs[-1].oneshot_pending:
            # pass
            
        print(self.tcs[0].fault)
        
    
        if self.tcs[0].oneshot_pending:
            raise Exception('Temperature not initialised!')
        return [tc.unpack_temperature() for tc in self.tcs]
        
    def set_type(self, tc_type='N'):
        thermocouple_type = getattr(adafruit_max31856.ThermocoupleType, tc_type)
        [tc._set_thermocouple_type(thermocouple_type) for tc in self.tcs]

# class TC():
    # def __init__(self, addresses):
        # for i in range(10):
            # try:
                # self.mcp = [MCP9600(a) for a in addresses]
            # except:
                # print("Attempt %i out of 10" %i)
                # continue

    # def __len__(self):
        # return len(self.mcp)

    # def initiate():
        # pass

    # def get_T(self):
        # T = [tc.get_hot_junction_temperature() for tc in self.mcp]
        # return T

    # def set_type(self, type):
        # if type not in ['K', 'J', 'T', 'N', 'S', 'E', 'B', 'R']:
            # raise Exception('Not supported thermocouple type')

        # else:
            # for tc in self.mcp:
                # tc.set_thermocouple_type(type)

    # def set_adc(self, res):
        # if res not in [12, 14, 16, 18]:
            # raise Exception("ADC Resolution must be 12, 14, 16 or 18")

        # else:
            # for tc in self.mcp:
                # tc._mcp9600.set('DEVICE_CONFIG', adc_resolution=res)
                
# ---------------------------DUMMY OBJECTS-----------------------------------------------#
class dummy_ToneGenerator():
    endchar = "\r\n"
    def __init__(self, port, baudrate=19200):
        self.ser = ''

    def comm(self, cmd):
        cmd = cmd + self.endchar
        return "Sent CMD: %s" %cmd

    def get_id(self):
        # Asks for device identification
        return self.comm('*IDN?')

    def error_status(self):
        return self.comm('EER?')

    def set_output(self, state):
        s = state.upper()
        if s not in ['ON', 'OFF']:
            raise NameError("%s is not a valid output mode" %s)

        return self.comm('OUTPUT '+s)

    def set_amplitude(self, amplitude, unit='VPP'):
        # Checks if input is allowed
        if not 0.005 < amplitude < 20:
            raise ValueError("Amplitude is not within required range 5mV-20V")

        unit = unit.upper()
        if unit not in ['VPP', 'VRMS', 'DBM']:
            raise NameError("Amplitude Type %s is not valid" %unit)

        cmd = 'AMPUNIT ' + unit + ';AMPL ' + str(amplitude)
        return self.comm(cmd)

    # Implement check on frequency
    def set_frequency(self, f):
        return self.comm('WAVFREQ '+ str(f))

    def set_waveform(self, form):
        form = form.upper()
        if form not in ['SINE', 'SQUARE', 'TRIANG', 'DC', '+PULSE', '-PULSE']:
            raise NameError("Waveform %s is not valid" %form)

        return self.comm('WAVE ' + form)

    def set_symmetry(self, value):
        if 0 <= value <= 100:
            return self.comm('SYMM ' + str(value))
        else:
            raise ValueError("Symmetry has to be a float between 0-100")

class dummy_PowerSupply():
    endchar = "\r\n"

    def __init__(self, port, baudrate=9600):
        self.ser = ''


    def comm(self, cmd):
        cmd = cmd + self.endchar
        return 'Sent CMD: %s' %cmd

    def error_status(self):
        return self.comm('EER?')

    def get_id(self):
        return self.comm('*IDN?')

    def get_V(self):
        return "%iV" %random.randint(0, 5)

    def set_V(self, V):
        # Checks if input is allowed
        if not 0 <= V <= 60:
            raise ValueError("Voltage is not within required range 0-60V")
        return self.comm('V1 ' + str(V))

    def get_I(self):
        return "%iA" %random.randint(0, 5)

    def set_I(self, I):
        # Checks if input is allowed
        if not 0 <= I <= 30:
            raise ValueError("Current is not within required range 0-20A")
        return self.comm('I1 ' + str(I))

    def set(self, V, I):
        if I == 0:
            print('PSU OFF')
        else:
            print('PSU ON')

        self.set_V(V)
        self.set_I(I)

    def get_output(self):
        cmd = 'OP1?' + self.endchar
        self.ser.write(cmd.encode('utf-8'))
        time.sleep(self.wait)
        # Reads return message
        out = ''
        while self.ser.in_waiting > 0:
            out += self.ser.readline().decode('utf-8')
        return out

    def set_output(self, state):
        modes = {'OFF': 0,
                 'ON': 1}
        if isinstance(state, str):
            s = state.upper()
            if s not in ['OFF', 'ON']:
                raise NameError("%s is not a valid output mode!" % s)
            mode = modes[s]
        else:
            if state not in [0, 1]:
                raise NameError("%s is not a valid input" % str(state))
            mode = state

        return self.comm('OP1 ' + str(mode))

    def status(self):
        V = self.get_V()
        I = self.get_I()
        OP = self.get_output()

        status = V + I + OP
        return status

    def set_default(self):
        self.set_output('OFF')
        self.set(0, 0)


class dummy_fiber():
    def __init__(self, port):
        self.port = port

    def __len__(self):
        return 3

    def initiate(self):
    # Compability between TC and fibre
        pass

    def get_T(self):
        T = [random.randint(50, 100) for i in range(3)]
        return T

class dummy_TC():
        """
        Class that handles the SPI driven thermocouple amplifier from Adafruit (MAX 31856)
        """
        def __init__(self, CS_PINS=['D5'], tc_type='N'):
            self.tcs = CS_PINS

        def __len__(self):
            return len(self.tcs)

        def initiate(self):
            pass

        def get_T(self):
            T = [random.randint(50, 100) for i in range(len(self))]
            return T

        def set_type(self, tc_type='N'):
            if type not in ['K', 'J', 'T', 'N', 'S', 'E', 'B', 'R']:
                raise Exception('Not supported thermocouple type')

            else:
                print("Set thermocouple to type %s" %type)

# class dummy_TC():
#     def __init__(self, addresses):
#         self.mcp = addresses
#
#     def __len__(self):
#         return len(self.mcp)
#
#     def get_T(self):
#         T = [random.randint(50, 100) for i in range(len(self))]
#         return T
#
#     def set_type(self, type):
#         if type not in ['K', 'J', 'T', 'N', 'S', 'E', 'B', 'R']:
#             raise Exception('Not supported thermocouple type')
#
#         else:
#             print("Set thermocouple to type %s" %type)
#
#     def set_adc(self, res):
#         if res not in [12, 14, 16, 18]:
#             raise Exception("ADC Resolution must be 12, 14, 16 or 18")
#
#         else:
#             print("Set res to %i" %res)
