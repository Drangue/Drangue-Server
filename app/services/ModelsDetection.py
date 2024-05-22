import os
import shutil
import subprocess
from osgeo import gdal, ogr, osr
from ultralytics import YOLO
from shapely.geometry import Polygon
import geopandas as gpd
import tempfile

class ModelsDetection:
    def __init__(self):
        self.model_paths = {
            'landslidemodel': r"C:\Users\USER\Desktop\Work\drangue\Drangue-Server\app\services\best.pt",
            # Add more models as needed
        }
        self.models = {}
        for model_name, model_path in self.model_paths.items():
            self.models[model_name] = YOLO(model_path)
                       
    def calculate_bounding_box(self, polygons):
        # Initialize min and max coordinates to None
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        # Iterate over each polygon
        for polygon in polygons:
            # Iterate over each point in the polygon
            for point in polygon:
                x, y = point
                # Update min and max coordinates
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
        
        # Construct the bounding box as a tuple (min_x, min_y, max_x, max_y)
        bbox = (min_x, min_y, max_x, max_y)
        
        return bbox
    
    def reproject_coordiantes(self, coordiantes, inEPSG=3857, outEPSG=4326):
        InSR = osr.SpatialReference()
        InSR.ImportFromEPSG(inEPSG)       # WGS84/Geographic
        OutSR = osr.SpatialReference()
        OutSR.ImportFromEPSG(outEPSG)     # WGS84 UTM Zone 56 South

        Point = ogr.Geometry(ogr.wkbPoint)
        Point.AddPoint(coordiantes[0], coordiantes[1]) # use your coordinates here
        Point.AssignSpatialReference(InSR)    # tell the point what coordinates it's in
        Point.TransformTo(OutSR)     
        return (Point.GetX(),Point.GetY()) # project it to the out spatial reference
    def divide_bbox_into_tiles(self, bbox, rows, cols):
        min_lon, min_lat, max_lon, max_lat = bbox
        lon_step = (max_lon - min_lon) / cols
        lat_step = (max_lat - min_lat) / rows

        tiles = []
        for row in range(rows):
            for col in range(cols):
                lower_left_lon = min_lon + col * lon_step
                lower_left_lat = min_lat + row * lat_step
                upper_right_lon = lower_left_lon + lon_step
                upper_right_lat = lower_left_lat + lat_step
                tile_bbox = (lower_left_lon, lower_left_lat, upper_right_lon, upper_right_lat)
                tiles.append(tile_bbox)
        
        return tiles
    
    def create_tiles(self, input_file, num, tile_width, tile_height):
        ds = gdal.Open(input_file)
        band = ds.GetRasterBand(1)
        xsize = band.XSize
        ysize = band.YSize
        
        for i in range(0, xsize, tile_width):
            for j in range(0, ysize, tile_height):
                ulx = ds.GetGeoTransform()[0] + i * ds.GetGeoTransform()[1]
                uly = ds.GetGeoTransform()[3] + j * ds.GetGeoTransform()[5]
                lrx = ulx + tile_width * ds.GetGeoTransform()[1]
                lry = uly + tile_height * ds.GetGeoTransform()[5]
                output_filename = f"detection/tile_{i}_{j}_{num}.tif"
                gdal.Translate(output_filename, ds, format='GTiff', projWin=[ulx, uly, lrx, lry])
                print(f"Created {output_filename}")
    def polygons_to_shapefile(self, polygons, default_crs="EPSG:4326"):
        output_file = tempfile.mkdtemp()
        print(output_file)

        crs = default_crs # Get the coordinate reference system from the TIFF
        
        # Create a list of Polygon objects from the list of coordinates
        polygon_shapes = [Polygon(poly) for poly in polygons]
        
        # Create a GeoDataFrame
        gdf = gpd.GeoDataFrame(index=range(len(polygon_shapes)), crs=crs, geometry=polygon_shapes)
        
        # Save to a shapefile
        gdf.to_file(output_file, driver='ESRI Shapefile')
        extensions = ["shp", "cpg", "dbf", "prj", "shx"]
        
        base_name= os.path.basename(output_file)
        output_files = [f"{output_file}\{base_name}.{ext}" for ext in extensions]
        return output_files
    def polygons_to_geojson(self, polygons, default_crs="EPSG:4326"):
        # Create a unique temporary file name
        output_file_path = tempfile.mktemp(suffix=".geojson")

        crs = default_crs  # Get the coordinate reference system from the TIFF

        # Create a list of Polygon objects from the list of coordinates
        polygon_shapes = [Polygon(poly) for poly in polygons]

        # Create a GeoDataFrame
        gdf = gpd.GeoDataFrame(index=range(len(polygon_shapes)), crs=crs, geometry=polygon_shapes)

        # Save to a GeoJSON file
        gdf.to_file(output_file_path, driver='GeoJSON')

        return output_file_path
    def create_geotiff_with_area(self, polygons, zoom_level, output_file="temp.tiff", area_km2=4):
        if os.path.exists('detection'):
            shutil.rmtree('detection')
        os.makedirs('detection', exist_ok=True)
        """
        Create a GeoTIFF from a TMS based on center coordinates and area.
        
        :param center_coords: Tuple (latitude, longitude) of the center point.
        :param zoom_level: Integer representing the zoom level.
        :param output_file: String, name of the output file (e.g., 'output.tiff').
        :param area_km2: Area in square kilometers for the bbox around the center point.
        """
        # top_left_coords, bottom_right_coords = calculate_bbox(center_coords, area_km2)
        bbox = self.calculate_bounding_box(polygons)
        tiles = self.divide_bbox_into_tiles(bbox, rows=1, cols=1)
        for tile in enumerate(tiles):
            out_file_name =  f"detection/{tile[0]}_{output_file}"
            lower_left_lon, lower_left_lat, upper_right_lon, upper_right_lat = tile[1]
            params = ["-f ", "-t "]
            if lower_left_lat <0 or upper_right_lat <0:
                params = ["--from=","--to="]
            command = [
                "python", R"C:\Users\USER\Desktop\Work\drangue\Drangue-Server\app\services\tms2geotiff.py",
                "-s", "http://mt0.google.com/vt/lyrs=y&hl=en&&s=Ga&x={x}&y={y}&z={z}",
                f"{params[0]}{lower_left_lat},{lower_left_lon}",
                f"{params[1]}{upper_right_lat},{upper_right_lon}",
                "-z", str(zoom_level),
               out_file_name
            ]

            # Run the command
            try:
                subprocess.run(command, check=True)
                self.create_tiles(out_file_name, tile[0], 640, 640)  # Example: tile size 1024x1024 pixels
                # delete file
                os.remove(out_file_name)

                print(f"GeoTIFF generated successfully: {output_file}")
            except subprocess.CalledProcessError as e:
                print(f"An error occurred while generating GeoTIFF: {e}")
    def pixels_to_coordinates(self, tif_file_path, pixel_coords):
        # Open the TIFF file
        ds = gdal.Open(tif_file_path)
        if ds is None:
            print("Error: Could not open the TIFF file.")
            return None
        
        # Get the geotransformation
        geo_transform = ds.GetGeoTransform()
        
        # Define the transformation function
        def transform(x_pixel, y_pixel):
            # Apply transformation using float precision
            x = geo_transform[0] + (x_pixel + 0.5) * geo_transform[1] + (y_pixel + 0.5) * geo_transform[2]
            y = geo_transform[3] + (x_pixel + 0.5) * geo_transform[4] + (y_pixel + 0.5) * geo_transform[5]
            x, y = self.reproject_coordiantes((x, y))
            return x, y
        
        # Convert pixel coordinates to geographic coordinates
        geo_coords = [transform(x_pixel, y_pixel) for x_pixel, y_pixel in pixel_coords]
        
        # Close the TIFF file
        ds = None
        return geo_coords
    
    def detect_polygons(self, polygons,zoom, output_file, area_km2):
        self.create_geotiff_with_area(polygons=polygons, zoom_level=18, output_file=output_file, area_km2=area_km2)
        results =  self.models["landslidemodel"].predict("detection", imgsz=1280, conf=0.5, iou=0.5,save=False)
        detected_polys = []
        for result in results:

            try:
                masks = result.masks.xy 
            except:
                continue
            
            for poly in masks:
                poly_list = poly.tolist()
                print(poly_list)
                detected_coordinates = self.pixels_to_coordinates(result.path, poly.tolist())
                print(detected_coordinates)

                detected_polys.append(detected_coordinates)
        shutil.rmtree('detection')
        
        
        shapefile_output = self.polygons_to_shapefile(detected_polys)
        geojson_output = self.polygons_to_geojson(detected_polys)
        returned_output = {
            "polygons": detected_polys,
            "shapefile": shapefile_output, 
            "geojson": geojson_output
        }
        return returned_output
           