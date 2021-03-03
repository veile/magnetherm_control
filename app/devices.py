    # -*- coding: utf-8 -*-
"""
Created on Wed Sep  9 12:32:52 2020

@author: Veile
"""
import serial
import time
import numpy as np
import pickle
from app.utils import change_state

class WrongDeviceError(Exception):
    """Base class for wrong device"""

class ToneGenerator():
    endchar = "\r\n"

    def __init__(self, port, baudrate=9600):

        self.ser = serial.Serial(port=port,
                                 baudrate=baudrate)

        # Asks for device identification
        cmd = "*IDN?"+self.endchar
        self.ser.write(cmd.encode('utf-8'))

        time.sleep(0.5)

        # Reads return message
        self.ID = ''
        while self.ser.in_waiting > 0:
            self.ID += self.ser.readline().decode('utf-8')

        # Sets default settings
        # self.output('OFF')
        # self.amplitude(6)
        # self.waveform('SQUARE')
        # self.symmetry(50)


    def output(self, state):
        s = state.upper()
        if s not in ['ON', 'OFF']:
            raise NameError("%s is not a valid output mode" %s)

        cmd = 'OUTPUT '+s+self.endchar
        self.ser.write(cmd.encode('utf-8'))

    def error_status(self):
        cmd = 'ERR?'+self.endchar
        self.ser.write(cmd.encode('utf-8'))

        # Reads return message
        out = ''
        while self.ser.in_waiting > 0:
            out += self.ser.readline().decode('utf-8')
        return out


    def amplitude(self, amplitude, unit='VPP'):
        # Checks if input is allowed
        if not 0.005 < amplitude < 20:
            raise ValueError("Amplitude is not within required range 5mV-20V")

        unit = unit.upper()
        if unit not in ['VPP', 'VRMS', 'DBM']:
            raise NameError("Amplitude Type %s is not valid" %unit)


        cmd = 'AMPUNIT ' + unit + ';AMPL ' + str(amplitude) + self.endchar
        self.ser.write(cmd.encode('utf-8'))

    def frequency(self, f):
        cmd = 'WAVFREQ ' + str(f) + self.endchar
        self.ser.write(cmd.encode('utf-8'))

    def waveform(self, form):
        form = form.upper()
        if form not in ['SINE', 'SQUARE', 'TRIANG', 'DC', '+PULSE', '-PULSE']:
            raise NameError("Waveform %s is not valid" %form)

        cmd = 'WAVE ' + form + self.endchar
        self.ser.write(cmd.encode('utf-8'))


    def symmetry(self, value):
        if 0 <= value <= 100:
            cmd = 'SYMM ' + str(value) + self.endchar
            self.ser.write(cmd.encode(('utf-8')))
        else:
            raise ValueError("Symmetry has to be a float between 0-100")

    def close(self):
        self.ser.close()

