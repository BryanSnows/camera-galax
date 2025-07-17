import PIL.Image
import PIL.ImageOps
import keyence.LJSwrap as LJSwrap

import ctypes
import sys
import time

import numpy as np
import PIL

##############################################################################
# sample_ImageAcquisition.py: LJ-S Image acquisition sample.
#
# -First half part: Describes how to acquire images via LJSwrap I/F.
# -Second half part: Describes how to display images using additional modules.
#
##############################################################################

TRG_READY = 0x0020           # Bitmask for the trigger ready status.

image_available = False      # Flag to confirm the image acquisition completed.
acquisition_timeout = False  # Flag to confirm the capturing timeout occurred.
processing_timeout = False   # Flag to confirm the processing timeout occurred.
isCommCloseComplete = False  # Flag to confirm ready to close high speed comm.
ysize_acquired = 0           # Number of Y lines of acquired image.
z_val = []                   # The buffer for height image.
lumi_val = []                # The buffer for luminance image.


def main():

    global image_available
    global acquisition_timeout
    global processing_timeout
    global isCommCloseComplete
    global ysize_acquired
    global z_val
    global lumi_val

    ##################################################################
    # CHANGE THIS BLOCK TO MATCH YOUR SENSOR SETTINGS (FROM HERE)
    ##################################################################

    deviceId = 0                  # Set "0" if you use only 1 head.
    interpolate_yline = 1 #1      # Number of interpolated Y lines (up to 8).
    timeout_sec = 5               # Timeout value for the acquiring image
    use_external_trigger = False  # 'True' to control trigger externally.
    use_image_filter = False      # 'True' to use the image filter (Windows).

    ethernetConfig = LJSwrap.LJS8IF_ETHERNET_CONFIG()
    ethernetConfig.abyIpAddress[0] = 192    # IP address
    ethernetConfig.abyIpAddress[1] = 168
    ethernetConfig.abyIpAddress[2] = 1
    ethernetConfig.abyIpAddress[3] = 4
    ethernetConfig.wPortNo = 24691          # Port No.
    HighSpeedPortNo = 24692                 # Port No. for high-speed

    ##################################################################
    # CHANGE THIS BLOCK TO MATCH YOUR SENSOR SETTINGS (TO HERE)
    ##################################################################

    # Check input parameters
    if (interpolate_yline < 1) or (interpolate_yline > 8):
        print("Invalid value of 'interpolate_yline'.")
        print("Set the value between 1 and 8.")
        print("Exit the program.")
        sys.exit()

    # Initialize DLL
    if 'LJS8IF_Initialize' in dir(LJSwrap):
        res = LJSwrap.LJS8IF_Initialize()
        print("LJSwrap.LJS8IF_Initialize:", hex(res))
        if res != 0:
            print("Failed to initialize the library.")
            LJSwrap.LJS8IF_Finalize()
            print("Exit the program.")
            sys.exit()

    # Ethernet open
    res = LJSwrap.LJS8IF_EthernetOpen(0, ethernetConfig)
    print("LJSwrap.LJS8IF_EthernetOpen:", hex(res))
    if res != 0:
        print("Failed to connect contoller.")
        res = LJSwrap.LJS8IF_CommunicationClose(deviceId)
        print("LJSwrap.LJS8IF_CommunicationClose:", hex(res))
        if 'LJS8IF_Initialize' in dir(LJSwrap):
            LJSwrap.LJS8IF_Finalize()
        print("Exit the program.")
        sys.exit()

    # Initialize Hi-Speed Communication
    my_callback_s_a = LJSwrap.LJS8IF_CALLBACK_SIMPLE_ARRAY(callback_s_a)

    res = LJSwrap.LJS8IF_InitializeHighSpeedDataCommunicationSimpleArray(
        deviceId,
        ethernetConfig,
        HighSpeedPortNo,
        my_callback_s_a,
        0)
    print("LJSwrap.LJS8IF_InitializeHighSpeedDataCommunicationSimpleArray:",
          hex(res))
    if res != 0:
        res = LJSwrap.LJS8IF_FinalizeHighSpeedDataCommunication(deviceId)
        print("LJSwrap.LJS8IF_FinalizeHighSpeedDataCommunication:", hex(res))
        res = LJSwrap.LJS8IF_CommunicationClose(deviceId)
        print("LJSwrap.LJS8IF_CommunicationClose:", hex(res))
        if 'LJS8IF_Initialize' in dir(LJSwrap):
            LJSwrap.LJS8IF_Finalize()
        print("\nExit the program.")
        sys.exit()

    # PreStart Hi-Speed Communication
    req = LJSwrap.LJS8IF_HIGH_SPEED_PRE_START_REQ()
    req.bySendPosition = 2
    profinfo = LJSwrap.LJS8IF_HEIGHT_IMAGE_INFO()

    res = LJSwrap.LJS8IF_PreStartHighSpeedDataCommunication(
        deviceId,
        req,
        use_image_filter,
        profinfo)
    print("LJSwrap.LJS8IF_PreStartHighSpeedDataCommunication:", hex(res))
    if res != 0:
        res = LJSwrap.LJS8IF_FinalizeHighSpeedDataCommunication(deviceId)
        print("LJSwrap.LJS8IF_FinalizeHighSpeedDataCommunication:", hex(res))
        res = LJSwrap.LJS8IF_CommunicationClose(deviceId)
        print("LJSwrap.LJS8IF_CommunicationClose:", hex(res))
        if 'LJS8IF_Initialize' in dir(LJSwrap):
            LJSwrap.LJS8IF_Finalize()
        print("\nExit the program.")
        sys.exit()

    # allocate the memory
    xsize = profinfo.wXPointNum
    ysize = profinfo.wYLineNum
    z_val = [0] * xsize * ysize
    lumi_val = [0] * xsize * ysize

    # Start Hi-Speed Communication
    image_available = False
    acquisition_timeout = False
    processing_timeout = False
    res = LJSwrap.LJS8IF_StartHighSpeedDataCommunication(deviceId)
    print("LJSwrap.LJS8IF_StartHighSpeedDataCommunication:", hex(res))
    if res != 0:
        res = LJSwrap.LJS8IF_FinalizeHighSpeedDataCommunication(deviceId)
        print("LJSwrap.LJS8IF_FinalizeHighSpeedDataCommunication:", hex(res))
        res = LJSwrap.LJS8IF_CommunicationClose(deviceId)
        print("LJSwrap.LJS8IF_CommunicationClose:", hex(res))
        if 'LJS8IF_Initialize' in dir(LJSwrap):
            LJSwrap.LJS8IF_Finalize()
        print("\nExit the program.")
        sys.exit()

    # Start Measure
    waitTrigger_sec = 0
    if use_external_trigger is False:
        # Check the  status of the sensor head.
        status = ctypes.c_ushort()
        start_time = time.time()
        while True:
            LJSwrap.LJS8IF_GetAttentionStatus(deviceId, status)
            if status.value & TRG_READY:
                break
            waitTrigger_sec = time.time() - start_time
            if waitTrigger_sec > timeout_sec:
                break
        res = LJSwrap.LJS8IF_Trigger(deviceId)
        print("LJSwrap.LJS8IF_Trigger:", hex(res))
        if res != 0:
            res = LJSwrap.LJS8IF_StopHighSpeedDataCommunication(deviceId)
            print("LJSwrap.LJS8IF_StopHighSpeedDataCommunication:", hex(res))
            res = LJSwrap.LJS8IF_FinalizeHighSpeedDataCommunication(deviceId)
            print("LJSwrap.LJS8IF_FinalizeHighSpeedDataCommu.:", hex(res))
            res = LJSwrap.LJS8IF_CommunicationClose(deviceId)
            print("LJSwrap.LJS8IF_CommunicationClose:", hex(res))
            if 'LJS8IF_Initialize' in dir(LJSwrap):
                LJSwrap.LJS8IF_Finalize()
            print("\nExit the program.")
            sys.exit()

    # wait for the image acquisition complete
    start_time = time.time()
    while True:
        if image_available:
            break
        if time.time() - start_time > timeout_sec - waitTrigger_sec:
            acquisition_timeout = True
            break

    # Stop
    isCommCloseComplete = False
    res = LJSwrap.LJS8IF_StopHighSpeedDataCommunication(deviceId)
    print("LJSwrap.LJS8IF_StopHighSpeedDataCommunication:", hex(res))

    # Finalize
    # Wait for the high speed communication close completed.
    # Or wait until a timeout occurs.
    start_time = time.time()
    while True:
        if isCommCloseComplete:
            break
        if time.time() - start_time > timeout_sec:
            break
    res = LJSwrap.LJS8IF_FinalizeHighSpeedDataCommunication(deviceId)
    print("LJSwrap.LJS8IF_FinalizeHighSpeedDataCommunication:", hex(res))

    # Close
    res = LJSwrap.LJS8IF_CommunicationClose(deviceId)
    print("LJSwrap.LJS8IF_CommunicationClose:", hex(res))

    # Finalize DLL
    if 'LJS8IF_Finalize' in dir(LJSwrap):
        LJSwrap.LJS8IF_Finalize()

    if image_available is not True:
        print("\nFailed to acquire image (timeout)")
        print("\nTerminated normally.")
        sys.exit()

    ##################################################################
    # Image processing part:
    #
    # <NOTE> Additional modules are required to execute the next block.
    # -'Numpy' for handling array data.
    #
    # If you want to skip,
    # set the next conditional branch to 'False'.
    #
    ##################################################################
    if True:
        if interpolate_yline > 1:
            # Interpolation
            tmp = np.reshape(z_val, (ysize, xsize))
            tmp = np.tile(tmp, interpolate_yline)
            z_val = tmp.reshape(ysize*interpolate_yline*xsize)

            tmp = np.reshape(lumi_val, (ysize, xsize))
            tmp = np.tile(tmp, interpolate_yline)
            lumi_val = tmp.reshape(ysize*interpolate_yline*xsize)

            # Update the profile information
            profinfo.wYLineNum *= interpolate_yline
            ysize = profinfo.wYLineNum
            profinfo.dwPitchY = int(profinfo.dwPitchY / interpolate_yline)

    else:
        interpolate_yline = 1

    ##################################################################
    # Display part:
    #
    # <NOTE> Additional modules are required to execute the next block.
    # -'Numpy' for handling array data.
    # -'Pillow' for 2D image display.
    # -'matplotlib' for profile display.
    #
    # If you want to skip,
    # set the next conditional branch to 'False'.
    #
    ##################################################################
    if True:
        fig = plt.figure(figsize=(8.0, 2*interpolate_yline+1))
        plt.subplots_adjust(hspace=0.5)

        # Height image display
        img1 = PIL.Image.new('I', (xsize, ysize))
        img1.putdata(list(map(int, z_val)))
        im_list1 = np.asarray(img1)
        np.savetxt('mobo1.csv', im_list1)

        # Luminance image display
        img2 = PIL.Image.new('I', (xsize, ysize))        
        img2.putdata(list(map(int, lumi_val)))
        im_list2 = np.asarray(img2)
        mobo = PIL.Image.fromarray(im_list2)
        mobo = PIL.ImageOps.grayscale(mobo)
        mobo.save('mobo1.png')
    return


###############################################################################
# Callback function
# It is called when the specified number of profiles are received.
###############################################################################
def callback_s_a(p_header,
                 p_height,
                 p_lumi,
                 luminance_enable,
                 xpointnum,
                 profnum,
                 notify, user):

    global ysize_acquired
    global image_available
    global processing_timeout
    global z_val
    global lumi_val
    global isCommCloseComplete

    if (notify == 0) or (notify == 0x10000):
        if profnum != 0:
            if (image_available is False) and (acquisition_timeout is False):
                processing_timeout = p_header.contents.byProcTimeout > 0
                for i in range(xpointnum * profnum):
                    z_val[i] = p_height[i]
                    if luminance_enable == 1:
                        lumi_val[i] = p_lumi[i]

                ysize_acquired = profnum
                image_available = True

    if (notify == 1):
        isCommCloseComplete = True
    return


def get_profilemeter_image_bytes():
    main()
    try:
        with open('mobo1.png', 'rb') as f:
            return f.read()
    except Exception as e:
        print(f"[Profilemeter] Error reading mobo1.png: {e}")
        return b''


if __name__ == '__main__':
    main()