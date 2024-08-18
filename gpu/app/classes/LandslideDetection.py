from __init__ import ModelsDetection
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import numpy as np
import cv2
import os

class LandslideDetection(ModelsDetection):
    def __init__(self):
        super().__init__()

    def run_clouds_detection(self, image_path):
        try:
            # Perform cloud detection
            results = self.detection_pipeline('cloud', image_path)
            cloud_polygons = []
            for result in results:
                if result.masks.xy is not None:
                    for mask in result.masks.xy:
                        cloud_polygons.append(self.mask_to_polygon(mask))
            return cloud_polygons
        except Exception as e:
            # print(f"Error in run_clouds_detection: {e}")
            return []

    def run_buildings_detection(self, image_path):
        try:
            # Perform building detection
            results = self.detection_pipeline('infrastructure', image_path)
            building_polygons = []
            for result in results:
                if result.masks.xy is not None:
                    for mask in result.masks.xy:
                        building_polygons.append(self.mask_to_polygon(mask))
            return building_polygons
        except Exception as e:
            # print(f"Error in run_buildings_detection: {e}")
            return []

    def run_landslide_detection(self, image):
        try:
            # Perform landslide detection on the image
            results = self.detection_pipeline(feature='landslide', folder=image, imgsz=640, conf=0.3, iou=0.2, save=False)
            landslide_polygons = []
            for result in results:
                if result.masks.xy is not None:
                    for mask in result.masks.xy:
                        landslide_polygons.append(self.mask_to_polygon(mask))
            return landslide_polygons
        except Exception as e:
            # print(f"Error in run_landslide_detection: {e}")
            return []

    def crop_polygons_from_image(self, image_path, polygons):
        try:
            # Load image
            image = cv2.imread(image_path)
            mask = np.ones(image.shape[:2], dtype=np.uint8) * 255  # Create a white mask
            
            # Create masks for all polygons
            for polygon in polygons:
                polygon = np.array(polygon, dtype=np.int32)
                cv2.fillPoly(mask, [polygon], 0)  # Set polygon area to black

            # Extract the remaining region
            remaining_image = cv2.bitwise_and(image, image, mask=mask)
            return remaining_image
        except Exception as e:
            # print(f"Error in crop_polygons_from_image: {e}")
            return None

    def plot_all(self, image_path, cloud_polygons, building_polygons, landslide_polygons, save_path="landslide_detection.png"):
        try:
            # Plot the original image and overlay the detected features
            image = Image.open(image_path)
            fig, ax = plt.subplots(1, figsize=(12, 12))
            ax.imshow(image)

            for polygon in cloud_polygons:
                cloud_patch = patches.Polygon(polygon, closed=True, linewidth=2, edgecolor='blue', facecolor='blue', alpha=0.4)
                ax.add_patch(cloud_patch)

            for polygon in building_polygons:
                building_patch = patches.Polygon(polygon, closed=True, linewidth=2, edgecolor='green', facecolor='none')
                ax.add_patch(building_patch)

            for polygon in landslide_polygons:
                landslide_patch = patches.Polygon(polygon, closed=True, linewidth=2, edgecolor='red', facecolor='red', alpha=0.4)
                ax.add_patch(landslide_patch)

            plt.axis('off')
            plt.savefig(save_path, bbox_inches='tight', pad_inches=0)
            plt.show()
            
        except Exception as e:
            # print(f"Error in plot_all: {e}")
            pass

    def process_image(self, image_path):
        try:
            # Perform cloud detection
            cloud_polygons = self.run_clouds_detection(image_path)
            
            # Crop out detected clouds from the image
            remaining_after_clouds = self.crop_polygons_from_image(image_path, cloud_polygons)

            if remaining_after_clouds is not None:
                # Save the remaining image to a temporary file
                temp_clouds_file_path = 'temp_remaining_after_clouds.png'
                cv2.imwrite(temp_clouds_file_path, remaining_after_clouds)

                # Perform building detection on the remaining image
                building_polygons = self.run_buildings_detection(temp_clouds_file_path)

                # Crop out detected buildings from the remaining image
                remaining_after_buildings = self.crop_polygons_from_image(temp_clouds_file_path, building_polygons)

                if remaining_after_buildings is not None:
                    # Save the remaining image to a temporary file
                    temp_buildings_file_path = 'temp_remaining_after_buildings.png'
                    cv2.imwrite(temp_buildings_file_path, remaining_after_buildings)

                    # Perform landslide detection on the remaining image
                    landslide_polygons = self.run_landslide_detection(temp_buildings_file_path)

                    # Plot results
                    self.plot_all(image_path, cloud_polygons, building_polygons, landslide_polygons)

                    # Clean up temporary files
                    os.remove(temp_clouds_file_path)
                    os.remove(temp_buildings_file_path)
        except Exception as e:
            # print(f"Error in process_image: {e}")
            pass

    def mask_to_polygon(self, mask):
        # Convert a mask to a polygon
        return mask.tolist()


# Initialize the LandslideDetection class
landslide_detector = LandslideDetection()

# Define the input image path
image_path = r"C:\Users\USER\Desktop\Work\Uniten\Prototype\Backend\sample-flask-main\TestingData\landslide\landslide_1.jpg"

# Run the entire process
landslide_detector.process_image(image_path)
