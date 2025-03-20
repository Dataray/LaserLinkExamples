# -*- coding: utf-8 -*-
"""
@author: Rocco Dragone
Simple example that connects to first DataRay device found on system, changes
some settings, and runs camera until a valid image is retrieved. The example
then prints out some of the calculated results and generates a plot
of the 2D image with the major and minor profiles. Finally, this example will
save an HDF5 file on the LaserLink server.

Search for #TODO for sections of code that may need to be changed for your
application
"""

import requests
import numpy as np
import matplotlib.pyplot as plt
import base64
from PIL import Image
import re
import json

# Defining main function
def main():   
    #TODO: Change this to the appropriate url and port for your network setup.
    #Using localhost in lieu of an IP address will considerable overhead
    url = "http://192.168.5.222:18080"

    deviceList=requests.get(url + "/RefreshDeviceList").text
    print(deviceList)
    #Use regex to automatically get device_id of first listed device.
    #If you only have one camera, you can hard-code the device_id
    x=re.findall(r"(?<=\[).*(?=\])", deviceList)[0]
    y=x.split(',')
    deviceName=y[2]
    device_id=y[1].strip()
    print((requests.get(url + "/ConnectCamera/"+device_id)).text)
    #TODO: Change to something appropriate for your camera and beam diameter
    width = 2048
    height = 2048
    x_offset= 0
    y_offest= 0
    binning = 1
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
        "i_exposure_time_us": 10000,
        "d_gamma": 1}
    #ChangeSettings will return ERROR if invalid settings are used.
    print((requests.post(url + "/ChangeSettings/"+device_id, json = jsonData)).text)
    print((requests.get(url + "/StartCamera/"+device_id)).text)
    
    #let camera run until we are getting valid images
    image_invalid=True
    while(image_invalid):
        try:
            result_str=requests.get(url + "/GetResults/"+device_id).text
            if result_str.startswith("Invalid image."):
                print(result_str)
                continue
            elif result_str =="No Image Available.":
                continue
            else:
                image_invalid=False
        except KeyboardInterrupt:
            print((requests.get(url + "/StopCamera/"+device_id)).text)
            print((requests.get(url + "/DisconnectCamera/"+device_id)).text)#Stop and disconnect camera
            break
    print((requests.get(url + "/StopCamera/"+device_id)).text)

    #calculated values
    print("Xc (um):"+(requests.get(url + "/GetResult/"+device_id+"/d_CentroidX_um")).text)
    print("Yc (um):"+(requests.get(url + "/GetResult/"+device_id+"/d_CentroidY_um")).text)
    print("ISO11146 Major Diameter (um):"+(requests.get(url + "/GetResult/"+device_id+"/d_ISO11146Major_um")).text)
    print("ISO11146 Minor Diameter (um):"+(requests.get(url + "/GetResult/"+device_id+"/d_ISO11146Minor_um")).text)
    print("Exposure Time (us):"+(requests.get(url + "/GetSetting/"+device_id+"/i_exposure_time_us")).text)
    print("ADC Peak (ADU):"+(requests.get(url + "/GetResult/"+device_id+"/i_ADC_peak_adu")).text)
    print("Baseline (ADU):"+(requests.get(url + "/GetResult/"+device_id+"/d_Baseline")).text)
    
    #2D Image
    #check that image matches requested size. It is possible that invalid parameters were used
    settings=requests.get(url + "/GetSettings/"+device_id).text
    settings_dict=json.loads(settings)
    image_width=settings_dict['i_width']
    image_height=settings_dict['i_height']
    image_response=(requests.get(url + "/GetImage/"+device_id,stream=True))
    decoded= base64.b64decode(image_response.content)
    img=Image.frombytes('I;16',size=[image_width,image_height],data=decoded)
    fig = plt.figure(figsize=[14,7])
    ax_image= plt.subplot2grid((2, 2), (0, 0), rowspan=2,fig=fig)
    ax_image.imshow(img)
    ax_image.set_title("Image")

    #Major Axis
    temp=requests.get(url + "/GetMajorProfile/"+device_id).text
    j=json.loads(temp)
    u=np.array([])
    intensity=np.array([])
    for k in range(j['count']):
        u=np.append(u,k*j['stepsize'])
        intensity = np.append(intensity,j['data'][k])
    ax_major=plt.subplot2grid((2,2),(0,1),fig=fig)
    ax_major.plot(u,intensity)
    ax_major.set_title("Major Axis")
    ax_major.set_ylabel("Intensity (ADU)")

    
    #Minor Axis
    temp=requests.get(url + "/GetMinorProfile/"+device_id).text
    j_minor=json.loads(temp)
    u_minor=np.array([])
    intensity_minor=np.array([])
    for k in range(j_minor['count']):
        u_minor=np.append(u_minor,k*j_minor['stepsize'])
        intensity_minor= np.append(intensity_minor,j_minor['data'][k])
    ax_minor=plt.subplot2grid((2,2),(1,1),fig=fig)
    ax_minor.plot(u_minor,intensity_minor)
    ax_minor.set_title("Minor Axis")
    ax_minor.set_xlabel("um")
    ax_minor.set_ylabel("Intensity (ADU)")
    
    #Save image as HDF5 file
    #TODO: Change this to a path that LaserLink has write access to. This location
    #needs to be on the server PC
    file_path=b"C:\\Users\\rdragone\\AppData\\Local\\DataRay Inc\\asdf.h5"
    #path names need to be Base64 encoded to send over HTTP
    encoded_bytes = base64.urlsafe_b64encode(file_path)
    print((requests.get(url + "/SaveToHDF5/"+device_id+"/"+str(encoded_bytes.decode()))).text)

    plt.show()
    #Stop and disconnect camera
    print((requests.get(url + "/DisconnectCamera/"+device_id)).text)
    
# Using the special variable
# __name__
if __name__=="__main__":
    main()