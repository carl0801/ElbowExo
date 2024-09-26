# get_position.py
from ctypes import *
import sys

path = 'EPOS-Windows-DLL-En\\Microsoft Visual C++\\Example VC++\\EposCmd64.dll'
cdll.LoadLibrary(path)
epos = CDLL(path)

NodeID = 31
keyhandle = 0
pErrorCode = c_uint()

def GetPositionIs():
    pPositionIs = c_long()
    pErrorCode = c_uint()

    ret = epos.VCS_GetPositionIs(keyhandle, NodeID, byref(pPositionIs), byref(pErrorCode))

    if ret == 1:
        return pPositionIs.value
    else:
        return None

# Open USB Port
keyhandle = epos.VCS_OpenDevice(b'EPOS4', b'MAXON SERIAL V2', b'USB', b'USB0', byref(pErrorCode))

if keyhandle != 0:
    position = GetPositionIs()
    if position is not None:
        print(f'Position Actual Value: {position} [inc]')
    else:
        print('GetPositionIs failed')
    epos.VCS_CloseDevice(keyhandle, byref(pErrorCode))
else:
    print('Could not open Com-Port')