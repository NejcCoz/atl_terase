import os
import time
import rasterio
from shapely.geometry import box
from pyproj.crs import CRS
import geopandas as gpd
import pandas as pd
from tqdm import tqdm


t2 = time.time()
root_dir = "l:\\Slovenija\\DEM_D96_05m_buffered"

list_paths = []
for root, _, fnames in sorted(os.walk(root_dir)):
    for i, fname in enumerate(sorted(fnames)):
        path = os.path.join(root_dir, fname)
        list_paths.append(path)

t2 = time.time() - t2
print(f"Find paths: {t2:02} sec.")
print(len(list_paths))


def get_extents(tif_path):
    fn = os.path.basename(tif_path)
    # This extracts bottom-left corner
    coords = [int(s) for s in fn.split("_") if s.isdigit()]
    a, b, c, d = coords + [s + 1000 for s in coords]
    polygon = box(a, b, c, d)
    # with rasterio.open(tif_path) as ds:
    #     bb = ds.bounds
    #     polygon = box(bb.left, bb.bottom, bb.right, bb.top)
    return polygon


tdf = pd.DataFrame(list_paths, columns=["File_Paths"])

# tdf = df.iloc[700:708].copy()

tqdm.pandas(desc="Reading tif extents")
tdf["geometry"] = tdf["File_Paths"].progress_apply(lambda g: get_extents(g))

# Convert to GPD
tdf = gpd.GeoDataFrame(tdf)
tdf = tdf.set_crs(CRS.from_epsg(3794))

# Save SHP
print("Saving SHP...")
tdf.to_file("test.shp")

# for path in list_paths[700:702]:
#     t3 = time.time()
#     # Create polygon
#     poly = get_extents(path)
#     crs = CRS.from_epsg(3794)
#     gs = gpd.GeoSeries(poly, crs=crs)
#     t3 = time.time() - t3
#     print(t3)

print("DONE!")
