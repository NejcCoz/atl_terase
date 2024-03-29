"""
UNFINISHED, JUST AN IDEA


Creates small tiles for AITLAS input dataset. Read existing tiffs as VRT and
then use window read for each polygon. Polygon grid was crated in qgis.
"""

from osgeo import gdal
import os
from pyproj.crs import CRS
import glob


def get_extent(dataset):

    cols = dataset.RasterXSize
    rows = dataset.RasterYSize
    transform = dataset.GetGeoTransform()
    minx = transform[0]
    maxx = transform[0] + cols * transform[1] + rows * transform[2]

    miny = transform[3] + cols * transform[4] + rows * transform[5]
    maxy = transform[3]

    return {
            "minX": str(minx), "maxX": str(maxx),
            "minY": str(miny), "maxY": str(maxy),
            "cols": str(cols), "rows": str(rows)
            }


def create_tiles(minx, miny, maxx, maxy, n):
    width = maxx - minx
    height = maxy - miny

    matrix = []

    for j in range(n, 0, -1):
        for i in range(0, n):

            ulx = minx + (width/n) * i  # 10/5 * 1
            uly = miny + (height/n) * j  # 10/5 * 1

            lrx = minx + (width/n) * (i + 1)
            lry = miny + (height/n) * (j - 1)
            matrix.append([[ulx, uly], [lrx, lry]])

    return matrix


def split(file_name, n):
    raw_file_name = os.path.splitext(os.path.basename(file_name))[0].replace("_downsample", "")
    driver = gdal.GetDriverByName('GTiff')
    dataset = gdal.Open(file_name)
    band = dataset.GetRasterBand(1)
    transform = dataset.GetGeoTransform()

    extent = get_extent(dataset)

    cols = int(extent["cols"])
    rows = int(extent["rows"])

    print(f"Columns: {cols}")
    print(f"Rows: {rows}")

    minx = float(extent["minX"])
    maxx = float(extent["maxX"])
    miny = float(extent["minY"])
    maxy = float(extent["maxY"])

    width = maxx - minx
    height = maxy - miny

    output_path = os.path.join("data", raw_file_name)
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # print("GCD", gcd(round(width, 0), round(height, 0))
    # print("Width", width
    # print("height", height

    tiles = create_tiles(minx, miny, maxx, maxy, n)
    transform = dataset.GetGeoTransform()
    x_origin = transform[0]
    y_origin = transform[3]
    pixel_width = transform[1]
    pixel_height = -transform[5]

    print(f"{x_origin}, {y_origin}")

    tile_num = 0
    for tile in tiles:

        minx = tile[0][0]
        maxx = tile[1][0]
        miny = tile[1][1]
        maxy = tile[0][1]

        p1 = (minx, maxy)
        p2 = (maxx, miny)

        i1 = int((p1[0] - x_origin) / pixel_width)
        j1 = int((y_origin - p1[1]) / pixel_height)
        i2 = int((p2[0] - x_origin) / pixel_width)
        j2 = int((y_origin - p2[1]) / pixel_height)

        print(f"{i1}, {j1}")
        print(f"{i2}, {j2}")

        new_cols = i2-i1
        new_rows = j2-j1

        data = band.ReadAsArray(i1, j1, new_cols, new_rows)

        # print data

        new_x = x_origin + i1*pixel_width
        new_y = y_origin - j1*pixel_height

        print(f"{new_x}, {new_y}")

        new_transform = (new_x, transform[1], transform[2], new_y, transform[4], transform[5])

        output_file_base = raw_file_name + "_" + str(tile_num) + ".tif"
        output_file = os.path.join("data", raw_file_name, output_file_base)

        dst_ds = driver.Create(output_file,
                               new_cols,
                               new_rows,
                               1,
                               gdal.GDT_Float32)

        # writing output raster
        dst_ds.GetRasterBand(1).WriteArray(data)

        tif_metadata = {
            "minX": str(minx), "maxX": str(maxx),
            "minY": str(miny), "maxY": str(maxy)
        }
        dst_ds.SetMetadata(tif_metadata)

        # setting extension of output raster
        # top left x, w-e pixel resolution, rotation, top left y, rotation, n-s pixel resolution
        dst_ds.SetGeoTransform(new_transform)

        wkt = dataset.GetProjection()

        # setting spatial reference of output raster

        # Assign CRS from pyproj
        slo_crs = CRS.from_epsg(3794)
        dst_ds.SetProjection(slo_crs)

        # srs = osr.SpatialReference()
        # srs.ImportFromWkt(wkt)
        # dst_ds.SetProjection(srs.ExportToWkt())

        # Close output raster dataset
        dst_ds = None

        tile_num += 1

    dataset = None


# List all DEM tifs
list_tifs = glob.glob("l:\\Slovenija\\DEM_D96_05m_buffered\\*.tif")

# Create VRT
slo_crs = CRS.from_epsg(3794)
vrt_options = gdal.BuildVRTOptions(outputSRS=slo_crs)
my_vrt = gdal.BuildVRT('my.vrt', ['one.tif', 'two.tif'], options=vrt_options)
my_vrt = None