class PowerSupply():
    endchar = "\r\n"
    wait = 0.5 #s

    def __init__(self, port, baudrate=9600):

        self.ser = serial.Serial(port=port,
                                 baudrate=baudrate)


        # Asks for device identification
        cmd = "*IDN?" + self.endchar
        self.ser.write(cmd.encode('utf-8'))

        time.sleep(self.wait)
        # Reads return message
        self.ID = ''
        while self.ser.in_waiting > 0:
            self.ID += self.ser.readline().decode('utf-8')
        self.ID = str(self.ID)
        # if self.ID != "???":
        #     raise WrongDeviceError("Unexpected device: %s." % self.ID)

        # Applies 'Default Settings'
        cmd = "V1 0; I1 0" + self.endchar
        self.ser.write(cmd.encode('utf-8'))

    def get_V(self):
        cmd = 'V1O?' + self.endchar
        self.ser.write(cmd.encode('utf-8'))
        time.sleep(self.wait)
        # Reads return message
        out = ''
        while self.ser.in_waiting > 0:
            out += self.ser.readline().decode('utf-8')
        return out

    def get_I(self):
        cmd = 'I1O?' + self.endchar
        self.ser.write(cmd.encode('utf-8'))
        time.sleep(self.wait)
        # Reads return message
        out = ''
        while self.ser.in_waiting > 0:
            out += self.ser.readline().decode('utf-8')
        return out

    def get_output(self):
        cmd = 'OP1?' + self.endchar
        self.ser.write(cmd.encode('utf-8'))
        time.sleep(self.wait)
        # Reads return message
        out = ''
        while self.ser.in_waiting > 0:
            out += self.ser.readline().decode('utf-8')
        return out

    def status(self):
        V = self.get_V()
        I = self.get_I()
        OP = self.get_output()

        status = V+I+OP
        return status


    def set_V(self, V):
        # Checks if input is allowed
        if not 0 <= V <= 60:
            raise ValueError("Voltage is not within required range 0-60V")

        cmd = 'V1 ' + str(V) + self.endchar
        self.ser.write(cmd.encode('utf-8'))

    def set_I(self, I):
        # Checks if input is allowed
        if not 0 <= I <= 30:
            raise ValueError("Current is not within required range 0-20A")

        cmd = 'I1 ' + str(I) + self.endchar
        self.ser.write(cmd.encode('utf-8'))

    def set(self, V, I):
        self.set_V(V)
        self.set_I(I)

    def set_output(self, state):
        modes = {'OFF': 0,
                 'ON': 1}
        if isinstance(state, str):
            s = state.upper()
            if s not in ['OFF', 'ON']:
                raise NameError("%s is not a valid output mode!"%s)
            mode = modes[s]
        else:
            if state not in [0, 1]:
                raise NameError("%s is not a valid input" %str(state))
            mode = state

        cmd = 'OP1 ' + str(mode) + self.endchar
        self.ser.write(cmd.encode('utf-8'))

    def close(self):
        self.ser.close()


def scan(tone, power, freqs, V, I):
    # duration = 2 #
    currents = []
    current = []

    power.set(V, I)
    tone.frequency(freqs[0])
    time.sleep(0.5)

    power.set_output('ON')
    tone.output('ON')
    for f in freqs:
        tone.frequency(f)
        # start = time.time()
        # while (time.time()-start) < duration:
        time.sleep(0.5)
        read = power.get_I()
        # print(read)
        currents.append( float(read[:5]) )
        # currents.append( np.array(current).mean() )

    power.set(0,0)
    power.set_output('OFF')
    return np.array(currents)

def tune_debug(T, P, f):
    freqs = np.linspace((f-5)*1e3, (f+5)*1e3, 11, endpoint=True)
    current = scan(T, P, freqs, 40.9/3, 20)


    mx = np.argmax(current)
    freqs2 = np.linspace(freqs[mx]-1e3, freqs[mx]+1e3, 10, endpoint=True)
    current2 = scan(T, P, freqs2, V=40.9 / 3, I=20)

    T.frequency(freqs2[np.argmax(current2)])


    plt.plot(freqs, current)
    plt.plot(freqs2, current2, 'r')
    plt.show()

def exposure(T, P, t, V, I):
    volts = []
    tV = []
    amps = []
    tI = []


    P.set(V, I)
    P.set_output('ON')
    start = time.time()
    while (time.time()-start) < t:
        readV = P.get_V()
        tV.append( time.time()-start )

        readI = P.get_I()
        tI.append( time.time()-start )

        volts.append(float(readV[:5]))
        amps.append(float(readI[:5]))

    P.set_output('OFF')
    P.set(0, 0)
    return tV, volts, tI, amps


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    T = ToneGenerator('COM9')
    P = PowerSupply('COM7')

    tune_debug(T, P, f=406)
    tV, V, tI, I = exposure(T, P, t=5, V=45, I=10)

    plt.plot(tV, V)
    plt.twinx()
    plt.plot(tI, I)
    plt.show()