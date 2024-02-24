import tkinter as tk
from tkinter import filedialog
import geopandas as geo
import pandas as pd
import folium
from folium.plugins import Draw, Geocoder
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.wkt import dumps, loads
import webbrowser
import datetime
import pyperclip
import os
import fiona
from fiona.drvsupport import supported_drivers
fiona.drvsupport.supported_drivers['KML'] = 'rw' #this one works, a lot of others did not

current_time_str = None

def draw_polygon():
    
    global current_time_str 

    current_time = datetime.datetime.now()
    current_time_str = current_time.strftime('%Y%m%d%H%M%S')
    print(current_time_str)

    # Create a map centered at a specific location (e.g., Middleburg, Maryland)
    m = folium.Map(location=[39.0626, -77.7420],
                   tiles = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', 
                   attr = 'Google Maps',
                   zoom_start=3,
                   max_zoom=22)

    # Add the draw control to the map
    draw = Draw(export=True,
                filename=f'{current_time_str}' + '.geojson')  # Enables exporting drawn shapes to GeoJSON
    
    geocoder = Geocoder(collapsed=False,
                    position='topright',
                    provider='Nominatim')

    
    geocoder.add_to(m)
    draw.add_to(m)

    # Save the map to an HTML file
    m.save("draw_map.html")

    # Open the map in the default web browser
    webbrowser.open("draw_map.html")


def retrieve_wkt():
    # Get the filename based on the datetime prefix (you can modify this part as needed)

    user_home = os.path.expanduser("~")
    downloads_folder = os.path.join(user_home, "Downloads/")

    filename = f'{current_time_str}.geojson'
    basepath = downloads_folder
    print(basepath)
    timestamp = current_time_str

    # Read the GeoJSON file
    try:
        features = geo.read_file(f'{basepath}' + f'{timestamp}' + '.geojson')
        features = features.to_crs('4326')

        # Combine the geometries
        combined_geometry = features.geometry.unary_union
        combined_geometry = features.geometry.unary_union.buffer(0)

        if not isinstance(combined_geometry, Polygon):
            if combined_geometry.geom_type == 'MultiPolygon':
                combined_multi_polygon = combined_geometry
            else:
                combined_multi_polygon = MultiPolygon([combined_geometry])
        else:
            combined_multi_polygon = MultiPolygon([combined_geometry])

        # Convert to WKT string
        wkt_string = dumps(combined_multi_polygon)

        # Display the WKT string (you can modify this part as needed)
        print("Retrieved WKT string:")
        print(wkt_string)

        result_label.config(text="Retrieved WKT string:\n" + wkt_string)
        copy_button.pack()
        pyperclip.copy(wkt_string)

    except FileNotFoundError:
        print(f"File '{filename}' not found. Please export the GeoJSON file first.")


def upload_file():


    filetypes = [
        ("GeoJSON files", "*.geojson"),
        ("KML files", "*.kml"),
        ("CSV files", "*.csv"),
        ("All File Types", "*")
    ]

    path = filedialog.askopenfilename(filetypes=filetypes)

    file_extension = path.split('.')[-1]
    if file_extension == 'csv':
        df = pd.read_csv(path)
        print(df)

        if 'geometry' in df:
            df['geometry'] = df['geometry'].apply(lambda x: loads(x) if pd.notnull(x) else None)
            gdf = geo.GeoDataFrame(df, geometry='geometry')
        else:
            gdf = geo.GeoDataFrame(df, geometry=geo.points_from_xy(df.longitude, df.latitude))

    elif file_extension == 'geojson':
        gdf = geo.read_file(path)

    elif file_extension.upper() == 'KML':
        gdf = geo.read_file(path, driver='KML')
        #print(gdf)

    combined_geometry = gdf.geometry.unary_union
    combined_geometry = gdf.geometry.unary_union.buffer(0)

    if not isinstance(combined_geometry, Polygon):
        if combined_geometry.geom_type == 'MultiPolygon':
            combined_multi_polygon = combined_geometry
        else:
            combined_multi_polygon = MultiPolygon([combined_geometry])
    else:
        combined_multi_polygon = MultiPolygon([combined_geometry])

    wkt_string = dumps(combined_multi_polygon)

    # Write the WKT string to a text file
    # with open('combined_geometry.wkt', 'w') as file:
    #     file.write(wkt_string)

    print(wkt_string)

    result_label.config(text="Retrieved WKT string:\n" + wkt_string)

    # Show the "Copy WKT" button
    copy_button.pack()

def copy_wkt_to_clipboard():
    wkt_string = result_label.cget("text").split("\n")[1]
    pyperclip.copy(wkt_string)

root = tk.Tk()
root.title("Geometry Converter")

draw_button = tk.Button(root, text="Draw Polygon", command=draw_polygon)
draw_button.pack()

upload_button = tk.Button(root, text="Upload Geospatial File", command=upload_file)
upload_button.pack()

retrieve_button = tk.Button(root, text="Retrieve WKT from Drawn Polygon", command=retrieve_wkt)
retrieve_button.pack()

# Initially hide the "Retrieve WKT" button
#retrieve_button.pack_forget()

copy_button = tk.Button(root, text="Copy WKT to Clipboard", command=copy_wkt_to_clipboard)
copy_button.pack_forget()

result_label = tk.Label(root, text="", wraplength=600)
result_label.pack()

root.mainloop()

