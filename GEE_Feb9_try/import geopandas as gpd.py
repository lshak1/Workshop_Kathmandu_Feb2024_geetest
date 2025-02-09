%pip install geopandas
import geopandas as gpd

# Load the shapefile
shapefile_path = 'bgd_admbnda_adm2_bbs_20201113.shp'
gdf = gpd.read_file(shapefile_path)

# Convert the GeoDataFrame to GeoJSON
geojson = gdf.to_json()

# Save the GeoJSON to a file
geojson_path = 'path_to_your_geojson_file.json'
with open(geojson_path, 'w') as f:
    f.write(geojson)

print(f"GeoJSON file saved to {geojson_path}")