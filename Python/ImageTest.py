# -*- coding: utf-8 -*-
"""
@author: Rocco Dragone
Simple example that connects to first DataRay device found on system, changes
some settings, and then enters an infinite loop where the 2D image data is requested
and displayed. To end the loop, hit Ctrl+C on your keyboard. 

Search for #TODO for sections of code that may need to be changed for your
application
"""
import requests
import matplotlib.pyplot as plt
import re
import base64
from PIL import Image
import json

# Defining main function
def main():   
    #TODO: Change this to the appropriate url and port for your network setup.
    #Using localhost in lieu of an IP address will considerable overhead

    url = "http://192.168.7.214:18080"
    deviceList=requests.get(url + "/RefreshDeviceList").text
    print(deviceList)
    x=re.findall(r"(?<=\[).*(?=\])", deviceList)[0]
    y=x.split(',')
    deviceName=y[2]
    device_id=y[1].strip()
    print((requests.get(url + "/ConnectCamera/"+device_id)).text)
    width=1024
    height=1024
    x_offset= 0
    y_offest= 0
    binning = 2
    #TODO: Change to something appropriate for your camera and beam diameter
    jsonData={"i_width": width,
        "i_height": height,
        "i_x_offset": x_offset,
        "i_y_offset": y_offest,
        "i_binning": binning,
        "i_num_frames_to_average": 5,
        "b_hypercal_enabled": False,
        "i_auto_exposure_max_us": 100000,
        "i_auto_exposure_min_us": 85,
        "b_auto_exposure_enabled": True,
        "i_exposure_time_us": 2000,
        "d_gamma": 1}
    #ChangeSettings will return ERROR if invalid settings are used.
    print((requests.post(url + "/ChangeSettings/"+device_id, json = jsonData)).text)
    print((requests.get(url + "/StartCamera/"+device_id)).text)
    fig = plt.figure()
    while(True):
        try:
            #check that image matches requested size. It is possible that invalid parameters were used
            settings=requests.get(url + "/GetSettings/"+device_id).text
            settings_dict=json.loads(settings)
            image_width=settings_dict['i_width']
            image_height=settings_dict['i_height']
            image_response=(requests.get(url + "/GetImage/"+device_id,stream=True))
            if image_response =="Invalid image.":
                print(image_response)
                continue
            elif image_response =="No Image Available.":
                print(image_response)
                continue
            else:
                decoded= base64.b64decode(image_response.content)
                img=Image.frombytes('I;16',size=[image_width,image_height],data=decoded)
                plt.imshow(img)
                fig.canvas.draw()
                fig.canvas.flush_events()
                plt.show()
        except KeyboardInterrupt:
            print((requests.get(url + "/StopCamera/"+device_id)).text)
            print((requests.get(url + "/DisconnectCamera/"+device_id)).text)#Stop and disconnect camera
            break

# Using the special variable
# __name__
if __name__=="__main__":
    main()