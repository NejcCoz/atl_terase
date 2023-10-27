import rasterio
import numpy as np
import geopandas as gpd
from pyproj import CRS
import time
from shapely.geometry import box
# import shapely.speedups
# import matplotlib.pyplot as plt


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

    return grid


def get_vrt_extents(path):
    # Read metadata from raster
    with rasterio.open(path, "r") as src:
        # Pixel size
        pix_size = src.profile["transform"].a
        width = src.profile["width"]
        height = src.profile["height"]
        x_min = src.profile["transform"].c
        y_max = src.profile["transform"].f
        x_max = x_min + width * pix_size
        y_min = y_max - height * pix_size
        vrt = {
            "spacing": tile_size * pix_size,
            "extents": [x_min, y_min, x_max, y_max],
            "pixel_size": pix_size
        }
    return vrt


if __name__ == "__main__":
    # INPUTS
    # ------
    # Path to DEM mosaic (vrt)
    vrt_path = "p:\\ESA AiTLAS\\delo\\test_terase\\DEM_D96_05m_virtual_mosaic.vrt"
    # Path to mask (shp)
    terase_pth = "d:\\AiTLAS_terase\\terase_svn_d96.shp"

    tile_size = 512
    crs = CRS.from_epsg(3794)

    # Get raster meta data
    raster_meta = get_vrt_extents(vrt_path)

    # Read polygon that will be used for masking & find extents
    terase = gpd.read_file(terase_pth)
    # TODO: For future cases if needed, change multiple single features to one multipolygon
    # Explode into multiple single features:
    # terase = terase.explode()

    # Define grid extents (minimum area covered by both raster and polygons)
    r_ext = raster_meta["extents"]
    s_ext = list(terase.bounds.iloc[0])
    g_ext = [
        np.floor(max(r_ext[0], s_ext[0])),
        np.floor(max(r_ext[1], s_ext[1])),
        np.ceil(min(r_ext[2], s_ext[2])),
        np.ceil(min(r_ext[3], s_ext[3]))
    ]

    # Create grid from extents
    t1 = time.time()
    tile_width = int(raster_meta["spacing"])
    all_tiles = uniform_grid(g_ext, tile_width, crs.to_epsg())
    # all_tiles.to_file(".\\all_tiles_2048")
    t1 = time.time() - t1
    print(f"Time for grid: {t1}")

    # TESTING SPATIAL INDEX
    print("Querying spatial index...")
    t1 = time.time()
    # Returns array with two vectors, listing the
    my_grid = all_tiles.geometry.sindex.query_bulk(terase.geometry, predicate="intersects")
    t1 = time.time() - t1
    print(f"Time for sindex bulk querry: {t1}")

    # filter the grid to retain only the tiles that contain masked features
    needed_tiles = all_tiles.iloc[list(np.sort(my_grid[1, :]))]
    # If for some reason the sindex query is done with multiple polygons, then find and remove duplicates, this is done
    # using the np.unique() function
    # needed_tiles = all_tiles.iloc[list(np.unique(my_grid[1, :]))]

    # Save to SHAPE file (optional)
    needed_tiles.to_file(".\\needed_tiles")
