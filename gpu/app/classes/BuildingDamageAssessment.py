
from __init__ import ModelsDetection
import os
import shutil
import subprocess
from osgeo import gdal, ogr, osr
from ultralytics import YOLO
from shapely.geometry import Polygon
import geopandas as gpd
import tempfile
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import numpy as np
import rasterio
from shapely.geometry import box
import uuid



class BuildingDamageAssessment(ModelsDetection):
    def __init__(self):
        super().__init__()
        
    def handle_damage_assessment(self, pre_event, post_event):
        feature_type = "infrastructure"
        results = self.detection_pipeline(feature_type, pre_event, imgsz=640)

        buildings_with_damage = []

        for result in results:
            for mask in result.masks.xy:
                building_polygon = mask.tolist()
                cropped_image = self.crop_polygon_from_image(
                    post_event, building_polygon)
                damage_level = self.apply_damage_assessment(cropped_image)
                damage_assessment = self.damage_level_to_string(damage_level)
                buildings_with_damage.append(
                    {'polygon': building_polygon, 'damage_assessment': damage_assessment})

        # Convert buildings_with_damage to GeoDataFrame and save as shapefile and GeoJSON
        polygons = [Polygon(building['polygon'])
                    for building in buildings_with_damage]
        shapefile_path = self.polygons_to_shapefile(polygons)
        geojson_path = self.polygons_to_geojson(polygons)

        return {
            "shapefile": shapefile_path,
            "geojson": geojson_path,
            "buildings_with_damage": buildings_with_damage, 
        }

    def polygons_to_shapefile(self, polygons, default_crs="EPSG:4326"):
        output_dir = tempfile.mkdtemp()
        crs = default_crs
        polygon_shapes = [Polygon(poly) for poly in polygons]
        gdf = gpd.GeoDataFrame(index=range(
            len(polygon_shapes)), crs=crs, geometry=polygon_shapes)
        shapefile_path = os.path.join(output_dir, "buildings_with_damage.shp")
        gdf.to_file(shapefile_path, driver='ESRI Shapefile')
        zip_file_path = shutil.make_archive(output_dir, 'zip', output_dir)
        return zip_file_path

    def polygons_to_geojson(self, polygons, default_crs="EPSG:4326"):
        output_file_path = tempfile.mktemp(suffix=".geojson")
        crs = default_crs
        polygon_shapes = [Polygon(poly) for poly in polygons]
        gdf = gpd.GeoDataFrame(index=range(
            len(polygon_shapes)), crs=crs, geometry=polygon_shapes)
        gdf.to_file(output_file_path, driver='GeoJSON')
        return output_file_path

    def crop_polygon_from_image(self, image_path, polygon):
        """
        Crop the given polygon area from the image, either TIFF or regular image.
        """
        if image_path.lower().endswith('.tif') or image_path.lower().endswith('.tiff'):
            # Handle TIFF file with GDAL
            return self._crop_polygon_from_tiff(image_path, polygon)
        else:
            # Handle regular image with PIL
            return self._crop_polygon_from_regular_image(image_path, polygon)

    def _crop_polygon_from_tiff(self, image_path, polygon):
        """
        Crop the polygon from a TIFF image using GDAL.
        """
        ds = gdal.Open(image_path)
        if ds is None:
            raise FileNotFoundError(f"Could not open TIFF file {image_path}")

        geo_transform = ds.GetGeoTransform()
        inverse_transform = gdal.InvGeoTransform(geo_transform)
        pixel_polygon = [gdal.ApplyGeoTransform(
            inverse_transform, x, y) for x, y in polygon]

        x_coords, y_coords = zip(*pixel_polygon)
        min_x, max_x = int(min(x_coords)), int(max(x_coords))
        min_y, max_y = int(min(y_coords)), int(max(y_coords))

        cropped_image = ds.ReadAsArray(
            min_x, min_y, max_x - min_x, max_y - min_y)
        ds = None

        return cropped_image

    def _crop_polygon_from_regular_image(self, image_path, polygon):
        """
        Crop the polygon from a regular image using PIL.
        """
        image = Image.open(image_path)
        width, height = image.size

        x_coords, y_coords = zip(*polygon)
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)

        cropped_image = image.crop((min_x, min_y, max_x, max_y))
        cropped_image = np.array(cropped_image)

        return cropped_image

    def apply_damage_assessment(self, cropped_image):
        cropped_image_pil = Image.fromarray(cropped_image)
        results = self.models["damage_assessment"].predict(
            cropped_image_pil, imgsz=128, conf=.5, save=False, augment=True)
        damage_level = int(results[0].probs.top1)
        return damage_level

    def plot_damage_assessment(self, image_path, buildings_with_damage, save_path="damage_assessment_plot.png"):
        """
        Plot the detected buildings with different colors based on the damage level and save the plot.
        """
        # Define the colors for different damage levels
        damage_colors = {
            "destroyed": 'red',        # No damage
            "major-damage": 'orange',  # Minor damage
            "minor-damage": 'yellow',  # Moderate damage
            "unclassified": 'green'    # Severe damage
        }

        # Open the image
        image = Image.open(image_path)
        fig, ax = plt.subplots(1, figsize=(12, 12))
        ax.imshow(image)

        for building in buildings_with_damage:
            building_polygon, damage_level = building["polygon"], building["damage_assessment"]
            polygon = patches.Polygon(
                building_polygon, closed=True, linewidth=2, 
                edgecolor=damage_colors[damage_level], 
                facecolor=damage_colors[damage_level], 
                alpha=0.4  # Set the alpha for transparency
            )
            ax.add_patch(polygon)

        plt.axis('off')
        plt.savefig(save_path, bbox_inches='tight')  # Save the plot to the specified path
        plt.show()

    def detect_buildings_chunks(self, image_path):
        
        # divide image into tiles
        num = str(uuid.uuid4())
        tile_width = tile_height = 640
        folder_path=num
        self.create_tiles(image_path, num, tile_width, tile_height, folder_path)
        
        
        # apply detection
        results = self.detection_pipeline("infrastructure", folder_path, 640)
        
        
        buildings_polygons = []
        # append detctions to listt
        for result in results:
            
            # check if it works
            try:
                masks = result.masks.xy
            except:
                continue
            
            for poly in masks:
                poly = poly.tolist()

                detected_coordinates = self.pixels_to_coordinates(
                    result.path, poly)
                buildings_polygons.append(detected_coordinates)
                
        shapefile_output = self.polygons_to_shapefile(buildings_polygons)
        shutil.rmtree(folder_path)

        print(shapefile_output)






# Example usage:
model_detection = BuildingDamageAssessment()
image_path = r"C:\Users\USER\Desktop\Work\Uniten\Prototype\Backend\sample-flask-main\TestingData\buildings_huge_1_1.tif"
model_detection.detect_buildings_chunks(image_path)
# output_shapefile = r"C:\Users\USER\Desktop\Work\drangue\Drangue-Server\gpu\app\classes\DetectionHandler\SusceptibilityMapping\test_shapefiles\buildings.shp"

# detected_buildings_shapefile = model_detection.detect_buildings(image_path, output_shapefile)
# print(f"Buildings detected and saved to {detected_buildings_shapefile}")


# post_event = r"C:\Users\USER\Downloads\damage_test\socal-fire_00000817_post_disaster.png"
# damage_results = model_detection.handle_damage_assessment(
#     pre_event=pre_event, post_event=post_event)

# model_detection.plot_damage_assessment(post_event, damage_results["buildings_with_damage"])
