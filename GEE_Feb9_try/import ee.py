import ee
import geopandas as gpd
import datetime
import numpy as np

# Initialize the Earth Engine module.
ee.Initialize()

# Load the shapefile
shapefile_path = '/Users/lumana/Library/CloudStorage/GoogleDrive-lshakya@ncsu.edu/My Drive/notebooks/ee/Workshop_Kathmandu_Feb2024_geetest/GEE_Feb9_try/bgd_admbnda_adm2_bbs_20201113.shp'
gdf = gpd.read_file(shapefile_path)

# Function to export time-series data for a given geometry and variable
def export_time_series_data(collection, geometry, variable):
    def create_time_series(image):
        date = image.get('system:time_start')
        value = image.reduceRegion(reducer=ee.Reducer.mean(), geometry=geometry).get(variable)
        ft = ee.Feature(None, {'date': ee.Date(date).format('Y/M/d'), variable: value})
        return ft

    time_series = collection.map(create_time_series).getInfo()
    
    dates, values = [], []
    for f in time_series['features']:
        properties = f['properties']
        date = properties['date']
        dates.append(datetime.datetime.strptime(date, '%Y/%m/%d')) # Convert the date into something that Python recognizes
        val = properties[variable]
        values.append(val)
        
    return np.array(dates), np.array(values)

# Define the time range and the dataset
start_date = '1990-01-01'
end_date = '2020-01-31'
dataset = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR").filterDate(start_date, end_date)

# Variables to extract
variables = ['temperature_2m', 'temperature_2m_min', 'temperature_2m_max', 'total_precipitation_sum']

# Iterate over each district and extract the time-series data
district_data = {}
for idx, row in gdf.iterrows():
    district_name = row['district_name']  # Adjust this to match the column name in your shapefile
    geometry = ee.Geometry.Polygon(row['geometry'].exterior.coords)
    
    district_data[district_name] = {}
    for variable in variables:
        dates, values = export_time_series_data(dataset, geometry, variable)
        district_data[district_name][variable] = {'dates': dates, 'values': values}

# Now `district_data` contains the time-series data for each district and each variable