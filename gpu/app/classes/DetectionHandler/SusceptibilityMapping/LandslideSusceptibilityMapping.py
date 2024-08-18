import geopandas as gpd
from shapely.geometry import Point, Polygon
import numpy as np
import random
import os

def generate_random_shapefiles(output_dir, bounds, num_rivers=5, num_buildings=10, num_landslides=3, num_land_use=4):
    os.makedirs(output_dir, exist_ok=True)
    
    def random_point(bounds):
        minx, miny, maxx, maxy = bounds
        return Point(random.uniform(minx, maxx), random.uniform(miny, maxy))

    def random_polygon(bounds, num_points=5):
        minx, miny, maxx, maxy = bounds
        points = [random_point(bounds) for _ in range(num_points)]
        return Polygon(points)

    # Generate rivers
    rivers = gpd.GeoDataFrame(geometry=[random_polygon(bounds) for _ in range(num_rivers)])
    rivers.to_file(os.path.join(output_dir, 'rivers.shp'))

    # Generate buildings
    buildings = gpd.GeoDataFrame(geometry=[random_polygon(bounds) for _ in range(num_buildings)])
    buildings.to_file(os.path.join(output_dir, 'buildings.shp'))

    # Generate landslides
    landslides = gpd.GeoDataFrame(geometry=[random_polygon(bounds) for _ in range(num_landslides)])
    landslides.to_file(os.path.join(output_dir, 'landslides.shp'))

    # Generate land use
    land_use = gpd.GeoDataFrame(geometry=[random_polygon(bounds) for _ in range(num_land_use)])
    land_use.to_file(os.path.join(output_dir, 'land_use.shp'))

    print(f"Random shapefiles generated in {output_dir}")

# Example usage
# generate_random_shapefiles('test_shapefiles', bounds=(0, 0, 100, 100))

import geopandas as gpd
import rasterio
import numpy as np
from rasterio.features import rasterize
from rasterio.plot import show
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

def create_landslide_susceptibility_map(river_shapefile, buildings_shapefile, landslide_shapefile, land_use_shapefile, weights, output_raster):
    # Load shapefiles
    rivers = gpd.read_file(river_shapefile)
    buildings = gpd.read_file(buildings_shapefile)
    landslides = gpd.read_file(landslide_shapefile)
    land_use = gpd.read_file(land_use_shapefile)
    
    # Calculate the bounding box that includes all the shapefiles
    bounds = rivers.total_bounds
    bounds = np.minimum(bounds, buildings.total_bounds)
    bounds = np.minimum(bounds, landslides.total_bounds)
    bounds = np.minimum(bounds, land_use.total_bounds)
    minx, miny, maxx, maxy = bounds
    
    # Define output raster parameters (e.g., 100x100 resolution)
    out_shape = (100, 100)
    transform = rasterio.transform.from_bounds(minx, miny, maxx, maxy, out_shape[1], out_shape[0])
    profile = {
        'driver': 'GTiff',
        'height': out_shape[0],
        'width': out_shape[1],
        'count': 3,  # 3 bands for RGB
        'dtype': rasterio.uint8,
        'crs': rivers.crs,
        'transform': transform
    }

    # Rasterize shapefiles to match the output raster
    def rasterize_shapefile(gdf, out_shape, transform):
        return rasterize(
            ((geom, 1) for geom in gdf.geometry),
            out_shape=out_shape,
            transform=transform,
            fill=0,
            all_touched=True,
            dtype='uint8'
        )
    
    # Rasterize layers
    river_raster = rasterize_shapefile(rivers, out_shape, transform)
    buildings_raster = rasterize_shapefile(buildings, out_shape, transform)
    landslide_raster = rasterize_shapefile(landslides, out_shape, transform)
    land_use_raster = rasterize_shapefile(land_use, out_shape, transform)
    
    # Apply weights and combine layers to create the susceptibility score
    susceptibility_map = (river_raster * weights['rivers'] +
                          buildings_raster * weights['buildings'] +
                          landslide_raster * weights['landslides'] +
                          land_use_raster * weights['land_use'])
    
    # Normalize susceptibility map to the range 0-1
    susceptibility_map = (susceptibility_map - susceptibility_map.min()) / (susceptibility_map.max() - susceptibility_map.min())
    
    # Apply a colormap to convert the susceptibility map to RGB
    cmap = plt.get_cmap('RdYlGn_r')  # Example colormap (red to green, reversed)
    norm = mcolors.Normalize(vmin=0, vmax=1)
    colored_map = cmap(norm(susceptibility_map))
    
    # Convert the RGBA output to RGB (drop the alpha channel)
    colored_map_rgb = (colored_map[:, :, :3] * 255).astype(np.uint8)

    # Save output raster with RGB bands
    with rasterio.open(output_raster, 'w', **profile) as dst:
        for i in range(3):  # Write R, G, B bands
            dst.write(colored_map_rgb[:, :, i], i + 1)
    
    print(f"Colored landslide susceptibility map saved to {output_raster}")

# Example weights
weights = {
    'rivers': 0.8,
    'buildings': 0.5,
    'landslides': 1.5,
    'land_use': 0.3
}




# Example usage
create_landslide_susceptibility_map(
    river_shapefile='test_shapefiles/rivers.shp',
    buildings_shapefile='test_shapefiles/buildings.shp',
    landslide_shapefile='test_shapefiles/landslides.shp',
    land_use_shapefile='test_shapefiles/land_use.shp',
    weights=weights,
    output_raster='test_shapefiles/output_susceptibility_map.tif'
)
