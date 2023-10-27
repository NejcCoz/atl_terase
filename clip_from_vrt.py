import rasterio
from rasterio.windows import Window
# from rasterio.plot import show
# import matplotlib.pyplot as plt
from rvt.vis import mstp
from rvt.blend import e3mstp
import numpy as np
import geopandas as gpd
from pyproj import CRS
import time
from shapely.geometry import box
import shapely.speedups


# Create mesh
def uniform_grid(extents, spacing=256, epsg=3794):

    # t1 = time.time()
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

    # t1 = time.time() - t1
    # print(t1)

    return grid

vrt_path = "p:\\ESA AiTLAS\\delo\\test_terase\\DEM_D96_05m_virtual_mosaic.vrt"
# out_path = ".\\test.tif"

terase_pth = "d:\\AiTLAS_terase\\terase_svn_d96.shp"

tile_size = 512
visualization = "e3mstp"  # "e3mstp" or "mstp"

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

tile_size = 512

# TODO: Choose extents for the grid from the combination of SHP and Raster extents and "allign to grid"

t1 = time.time()
all_tiles = uniform_grid(raster_extents, spacing, 3794)
t1 = time.time() - t1
print(t1)

# TODO: Read polygons for masking and filter grid to contain only the overlaping cells

terase = gpd.read_file(terase_pth)
# if all_tiles.crs.to_epsg() == terase.crs.to_epsg():
#     pass
# else:
#     pass  ### TODO: reproject!

t1 = time.time()

# intersection = all_tiles.intersects(terase)
# ## todo do list comprehension
# t1 = time.time() - t1

# Randomise rows
df = all_tiles[0:60000]
df = df.sample(frac=1).reset_index(drop=True)

# Test rows until you reach 2000 samples
t1 = time.time()
no_of_samples = 0
list_of_samples = []
while no_of_samples < 2000:
    if all_tiles["geometry"][no_of_samples].intersects(terase.geometry[0]):
        no_of_samples += 1
        list_of_samples.append(all_tiles[no_of_samples])
t1 = time.time() - t1
print(f"Time for random samples: {t1}")

t1 = time.time()
shapely.speedups.enable()
pip_mask = all_tiles["geometry"][0:60000].intersects(terase.geometry[0])  # .within(terase.loc[0, 'geometry'])
t1 = time.time() - t1
shapely.speedups.disable()
print(f"Time for intersect: {t1}")

print(pip_mask.value_counts())

# TODO: Preform a random selection of N cells

# # Set extents for Window read --- TODO: buffer optional
# col_off = 125000
# row_off = 125000
# width = tile_size
# height = tile_size
#
# buff = 250
#
# # Read Window
# tile = Window(col_off, row_off, width, height)
# buffered = Window(col_off - buff, row_off - buff, width + 2 * buff, height + 2 * buff)
#
# with rasterio.open(vrt_path, "r") as vrt:
#     print(vrt.width)
#     print(vrt.height)
#     w = vrt.read(1, window=buffered)
#     tile_trans = vrt.window_transform(tile)
#     buff_trans = vrt.window_transform(buffered)
#     profile = vrt.profile.copy()
#     no_data = vrt.nodata
#
# # print(w.shape)
# # print(buff_trans)
# # print(profile)
#
# # Replace source nan values with np.nan
# if np.count_nonzero(w == no_data) > 0:
#     w[w == no_data] = np.nan
#
# # Apply RVT visualization
# if visualization == "mstp":
#     w_out = mstp(w, local_scale=(1, 10, 1), meso_scale=(10, 50, 5), broad_scale=(50, 500, 50),
#                  no_data=np.nan, fill_no_data=True)
#     w_out = w_out.astype("uint8")
# elif visualization == "e3mstp":
#     w_out = e3mstp(w, pix_size)
#     w_out = np.round(w_out * 255)
#     w_out = w_out.astype("uint8")
#
# # # Plot (DEBUGGING)
# # fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(21, 7))
# # show(w, ax=ax1, transform=buff_trans, cmap='Greys_r', vmin=np.nanmin(w), vmax=np.nanmax(w))
# # show(mstp_out, ax=ax2, transform=buff_trans)
# # # show(svf["svf"], ax=ax2, transform=win_transform, cmap='Greys_r', vmin=0, vmax=1)
# # plt.show()
#
# # Clip to tile
# size = w_out.shape[1]
# w_out = w_out[:, buff:size - buff, buff:size - buff]
#
# # To save as GeoTIFF change driver, width, height and transform
# out_path = ".\\test_buffer_502.tif"
# profile.update(
#     driver="GTiff",
#     compress="lzw",
#     count=w_out.shape[0],
#     width=w_out.shape[1],
#     height=w_out.shape[2],
#     dtype=w_out.dtype,
#     transform=tile_trans,
#     tiled=False,
#     blockxsize=None,
#     blockysize=None,
#     nodata=None
# )
# with rasterio.open(out_path, "w", **profile) as dst:
#     dst.write(w_out)
# #
# # profile.update(
# #     driver="GTiff",
# #     compress="lzw",
# #     count=1,
# #     width=w.shape[0],
# #     height=w.shape[1],
# #     dtype="float32",
# #     transform=tile_trans,
# #     tiled=False,
# #     blockxsize=None,
# #     blockysize=None,
# #     nodata=np.nan
# # )
# # with rasterio.open(".\\orig.tif", "w", **profile) as dst:
# #     dst.write(np.expand_dims(w, axis=0))
#
# print("DONE")
#
# # TODO: Create validity mask for that tile
