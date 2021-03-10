import sys
import glob
import os
import pandas as pd
import numpy as np
import math
import serial.tools.list_ports
from datetime import datetime


matrix_sheet = pd.DataFrame(
    np.array([
        [9, 200, 161.3,     23.5,   24.6,   23],
        [9, 88,  242,       26,     21.8,   20],
        [9, 26,  405.45,    31.2,   20.5,   16],
        [9, 15,  572.6,     31.8,   17.3,   14],
        [9, 6.2, 924.6,     31.4,   13.4,   12],
        [17, 200, 105.2,     26.77,  17,     25],
        [17, 88,  158.12,    26.25,  13.55,  17],
        [17, 26,  264.8,     36,     14.1,   17],
        [17, 15,  373.85,    40.4,   13.5,   16],
        [17, 6.2, 602.5,     43.4,   12,     12],
        [18, 200, 161.5,     36.2,   28,     46],
        [18, 88,  242.3,     40.2,   23.85,  39],
        [18, 26, 406,       40.9,   20,     32],
        [18, 15,  573.5,     46.8,   19,     29],
        [18, 6.2,  927.7,     38.3,   13.5,   18]
    ]),
    columns=[
        "Coil Turns",
        "Capacitance [nF]",
        "Frequency [kHz]",
        "Voltage [V]",
        "Current [A]",
        "Flux Density [mT]"
    ]
)

# B = k1*I
mu0 = 4 * np.pi * 1e-7
N = 18
L = 54e-3
R1 = 13e-3
R2 = 23e-3

k1 = 1/2 * mu0*N/(R2-R1)*np.log((np.sqrt(4*R2**2+L**2)+2*R2)/(np.sqrt(4*R1**2+L**2)+2*R1))*1e3

# Icoil = k2(f)*Iset
k2 = lambda f: -8.79797909e-07*f**2 - 8.52364188e-04*f + 4.99950719e+00

def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def get_devices():
    if sys.platform.startswith('win'):
        return [x.device for x in serial.tools.list_ports.comports()]
    elif sys.platform.startswith('linux'):
        return glob.glob('/dev/tty[A-Za-z]*')
    else:
        raise OSError("Operating system not implemented yet")


def get_files(dir="./data/"):
    files = os.listdir(dir)
    return [{'Filename': f,
             'Filesize': convert_size(os.path.getsize(dir+f)),
             'Last Modified': datetime.fromtimestamp(os.path.getmtime(dir+f)).strftime('%Y-%m-%d'),
             'File Created': datetime.fromtimestamp(os.path.getctime(dir+f)).strftime('%Y-%m-%d %H:%M')}
            for f in files]


# def current_state():
#     file = "state.txt"
#     with open(file, 'r') as f:
#         state = f.read()
#
#     return "%s"%state

# def change_state(newstate, which):
#     file = "state.txt"
#     which = which.lower()
#     state = current_state().split('\n\n')
#
#     with open(file, 'w') as f:
#         if which == 'current':
#             state[0] = "**Current State**: "+newstate
#         elif which == 'freq':
#             state[1] = "**Frequency**: " + newstate
#
#         f.write('\n\n'.join(state))


# def get_frequency():
#     state = current_state().split('\n\n')
#     frequency = state[1].split()[1]
#     return float(frequency)


def coil_current(f, power_current):
    return k2(f)*power_current


def current_to_field(f, power_current, r=18e-3, L=53e-3, N=18):
    I = coil_current(f, power_current)
    return k1*I

def field_to_current(field, f):
    mu0 = 4*np.pi*1e-7
    I = field/k1

    return I/k2(f)

# def exposing():
#     with open('exposing.txt', 'r') as f:
#         status = f.read()
#     return status == 'True'
#
# def set_exposure(state):
#     with open('exposing.txt', 'w') as f:
#         f.write(str(bool(state)))