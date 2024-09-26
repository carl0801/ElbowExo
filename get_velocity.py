# get_velocity.py
from ctypes import *
import sys

path = 'C:\\Users\\emilr\\Documents\\P5\\exo\\EPOS-Windows-DLL-En\\Microsoft Visual C++\\Example VC++\\EposCmd64.dll'
cdll.LoadLibrary(path)
epos = CDLL(path)

NodeID = 31
keyhandle = 0
pErrorCode = c_uint()

def GetVelocityIs(keyhandle):
    pVelocityIs = c_long()
    pErrorCode = c_uint()

    ret = epos.VCS_GetVelocityIs(keyhandle, NodeID, byref(pVelocityIs), byref(pErrorCode))

    if ret == 1:
        return pVelocityIs.value
    else:
        return None

# Open USB Port
keyhandle = epos.VCS_OpenDevice(b'EPOS4', b'MAXON SERIAL V2', b'USB', b'USB0', byref(pErrorCode))

if keyhandle != 0:
    velocity = GetVelocityIs()
    if velocity is not None:
        print(f'Velocity Actual Value: {velocity} [rpm]')
    else:
        print('GetVelocityIs failed')
    epos.VCS_CloseDevice(keyhandle, byref(pErrorCode))
else:
    print('Could not open Com-Port')