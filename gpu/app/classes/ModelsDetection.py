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
            'landslide': r"app\AI\landslide.pt",
            'infrastructure': r"app\AI\infrastructure.pt",
            'landslidemodel3': r"app\AI\tree.pt",
            'landslidemodel4': r"app\AI\landuse2.pt",
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

    def centroid(self, polys):
        """
        Calculate the centroid of a single polygon or a list of polygons.

        :param polygons: A polygon (list of tuples representing vertices) or a list of polygons
        :return: Tuple representing the centroid (cx, cy)
        """
        # Handle the case where the input is a single polygon
        if isinstance(polys[0], tuple):
            polys = [polys]

        total_x = 0
        total_y = 0
        total_points = 0

        for poly in polys:
            num_vertices = len(poly)
            if num_vertices == 0:
                raise ValueError("Polygon must have at least one vertex")

            total_x += sum(vertex[0] for vertex in poly)
            total_y += sum(vertex[1] for vertex in poly)
            total_points += num_vertices

        return (total_x / total_points, total_y / total_points)

    def reproject_coordiantes(self, coordiantes, inEPSG=3857, outEPSG=4326):
        InSR = osr.SpatialReference()
        InSR.ImportFromEPSG(inEPSG)       # WGS84/Geographic
        OutSR = osr.SpatialReference()
        OutSR.ImportFromEPSG(outEPSG)     # WGS84 UTM Zone 56 South

        Point = ogr.Geometry(ogr.wkbPoint)
        # use your coordinates here
        Point.AddPoint(coordiantes[0], coordiantes[1])
        # tell the point what coordinates it's in
        Point.AssignSpatialReference(InSR)
        Point.TransformTo(OutSR)
        # project it to the out spatial reference
        return (Point.GetX(), Point.GetY())

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
                tile_bbox = (lower_left_lon, lower_left_lat,
                             upper_right_lon, upper_right_lat)
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
                gdal.Translate(output_filename, ds, format='GTiff',
                               projWin=[ulx, uly, lrx, lry])
                print(f"Created {output_filename}")

    def polygons_to_shapefile(self, polygons, default_crs="EPSG:4326"):
        output_dir = tempfile.mkdtemp()
        print(output_dir)

        crs = default_crs  # Get the coordinate reference system from the TIFF

        # Create a list of Polygon objects from the list of coordinates
        polygon_shapes = [Polygon(poly) for poly in polygons]

        # Create a GeoDataFrame
        gdf = gpd.GeoDataFrame(index=range(
            len(polygon_shapes)), crs=crs, geometry=polygon_shapes)

        # Save to a shapefile
        gdf.to_file(output_dir, driver='ESRI Shapefile')

        # Zip the folder
        zip_file_path = shutil.make_archive(output_dir, 'zip', output_dir)

        return zip_file_path

    def polygons_to_geojson(self, polygons, default_crs="EPSG:4326"):
        # Create a unique temporary file name
        output_file_path = tempfile.mktemp(suffix=".geojson")

        crs = default_crs  # Get the coordinate reference system from the TIFF

        # Create a list of Polygon objects from the list of coordinates
        polygon_shapes = [Polygon(poly) for poly in polygons]

        # Create a GeoDataFrame
        gdf = gpd.GeoDataFrame(index=range(
            len(polygon_shapes)), crs=crs, geometry=polygon_shapes)

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
        print(bbox)

        tiles = self.divide_bbox_into_tiles(bbox, rows=1, cols=1)
        tiles = [bbox]
        for tile in enumerate(tiles):
            out_file_name = f"detection/{tile[0]}_{output_file}"
            lower_left_lon, lower_left_lat, upper_right_lon, upper_right_lat = tile[1]
            params = ["-f ", "-t "]
            if lower_left_lat < 0 or upper_right_lat < 0:
                params = ["--from=", "--to="]
            command = [
                "python", r"app\services\tms2geotiff.py",
                "-s", "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                f"{params[0]}{lower_left_lat},{lower_left_lon}",
                f"{params[1]}{upper_right_lat},{upper_right_lon}",
                "-z", str(zoom_level),
                out_file_name
            ]

            # Run the command
            try:
                subprocess.run(command, check=True)
                # Example: tile size 1024x1024 pixels
                self.create_tiles(out_file_name, tile[0], 2000, 2000)
                # delete file
                os.remove(out_file_name)

                print(f"GeoTIFF generated successfully: {output_file}")
            except subprocess.CalledProcessError as e:
                print(f"An error occurred while generating GeoTIFF: {e}")

    def pixels_to_coordinates(self, tif_file_path, pixel_coords):
        # Open the TIFF file
        print(tif_file_path)
        ds = gdal.Open(tif_file_path)
        if ds is None:
            print("Error: Could not open the TIFF file.")
            return None

        # Get the geotransformation
        geo_transform = ds.GetGeoTransform()

        # Define the transformation function
        def transform(x_pixel, y_pixel):
            # Apply transformation using float precision
            x = geo_transform[0] + (x_pixel + 0.5) * \
                geo_transform[1] + (y_pixel + 0.5) * geo_transform[2]
            y = geo_transform[3] + (x_pixel + 0.5) * \
                geo_transform[4] + (y_pixel + 0.5) * geo_transform[5]
            return x, y

        # Convert pixel coordinates to geographic coordinates
        geo_coords = [transform(x_pixel, y_pixel)
                      for x_pixel, y_pixel in pixel_coords]

        # Close the TIFF file
        ds = None

        return geo_coords

    def xywh_to_polygon(self, xywh):
        x, y, w, h = xywh
        return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]

    def detection_post_process(self, feature, results):
        detected_polys_files = []
        detected_polys = []
        for result in results:
            try:
                if feature in ["landslide", "infrastructure"]:
                    masks = result.masks.xy
                else:
                    masks = result.boxes.xywh

                box = result.boxes[0]
                class_id = int(box.cls)
                object_name = self.models[feature].names[class_id]
            except:
                continue

            for poly in masks:
                # poly_list = poly.tolist()
                # print(poly_list)
                if feature in ["landslide", "infrastructure"]:
                    poly = poly.tolist()
                else:
                    poly = self.xywh_to_polygon(poly.tolist())

                print(result.path)

                detected_coordinates = self.pixels_to_coordinates(
                    result.path, poly)
                # print(detected_coordinates)

                detected_coordinates_class = {
                    "polygons": detected_coordinates,
                    "class_name": object_name
                }

                detected_polys.append(detected_coordinates_class)
                detected_polys_files.append(detected_coordinates)

            if len(detected_polys) == 0:
                continue
        shapefile_output = self.polygons_to_shapefile(detected_polys_files)
        geojson_output = self.polygons_to_geojson(detected_polys_files)

        print(f"length of polys for {feature}: ", len(detected_polys))
        num_instances = len(detected_polys)
        output = {
            "polygons": detected_polys,
            "shapefile": shapefile_output,
            "geojson": geojson_output,
            "num_instances": num_instances
        }
        return output

    def detection_pipeline(self, feature, folder, imgsz=1280, conf=0.1, iou=0.2, save=False):
        results = self.models[feature].predict(
            folder, imgsz=imgsz, conf=conf, iou=iou, save=save)
        return results

    def detect_polygons(self, polygons, zoom, output_file, area_km2, features_selected):
        returned_output = {}
        self.create_geotiff_with_area(
            polygons=polygons, zoom_level=18, output_file=output_file, area_km2=area_km2)
        for feature in features_selected:
            folder_path = "detection"
            results = self.detection_pipeline(feature, folder_path)
            returned_output[feature] = self.detection_post_process(
                feature, results)
        shutil.rmtree('detection')

        return returned_output

    def detect_single_feature(self, feature_type, file_path):
        results = self.detection_pipeline(feature_type, file_path)
        output = self.detection_post_process(feature_type, results)
        return output