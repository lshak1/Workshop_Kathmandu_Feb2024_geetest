#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 16:12:12 2024

@author: ttsmith
"""
#%%Importing Modules
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import cartopy
import cartopy.crs as ccrs
import datetime
from shapely.geometry import mapping
import time, os
import rasterio

import ee
ee.Initialize()
print(ee.__version__)

#%% Function Definitions
def create_data(data, variable, location):
    name = 'x'
    def create_time_series(data, variable, name):
        def create_(image):
            date = image.get('system:time_start')
            value = image.reduceRegion(reducer=ee.Reducer.mean(), geometry=location).get(variable)
            ft = ee.Feature(None, {'date': ee.Date(date).format('Y/M/d-H:m:s'), name: value})
            return ft
        return data.map(create_).getInfo()
    
    time_series = create_time_series(data, variable, name)
    
    dates, datas = [], []
    for f in time_series['features']:
        properties = f['properties']
        date = properties['date']
        try:
            val = properties[name]
            datas.append(val)
            dates.append(datetime.datetime.strptime(date,'%Y/%m/%d-%H:%M:%S')) #Convert the date into something that Python recognizes
        except:
            pass
    return np.array(dates), np.array(datas)

def run_export(image, crs, filename, scale, region, maxPixels=1e12, cloud_optimized=True):
    task_config = {'fileNamePrefix': filename,'crs': crs,'scale': scale,'maxPixels': maxPixels, 'fileFormat': 'GeoTIFF', 'formatOptions': {'cloudOptimized': cloud_optimized}, 'region': region,}
    task = ee.batch.Export.image.toDrive(image, filename, **task_config)
    task.start()
    
def mask_(image):
    mask = image.gt(0.5)
    return image.updateMask(mask)


#%% Create the Data
trishuli_outline = gpd.read_file('../GeoData/Trishuli.geojson')
area_of_interest = ee.Geometry.MultiPolygon(ee.List(mapping(trishuli_outline.geometry[0])['coordinates']))

#Open the Google Earth Engine Data
#This data is in mm/hr: https://developers.google.com/earth-engine/datasets/catalog/NASA_GPM_L3_IMERG_V06#bands
hr_rainfall = ee.ImageCollection("NASA/GPM_L3/IMERG_V06").select('precipitationCal').filterDate('2024-01-01', '2024-03-01')
hr_rainfall = hr_rainfall.map(mask_) #Remove low values

#Create the time series
rdates, rain = create_data(hr_rainfall, 'precipitationCal', area_of_interest)

#Create the grid
rain_sum = hr_rainfall.reduce(ee.Reducer.sum())
run_export(rain_sum, 'epsg:4326', 'GPM_JanFeb2024_RainfallSum', scale=11132, region=area_of_interest)

#Load the new data
import time, os
#src = rasterio.open('../GeoData/GPM_Feb2024_RainfallSum.tif')
while not os.path.exists('/home/ttsmith/gdrive/GPM_JanFeb2024_RainfallSum.tif'):
    time.sleep(10)
src = rasterio.open('/home/ttsmith/gdrive/GPM_JanFeb2024_RainfallSum.tif')
grid_data = src.read(1)


#%% Create the Figure
#Make the plot
f = plt.figure(figsize=(25,10))

#First do the map:
ax = f.add_subplot(121, projection=ccrs.PlateCarree()) #Create a geographic axis
ax.add_feature(cartopy.feature.BORDERS, linestyle='--')
trishuli_outline.plot(ax=ax, facecolor='none', edgecolor='blue', linewidth=2)

left, bottom, right, top = src.bounds #Get the geographic boundaries of our grid data
ax.set_extent([left - 0.1, right + 0.1, bottom - 0.1, top + 0.1], crs=ccrs.PlateCarree())

#Add in the colormap
color = ax.imshow(grid_data, extent=(left, right, bottom, top))
cbar = plt.colorbar(color, ax=ax)
cbar.set_label('Jan+Feb 2024 Precipitation Sum (mm)', fontsize=18, fontweight='bold')

#Add in a grid so we can locate ourselves
gl = ax.gridlines(crs=ccrs.PlateCarree(), linewidth=1, color='black', alpha=0.5, linestyle='--', draw_labels=True)
gl.top_labels = False
gl.right_labels = False

ax.set_title('Jan+Feb 2024 Precipitation Sum, Trishuli', fontsize=24, fontweight='bold')

#Then add the chart
ax = f.add_subplot(122)
ax.plot(rdates, rain)
ax.set_ylim(ymin=0) #Set the minimum y-value to 0
ax.set_xlim(rdates[0], rdates[-1]) #Make the plot only go to the first and last date in our data

ax.set_xlabel('Date', fontsize=18, fontweight='bold') #Increase the size of the axis labels
ax.set_ylabel('Daily Precipitation (mm)', fontsize=18, fontweight='bold')

ax.tick_params(axis='both', which='major', labelsize=16) #Make the labels bigger
ax.tick_params(axis='x', which='major', rotation=45) #Rotate the x-labels so they are clearer

ax.plot(rdates[rain != 0], rain[rain != 0], 'rx', markersize=8, label='Rainfall') #Only plot non-zero days
ax.legend() #Add a legend for easy reference

ax.set_title('Trishuli Rainfall, Jan-Feb 2024', fontsize=20, fontweight='bold') #Add a title
ax.grid(True) #Add a grid
f.savefig('Trishuli_Figure.png', dpi=300, bbox_inches='tight')