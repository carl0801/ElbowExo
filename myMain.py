from ctypes import *
import subprocess   
import time

# Folder created for example: /home/pi/src/python/
# Copy maxon motor Linux Library arm v7 into this folder
# Library must match according your cpu, eg. PI3 has arm v7
# EPOS Comand Library can be found here, when EPOS Studio has been installed:
# C:\Program Files (x86)\maxon motor ag\EPOS IDX\EPOS4\04 Programming\Linux Library
path = 'EPOS-Windows-DLL-En\\Microsoft Visual C++\\Example VC++\\EposCmd64.dll'
cdll.LoadLibrary(path)
epos=CDLL(path)

# Node ID must match with Hardware Dip-Switch setting of EPOS4
NodeID=31
keyhandle=0
# return variable from Library Functions
ret=0
pErrorCode=c_uint()
pDeviceErrorCode=c_uint()

# initialize port
def init():

    print('Opening Port...')
    keyhandle = epos.VCS_OpenDevice(b'EPOS4', b'MAXON SERIAL V2', b'USB', b'USB0', byref(pErrorCode))
    # set motortype to EPOS4 BLDC
    ret = epos.VCS_SetMotorType(keyhandle, NodeID, 11, byref(pErrorCode))
    # set motor parameters: nominal current, max current, thermal time constant, and pole pair count(det er indstillet)
    ret = epos.VCS_SetEcMotorParameter(keyhandle, NodeID, 218, 30000, 5, 2)
    if ret == 1:
        print('Motor parameters set')
    else:
        print('Motor parameters not set')
    if keyhandle != 0:
        print('Keyhandle: %8d' % keyhandle)

        # Verify Error State of EPOS4
        ret = epos.VCS_GetDeviceErrorCode(keyhandle, NodeID, 1, byref(pDeviceErrorCode), byref(pErrorCode))
        print('Device Error: %#5.8x' % pDeviceErrorCode.value)

        # Device Error Evaluation
        if pDeviceErrorCode.value == 0:
            # Set Operation Mode PPM
            ret = epos.VCS_ActivateProfilePositionMode(keyhandle, NodeID, byref(pErrorCode))

            # Profile Velocity=500rpm / Acceleration=1000rpm/s / Deceleration=1000rpm/s
            ret = epos.VCS_SetPositionProfile(keyhandle, NodeID, 2500, 10000, 10000, byref(pErrorCode))

            # Read Position Actual Value with VCS_GetObject()
            #ret = GetPositionIs()
            
            ret = epos.VCS_SetEnableState(keyhandle, NodeID, byref(pErrorCode))
            print('Device Enabled')

            return keyhandle


        else:
            print('EPOS4 is in Error State: %#5.8x' % pDeviceErrorCode.value)
            print('EPOS4 Error Description can be found in the EPOS4 Firmware Specification')

        # Close Com-Port
        ret = epos.VCS_CloseDevice(keyhandle, byref(pErrorCode))
        print('Error Code Closing Port: %#5.8x' % pErrorCode.value)
    else:
        print('Could not open Com-Port')
        print('Keyhandle: %8d' % keyhandle)
        print('Error Opening Port: %#5.8x' % pErrorCode.value)

def print_pos_vel():
    # Print position and velocity using subprocess
    p = subprocess.Popen(["python", "exo/get_position.py"], stdout=subprocess.PIPE)
    out, err = p.communicate()
    out = out.decode("utf-8")
    print(out)

    v = subprocess.Popen(["python", "exo/get_velocity.py"], stdout=subprocess.PIPE)
    out, err = v.communicate()
    out = out.decode("utf-8")
    print(out)

def GetPositionIs(keyhandle):
    pPositionIs = c_long()
    pErrorCode = c_uint()

    ret = epos.VCS_GetPositionIs(keyhandle, NodeID, byref(pPositionIs), byref(pErrorCode))

    if ret == 1:
        return pPositionIs.value
    else:
        return None

def GetCurrentVelocity(keyhandle):
    pVelocityIs = c_long()
    pErrorCode = c_uint()

    ret = epos.VCS_GetVelocityIs(keyhandle, NodeID, byref(pVelocityIs), byref(pErrorCode))

    if ret == 1:
        return pVelocityIs.value
    else:
        return None

def velocity_control(keyhandle, setVelocity, NodeID, pErrorCode):
        # Activate Velocity Mode
    ret = epos.VCS_ActivateVelocityMode(keyhandle, NodeID, byref(pErrorCode))
    if ret != 1:
        print(f'Failed to activate velocity mode. Error code: {pErrorCode.value}')
        return

    # Set Velocity Must
    ret = epos.VCS_SetVelocityMust(keyhandle, NodeID, setVelocity, byref(pErrorCode))
    if ret != 1:
        print(f'Failed to set velocity must. Error code: {pErrorCode.value}')
        return

    print(f'Moving with velocity: {setVelocity} rpm')


def main():
    keyhandle = init()
    speed = 1100
    velocity_control(keyhandle, speed, NodeID, pErrorCode)
    time.sleep(2)
    currentVel = GetCurrentVelocity(keyhandle)
    print(f'Current velocity: {currentVel}')
    a = input("press Enter to stop motor: " )
    if a is not None:
        # Stop Motor, disable EPOS4
        ret = epos.VCS_SetDisableState(keyhandle, NodeID, byref(pErrorCode))
    
if __name__ == '__main__':
    main()