import subprocess
import rasterio
from pyproj.crs import CRS

# Path to th shapefile that will be rasterized
in_shp = "d:\\AiTLAS_terase\\terase_svn_d96.shp"

# Path to the raster that we are creating this mask for
dem_original = "c:\\Users\\ncoz\\ARRS_susa\\fill_tif_fill\\dem_slo_03_HAND_fill_nan.tif"

# Name of output raster (FULL PATH)
out_rst = "d:\\AiTLAS_terase\\terase_mask.tif"

with rasterio.open(dem_original) as ds:
    dem_bb = ds.bounds

# Assign CRS from pyproj
slo_crs = CRS.from_epsg(3794)

# Rasterize streams to match DEM
subprocess.call(
    " ".join([
        "gdal_rasterize",
        "-burn", "1",
        "-co", "COMPRESS=LZW",
        "-init", "0",
        "-tap",
        "-ot", "Byte",
        "-te", " ".join([str(i) for i in list(dem_bb)]),
        "-tr", "0.5 0.5",
        in_shp,
        out_rst
    ])
)

print("DONE!")
