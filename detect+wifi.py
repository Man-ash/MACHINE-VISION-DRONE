# Face Detection Example
#
# This example shows off the built-in face detection feature of the OpenMV Cam.
# 
# Face detection works by using the Haar Cascade feature detector on an image. A
# Haar Cascade is a series of simple area contrasts checks. For the built-in
# frontalface detector there are 25 stages of checks with each stage having
# hundreds of checks a piece. Haar Cascades run fast because later stages are
# only evaluated if previous stages pass. Additionally, your OpenMV Cam uses
# a data structure called the integral image to quickly execute each area
# contrast check in constant time (the reason for feature detection being
# grayscale only is because of the space requirment for the integral image).


# Prepared by Manash Pratim Kakati

import sensor, image, time, network, usocket, sys

SSID ='OPENMV_AP'    # Network SSID
KEY  ='1234567890'    # Network key (must be 10 chars)
HOST = ''           # Use first available interface
PORT = 8080         # Arbitrary non-privileged port

# Reset sensor
sensor.reset()


import time
from pyb import LED

red_led   = LED(1)
green_led = LED(2)
blue_led  = LED(3)
ir_led    = LED(4)

def led_control(x):

    if   (x&2)==0: green_led.off()
    elif (x&2)==2: green_led.on()
    if   (x&4)==0: blue_led.off()
    elif (x&4)==4: blue_led.on()



# Sensor settings
sensor.set_contrast(1)
sensor.set_gainceiling(16)
sensor.set_brightness(1)
sensor.set_saturation(1)
# QVGA and RGB565 ARE MODEFIED BY MUHAMMAD ANAS.
sensor.set_framesize(sensor.QVGA)
sensor.set_pixformat(sensor.RGB565)

# Load Haar Cascade
# By default this will use all stages, lower satges is faster but less accurate.
face_cascade = image.HaarCascade("frontalface", stages=25)
print(face_cascade)

# Init wlan module in AP mode.
wlan = network.WINC(mode=network.WINC.MODE_AP)
wlan.start_ap(SSID, key=KEY, security=wlan.WEP, channel=2)

# You can block waiting for client to connect
#print(wlan.wait_for_sta(10000))

def start_streaming(s):
    print ('Waiting for connections..')
    client, addr = s.accept()
    # set client socket timeout to 2s
    client.settimeout(2.0)
    print ('Connected to ' + addr[0] + ':' + str(addr[1]))

    # Read request from client
    data = client.recv(1024)
    # Should parse client request here

    # Send multipart header
    client.send("HTTP/1.1 200 OK\r\n" \
                "Server: OpenMV\r\n" \
                "Content-Type: multipart/x-mixed-replace;boundary=openmv\r\n" \
                "Cache-Control: no-cache\r\n" \
                "Pragma: no-cache\r\n\r\n")

# FPS clock
clock = time.clock()

while (True):

    for i in range(16):
        led_control(i)

    clock.tick() # Track elapsed milliseconds between snapshots().
    # Capture snapshot
    img = sensor.snapshot()
    cframe = img.compressed(quality=35)
    header = "\r\n--openmv\r\n" \
             "Content-Type: image/jpeg\r\n"\
             "Content-Length:"+str(cframe.size())+"\r\n\r\n"
    client.send(header)
    client.send(cframe)
        
    # Find objects.
    # Note: Lower scale factor scales-down the image more and detects smaller objects.
    # Higher threshold results in a higher detection rate, with more false positives.
    objects = img.find_features(face_cascade, threshold=0.75, scale_factor=1.25)


    # Draw objects
    for r in objects:
        img.draw_rectangle(r)


    # Print FPS.
    # Note: Actual FPS is higher, streaming the FB makes it slower.
    print(clock.fps())

while (True):
     # Create server socket
    s = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
    try:
        # Bind and listen
        s.bind([HOST, PORT])
        s.listen(5)

        # Set server socket timeout
        # NOTE: Due to a WINC FW bug, the server socket must be closed and reopened if
        # the client disconnects. Use a timeout here to close and re-create the socket.
        s.settimeout(3)
        start_streaming(s)
    except OSError as e:
        s.close()
        print("socket error: ", e)
        #sys.print_exception(e)
