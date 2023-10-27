import rasterio
import numpy as np
import geopandas as gpd
from pyproj import CRS
import time
from shapely.geometry import box
import shapely.speedups


# Create mesh
def uniform_grid(extents, spacing=256, epsg=3794):
    print("Creating uniform grid...")

    # total area for the grid [xmin, ymin, xmax, ymax]
    # extents = [378086.9099999999743886, 31798.7700000000004366, 615456.9200000000419095, 193207.6099999999860302]
    x_min, y_min, x_max, y_max = extents  # gdf.total_bounds

    # projection of the grid
    crs = CRS.from_epsg(epsg).to_wkt()

    grid_cells = []
    for x0 in np.arange(x_min, x_max, spacing):
        for y0 in np.arange(y_max, y_min, -spacing):
            # bounds
            x1 = x0 + spacing
            y1 = y0 - spacing
            grid_cells.append(box(x0, y0, x1, y1))

    # save as dataframe
    grid = gpd.GeoDataFrame(grid_cells, columns=['geometry'], crs=crs)
    grid['cell_id'] = range(1, len(grid) + 1)
    #
    return grid


if __name__ == "__main__":
    vrt_path = "p:\\ESA AiTLAS\\delo\\test_terase\\DEM_D96_05m_virtual_mosaic.vrt"

    terase_pth = "d:\\AiTLAS_terase\\terase_svn_d96.shp"

    tile_size = 2048

    # Read metadata from raster
    with rasterio.open(vrt_path, "r") as vrt:
        test_profile = vrt.profile
        width = test_profile["width"]
        height = test_profile["height"]
        pix_size = test_profile["transform"].a
        x_min = test_profile["transform"].c
        y_max = test_profile["transform"].f
        x_max = x_min + width * pix_size
        y_min = y_max - height * pix_size
        spacing = tile_size * pix_size
        raster_extents = [x_min, y_min, x_max, y_max]

    # Read polygon that will be used for masking
    terase = gpd.read_file(terase_pth)

    # Create grid from extents
    t1 = time.time()
    all_tiles = uniform_grid(raster_extents, spacing, 3794)
    t1 = time.time() - t1
    print(t1)
    all_tiles.to_file(".\\all_tiles_2048")

    # Randomise rows
    df = all_tiles[0:60000]
    # df = df.sample(frac=1).reset_index(drop=True)
    #
    # # Test rows until you reach 2000 samples
    # t1 = time.time()
    # no_of_samples = 0
    # list_of_samples = []
    # while no_of_samples < 2000:
    #     if all_tiles["geometry"][no_of_samples].intersects(terase.geometry[0]):
    #         no_of_samples += 1
    #         list_of_samples.append(all_tiles[no_of_samples])
    # t1 = time.time() - t1
    # print(f"Time for random samples: {t1}")

    t1 = time.time()
    shapely.speedups.enable()
    pip_mask = all_tiles["geometry"].intersects(terase.geometry[0])  # .within(terase.loc[0, 'geometry'])
    t1 = time.time() - t1
    shapely.speedups.disable()
    print(f"Time for intersect: {t1}")

    print(pip_mask.value_counts())

    filtered_tiles = all_tiles[pip_mask]
    filtered_tiles.to_file(".\\filtered_tiles_2048")


