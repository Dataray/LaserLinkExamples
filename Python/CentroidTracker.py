# -*- coding: utf-8 -*-
"""
@author: Rocco Dragone
Simple example that connects to first DataRay device found on system, changes
some settings, and then enters an infinite loop where the centroid values are
repeatedly read and plotted. To end the loop, hit Ctrl+C on your keyboard. 

Search for #TODO for sections of code that may need to be changed for your
application
"""
import requests
import json
import matplotlib.pyplot as plt
import numpy as np
import time
import re
# Defining main function
def main():   
    #You may need to set iPython console settings for graphics from inline to automatic
    #for plots to update during loop in separate window

    #TODO: Change this to the appropriate url and port for your network setup.
    #Using localhost in lieu of an IP address will considerable overhead
    url = "http://192.168.7.214:18080"

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
        "i_exposure_time_us": 2000,
        "d_gamma": 1}
    #ChangeSettings will return ERROR if invalid settings are used.
    print((requests.post(url + "/ChangeSettings/"+device_id, json = jsonData)).text)
    print((requests.get(url + "/StartCamera/"+device_id)).text)
    
    x_centroids=np.array([])
    y_centroids=np.array([])
    times=np.array([])
    start_time=time.time()
    fig = plt.figure()
    ax=fig.add_subplot(111)
    line1,=ax.plot(times,x_centroids,marker="x",label="Xc")
    line2,=ax.plot(times,y_centroids,marker="+",label="Yc")
    good_title="Centroid over time for "+deviceName
    ax.set_title(good_title)
    ax.set_xlim(0,20)
    ax.set_ylim(-1000,1000)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Centroid (um)")
    ax.legend()
    ax.grid()

    min_centroid=11000
    max_centroid=-11000
    x=0;

    #infinite loop until Ctrl+C
    while(True):
        try:
            result_str=requests.get(url + "/GetResults/"+device_id).text
            if result_str =="Invalid image.":
                ax.set_title("Invalid image detected. Pausing data collection.")
                fig.canvas.draw()
                fig.canvas.flush_events()
                plt.show()
                continue
            else:
                ax.set_title(good_title)
            result_dict=json.loads(result_str)
            cur_x_centroid=result_dict["d_CentroidX_um"]
            cur_y_centroid=result_dict["d_CentroidY_um"]
            if(x>50):
                x_centroids=np.delete(x_centroids,0)
                y_centroids=np.delete(y_centroids,0)
                times=np.delete(times,0)
            x_centroids=np.append(x_centroids,cur_x_centroid)
            y_centroids=np.append(y_centroids,cur_y_centroid)
            cur_max_centroid=max(cur_x_centroid,cur_y_centroid)
            cur_min_centroid=min(cur_x_centroid,cur_y_centroid)
            if(cur_max_centroid>max_centroid):
                max_centroid=cur_max_centroid
                ax.set_ylim(min_centroid-500,max_centroid+500)
            if(cur_min_centroid<min_centroid):
                min_centroid=cur_min_centroid
                ax.set_ylim(min_centroid-500,max_centroid+500)
            cur_time=time.time()-start_time
            times=np.append(times,cur_time)
            ax.set_xlim(min(times),cur_time)
            line1.set_xdata(times)
            line1.set_ydata(x_centroids)
            line2.set_xdata(times)
            line2.set_ydata(y_centroids)
            fig.canvas.draw()
            fig.canvas.flush_events()
            plt.show()
            x=x+1
        except KeyboardInterrupt:
            print((requests.get(url + "/StopCamera/"+device_id)).text)
            print((requests.get(url + "/DisconnectCamera/"+device_id)).text)#Stop and disconnect camera
            break

# Using the special variable
# __name__
if __name__=="__main__":
    main()